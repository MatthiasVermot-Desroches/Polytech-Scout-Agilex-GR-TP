#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from scipy.spatial.transform import Rotation


class GPSNavigationEKF(Node):

    def __init__(self):

        super().__init__('gps_navigation_ekf')

        # ==========================================================
        # PARAMÈTRES
        # ==========================================================

        self.target_lat = 43.61550
        self.target_lon = 7.07280

        self.goal_tolerance = 0.2  # m

        self.kp_angular = 0.5 #1.2
        self.linear_speed = 0.5

        # ==========================================================
        # ÉTAT
        # ==========================================================

        self.current_lat = None
        self.current_lon = None

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # ==========================================================
        # SUBSCRIBERS
        # ==========================================================

        self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
            10
        )

        # 🔥 IMPORTANT : EKF GLOBAL (pas filtered)
        self.create_subscription(
            Odometry,
            '/odometry/global',
            # '/odom',
            self.odom_callback,
            10
        )

        # ==========================================================
        # CMD
        # ==========================================================

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("GPS + EKF GLOBAL Navigation started")

    # ==========================================================
    # GPS
    # ==========================================================

    def gps_callback(self, msg):
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    # ==========================================================
    # ODOM EKF GLOBAL
    # ==========================================================

    def odom_callback(self, msg):

        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]

        r = Rotation.from_quat(quat)

        # ⚠️ IMPORTANT : ROS uses yaw from ZYX
        yaw = r.as_euler('zyx')[0]
        # yaw = r.as_euler('xyz')[2]
        self.current_yaw = yaw
        euler_xyz = r.as_euler('xyz', degrees=True)
        euler_zyx = r.as_euler('zyx', degrees=True)

        # self.get_logger().info(
        #     f"xyz={euler_xyz} zyx={euler_zyx}"
        # )

    # ==========================================================
    # DISTANCE GPS
    # ==========================================================

    def compute_distance(self):

        R = 6371000.0

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)
        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) *
             math.sin(dlon/2)**2)

        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # ==========================================================
    # BEARING
    # ==========================================================

    def compute_bearing(self):

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)
        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2)
             - math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

        return math.atan2(y, x)

    # ==========================================================
    # NORMALISATION
    # ==========================================================

    def norm(self, a):
        return math.atan2(math.sin(a), math.cos(a))

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    # ==========================================================
    # LOOP
    # ==========================================================

    def control_loop(self):

        if self.current_lat is None:
            self.get_logger().info("NONE LAT XD")
            return
        self.get_logger().info("CONTROL LOOP")
        dist = self.compute_distance()
        bearing = self.compute_bearing()

        error = self.norm(bearing - self.current_yaw)

        self.get_logger().info(
            f"dist={dist:.2f}m | error={math.degrees(error):.1f}°"
        )

        # self.get_logger().info(
        #     f"Bearing={math.degrees(bearing):.1f} "
        #     f"Yaw={math.degrees(self.current_yaw):.1f}"
        # )       

        self.get_logger().info(
            f"bearing={bearing:.3f} "
            f"yaw={self.current_yaw:.3f} "
            f"error={self.norm(bearing-self.current_yaw):.3f}"
        )

        if dist < self.goal_tolerance:
            self.stop()
            return

        cmd = Twist()

        if abs(error) > 0.25:
            cmd.linear.x = 0.0
            # cmd.angular.z = -self.kp_angular * error
            cmd.angular.z = self.kp_angular * error
            # cmd.angular.z = 0.3
        else:
            cmd.linear.x = self.linear_speed
            # cmd.angular.z = 0.3
            # cmd.angular.z = -0.5 * error
            cmd.angular.z = 0.5 * error

        max_angular_speed = 0.5

        if cmd.angular.z > max_angular_speed:
            cmd.angular.z = max_angular_speed

        if cmd.angular.z < -max_angular_speed:
            cmd.angular.z = -max_angular_speed

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = GPSNavigationEKF()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()