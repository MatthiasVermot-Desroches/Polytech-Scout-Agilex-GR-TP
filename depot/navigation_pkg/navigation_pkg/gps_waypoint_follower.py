import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import FollowWaypoints
from geometry_msgs.msg import PoseStamped
from robot_localization.srv import FromLL
import math

class GPSWaypointFollower(Node):
    def __init__(self):
        super().__init__('gps_waypoint_follower')

        # Client pour convertir GPS → coordonnées cartésiennes
        self.ll_to_map = self.create_client(FromLL, '/fromLL')

        # Client action Nav2
        self.waypoint_client = ActionClient(
            self, FollowWaypoints, 'follow_waypoints')

        self.get_logger().info('GPSWaypointFollower prêt')

    def lat_lon_to_pose(self, lat, lon, alt=0.0):
        """Convertit latitude/longitude en PoseStamped dans le repère map"""
        while not self.ll_to_map.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Attente service fromLL...')

        from geographic_msgs.msg import GeoPoint
        req = FromLL.Request()
        req.ll_point = GeoPoint()
        req.ll_point.latitude  = lat
        req.ll_point.longitude = lon
        req.ll_point.altitude  = alt

        future = self.ll_to_map.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = future.result().map_point.x
        pose.pose.position.y = future.result().map_point.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0

        return pose

    def follow_gps_waypoints(self, waypoints_gps):
        """
        Envoie une liste de waypoints GPS au robot.
        waypoints_gps : liste de tuples (latitude, longitude)
        Exemple : [(48.8566, 2.3522), (48.8570, 2.3530)]
        """
        self.get_logger().info(f'Conversion de {len(waypoints_gps)} waypoints GPS...')

        poses = []
        for lat, lon in waypoints_gps:
            pose = self.lat_lon_to_pose(lat, lon)
            poses.append(pose)
            self.get_logger().info(f'Waypoint converti : lat={lat} lon={lon} '
                                   f'→ x={pose.pose.position.x:.2f} '
                                   f'y={pose.pose.position.y:.2f}')

        self.get_logger().info('Envoi des waypoints à Nav2...')

        while not self.waypoint_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Attente Nav2...')

        goal = FollowWaypoints.Goal()
        goal.poses = poses

        future = self.waypoint_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Waypoints refusés par Nav2')
            return

        self.get_logger().info('Navigation démarrée !')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        self.get_logger().info('Navigation terminée !')


def main(args=None):
    rclpy.init(args=args)
    node = GPSWaypointFollower()

    # ─── MODIFIE CES COORDONNÉES GPS ───────────────────────────────
    # Mets ici les coordonnées GPS de tes waypoints
    waypoints = [
        (43.61539, 7.07272),   # Waypoint 1
    ]
    # ────────────────────────────────────────────────────────────────

    node.follow_gps_waypoints(waypoints)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()