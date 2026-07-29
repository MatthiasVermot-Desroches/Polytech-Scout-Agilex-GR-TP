#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

# from tf_transformations import euler_from_quaternion
from scipy.spatial.transform import Rotation


class GPSNavigationTP(Node):

    def __init__(self):

        super().__init__('gps_navigation_tp')

        # Coordonnée GPS cible
        self.target_lat = 43.6153733
        self.target_lon = 7.072748

        # Distance minimale avant arrêt
        self.goal_tolerance = 0.2  # mètres

        # Gains simples de contrôle
        self.angular_gain = 1.0
        self.linear_speed = 0.4

       
        self.current_lat = None
        self.current_lon = None

        self.current_yaw = 0.0

        self.current_x = 0.0
        self.current_y = 0.0


      
        self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
            10
        )

      
        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

      
        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

       
        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.get_logger().info('GPS Navigation TP Started')
   
    def gps_callback(self, msg):

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

   
    def odom_callback(self, msg):

                self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Orientation quaternion
        q = msg.pose.pose.orientation

        quaternion = [
            q.x,
            q.y,
            q.z,
            q.w
        ]

        # _, _, yaw = euler_from_quaternion(quaternion)

        # self.current_yaw = yaw
        rotation = Rotation.from_quat(quaternion)

        yaw = rotation.as_euler('xyz')[2]

        # self.current_yaw = -yaw
        self.current_yaw = yaw + math.pi

    def compute_distance_to_target(self):

        R = 6371000.0

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)

        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return R * c

    def compute_target_bearing(self):

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)

        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)

        x = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1)
            * math.cos(lat2)
            * math.cos(dlon)
        )

        bearing = math.atan2(y, x)

        return bearing

    def normalize_angle(self, angle):

        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    def stop_robot(self):

        cmd = Twist()

        cmd.linear.x = 0.0
        cmd.angular.z = 0.0

        self.cmd_pub.publish(cmd)

    def control_loop(self):

        # Attente GPS
        if self.current_lat is None:

            self.get_logger().info(
                'Waiting for GPS...'
            )

            return

        distance = self.compute_distance_to_target()

        target_bearing = self.compute_target_bearing()

        angle_error = self.normalize_angle(
            target_bearing - self.current_yaw
        )

        self.get_logger().info(
            f'Distance={distance:.2f} m | '
            f'Heading error={math.degrees(angle_error):.1f} deg'
        )

        self.get_logger().info(
            f"Bearing={math.degrees(target_bearing):.1f} "
            f"Yaw={math.degrees(self.current_yaw):.1f}"
        )

        if distance < self.goal_tolerance:

            self.get_logger().info(
                '================================='
            )

            self.get_logger().info(
                'TARGET REACHED'
            )

            self.get_logger().info(
                '================================='
            )

            self.stop_robot()

            return

        cmd = Twist()

        if abs(angle_error) > 0.3:

            cmd.linear.x = 0.0

            cmd.angular.z = (
                self.angular_gain
                * angle_error
            )

        else:

            cmd.linear.x = self.linear_speed

            cmd.angular.z = (
                0.5
                * angle_error
            )

        self.cmd_pub.publish(cmd)

def main(args=None):

    rclpy.init(args=args)

    node = GPSNavigationTP()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.get_logger().info(
            'Stopping robot...'
        )

        node.stop_robot()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()