#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from ublox_ubx_msgs.msg import UBXNavPVT

from scipy.spatial.transform import Rotation


class GPSRTKNavigator(Node):

    def __init__(self):

        super().__init__('gps_rtk_navigator')

        # =====================================================
        # CIBLE GPS
        # =====================================================

        self.target_lat = 43.6153733
        self.target_lon = 7.072748

        self.goal_tolerance = 0.5

        # =====================================================
        # ETAT ROBOT
        # =====================================================

        self.current_lat = None
        self.current_lon = None

        self.current_yaw = 0.0

        # =====================================================
        # ETAT RTK
        # =====================================================

        self.rtk_state = 0

        # 0 = no RTK
        # 1 = RTK FLOAT
        # 2 = RTK FIX

        # =====================================================
        # SUBSCRIBERS
        # =====================================================

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

        self.create_subscription(
            UBXNavPVT,
            '/navpvt',
            self.navpvt_callback,
            10
        )

        # =====================================================
        # CMD_VEL
        # =====================================================

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # =====================================================
        # TIMER
        # =====================================================

        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.get_logger().info('GPS RTK Navigator started')

    # =========================================================
    # GPS CALLBACK
    # =========================================================

    def gps_callback(self, msg):

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    # =========================================================
    # ODOM CALLBACK
    # =========================================================

    def odom_callback(self, msg):

        q = msg.pose.pose.orientation

        quaternion = [
            q.x,
            q.y,
            q.z,
            q.w
        ]

        rotation = Rotation.from_quat(quaternion)

        yaw = rotation.as_euler('xyz')[2]

        # self.current_yaw = yaw
        self.current_yaw = yaw + math.pi

    # =========================================================
    # NAVPVT CALLBACK
    # =========================================================

    def navpvt_callback(self, msg):

        # Extraction état RTK
        carr_soln = (msg.flags >> 6) & 0b11

        self.rtk_state = carr_soln

    # =========================================================
    # DISTANCE GPS
    # =========================================================

    def compute_distance(self):

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

    # =========================================================
    # BEARING
    # =========================================================

    def compute_bearing(self):

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

        return math.atan2(y, x)

    # =========================================================
    # NORMALIZE ANGLE
    # =========================================================

    def normalize_angle(self, angle):

        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    # =========================================================
    # STOP ROBOT
    # =========================================================

    def stop_robot(self):

        cmd = Twist()

        self.cmd_pub.publish(cmd)

    # =========================================================
    # CONTROL LOOP
    # =========================================================

    def control_loop(self):

        if self.current_lat is None:
            return

        # =====================================================
        # CALCULS
        # =====================================================

        distance = self.compute_distance()

        bearing = self.compute_bearing()

        angle_error = self.normalize_angle(
            bearing - self.current_yaw
        )

        # =====================================================
        # ETAT RTK
        # =====================================================

        if self.rtk_state == 2:

            rtk_status = 'RTK FIX'

            linear_speed = 0.5
            angular_gain = 1.2

        elif self.rtk_state == 1:

            rtk_status = 'RTK FLOAT'

            linear_speed = 0.3
            angular_gain = 0.8

        else:

            rtk_status = 'GPS ONLY'

            linear_speed = 0.15
            angular_gain = 0.5

        # =====================================================
        # DEBUG
        # =====================================================

        self.get_logger().info(
            f'{rtk_status} | '
            f'Distance={distance:.2f} m | '
            f'Angle={math.degrees(angle_error):.1f} deg'
        )
        self.get_logger().info(
            f"Bearing={math.degrees(target_bearing):.1f} "
            f"Yaw={math.degrees(self.current_yaw):.1f}"
        )

        # =====================================================
        # OBJECTIF ATTEINT
        # =====================================================

        if distance < self.goal_tolerance:

            self.get_logger().info(
                'TARGET REACHED'
            )

            self.stop_robot()

            return

        # =====================================================
        # CONTROLE
        # =====================================================

        cmd = Twist()

        if abs(angle_error) > 0.3:

            cmd.linear.x = 0.0

            cmd.angular.z = (
                angular_gain
                * angle_error
            )

        else:

            cmd.linear.x = linear_speed

            cmd.angular.z = (
                0.5
                * angle_error
            )

        self.cmd_pub.publish(cmd)


# =============================================================
# MAIN
# =============================================================

def main(args=None):

    rclpy.init(args=args)

    node = GPSRTKNavigator()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        node.stop_robot()

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()