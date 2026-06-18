#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from ublox_msgs.msg import NavPVT
# from tf_transformations import euler_from_quaternion
from scipy.spatial.transform import Rotation



class GPSRTKNavigator(Node):

    def __init__(self):

        super().__init__('gps_rtk_navigator')

        # ==========================================================
        # CIBLE
        # ==========================================================

        self.target_lat = 43.6153733
        self.target_lon = 7.072748

        self.goal_tolerance = 0.2

        # ==========================================================
        # RTK STATE
        # ==========================================================

        self.rtk_fix_type = 0  # 0=no fix, 2=GPS, 4=RTK FIX

        # ==========================================================
        # ÉTAT ROBOT
        # ==========================================================

        self.current_lat = None
        self.current_lon = None

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

        # RTK STATUS (très important)
        self.create_subscription(
            NavPVT,
            '/navpvt',
            self.navpvt_callback,
            10
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # ==========================================================
        # CMD_VEL
        # ==========================================================

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # ==========================================================
        # LOOP
        # ==========================================================

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("RTK GPS Navigator started")

    # ==========================================================
    # GPS CALLBACK
    # ==========================================================

    def gps_callback(self, msg):

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    # ==========================================================
    # RTK STATUS CALLBACK
    # ==========================================================

    def navpvt_callback(self, msg):

        # u-blox RTK state
        # 0 = no fix
        # 2 = 2D/3D fix
        # 4 = RTK FIX

        self.rtk_fix_type = msg.fix_type

    # ==========================================================
    # ODOM
    # ==========================================================

    def odom_callback(self, msg):

        q = msg.pose.pose.orientation

        quaternion = [q.x, q.y, q.z, q.w]

        # _, _, yaw = euler_from_quaternion(quaternion)

        # self.current_yaw = yaw
        rotation = Rotation.from_quat(quaternion)

        yaw = rotation.as_euler('xyz')[2]

        # self.current_yaw = -yaw
        self.current_yaw = yaw + math.pi

    # ==========================================================
    # DISTANCE GPS
    # ==========================================================

    def distance(self):

        R = 6371000.0

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)

        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2)**2 +
            math.cos(lat1) *
            math.cos(lat2) *
            math.sin(dlon / 2)**2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    # ==========================================================
    # BEARING
    # ==========================================================

    def bearing(self):

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)

        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)

        x = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1) *
            math.cos(lat2) *
            math.cos(dlon)
        )

        return math.atan2(y, x)

    # ==========================================================
    # CONTROL LOOP
    # ==========================================================

    def control_loop(self):

        if self.current_lat is None:
            return

        # ======================================================
        # RTK CHECK
        # ======================================================

        if self.rtk_fix_type != 4:

            self.get_logger().warn(
                f"RTK not FIXED (state={self.rtk_fix_type}) -> navigation degraded"
            )

        # ======================================================
        # NAVIGATION
        # ======================================================

        dist = self.distance()

        target_bearing = self.bearing()

        angle_error = self.normalize(target_bearing - self.current_yaw)

        cmd = Twist()

        # STOP
        if dist < self.goal_tolerance:

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

            self.cmd_pub.publish(cmd)

            self.get_logger().info("TARGET REACHED")

            return

        # ======================================================
        # RTK DEPENDENT BEHAVIOR
        # ======================================================

        if self.rtk_fix_type == 4:
            # RTK FIX → navigation précise
            kp = 1.2
            speed = 0.5

        elif self.rtk_fix_type == 2:
            # GPS only → plus lent
            kp = 0.8
            speed = 0.3

        else:
            # NO FIX → très lent ou stop
            kp = 0.4
            speed = 0.0

        # ======================================================
        # CONTROL
        # ======================================================

        if abs(angle_error) > 0.3:

            cmd.linear.x = 0.0
            cmd.angular.z = kp * angle_error

        else:

            cmd.linear.x = speed
            cmd.angular.z = 0.5 * angle_error

        self.cmd_pub.publish(cmd)

    # ==========================================================
    # UTIL
    # ==========================================================

    def normalize(self, a):

        return math.atan2(math.sin(a), math.cos(a))


def main():

    rclpy.init()

    node = GPSRTKNavigator()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()