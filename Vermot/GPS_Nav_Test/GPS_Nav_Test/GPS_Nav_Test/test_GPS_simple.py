#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import Twist


class GPSNavigator(Node):

    def __init__(self):

        super().__init__('gps_navigator')

        # =====================================================
        # CIBLE GPS
        # =====================================================

        self.target_lat = 43.6153733
        self.target_lon = 7.072748

        # =====================================================
        # POSITION ACTUELLE
        # =====================================================

        self.current_lat = None
        self.current_lon = None

        # =====================================================
        # GPS
        # =====================================================

        self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
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
            0.5,
            self.control_loop
        )

        self.get_logger().info('GPS-only Navigator started')

    # =====================================================
    # GPS CALLBACK
    # =====================================================

    def gps_callback(self, msg):

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    # =====================================================
    # DISTANCE GPS
    # =====================================================

    def distance_to_target(self):

        R = 6371000.0

        lat1 = math.radians(self.current_lat)
        lon1 = math.radians(self.current_lon)

        lat2 = math.radians(self.target_lat)
        lon2 = math.radians(self.target_lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2)**2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2)**2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return R * c

    # =====================================================
    # ANGLE GPS
    # =====================================================

    def bearing_to_target(self):

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

    # =====================================================
    # BOUCLE DE CONTRÔLE
    # =====================================================

    def control_loop(self):

        if self.current_lat is None:
            return

        distance = self.distance_to_target()

        bearing = self.bearing_to_target()

        self.get_logger().info(
            f'Distance cible : {distance:.2f} m | '
            f'Bearing : {math.degrees(bearing):.1f} deg'
        )

        cmd = Twist()

        # =================================================
        # ARRIVÉE
        # =================================================

        if distance < 2.0:

            self.get_logger().info('Target reached')

            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

            self.cmd_pub.publish(cmd)

            return

        # =================================================
        # GPS SEUL :
        # comportement volontairement naïf
        # =================================================

        cmd.linear.x = 0.3

        # rotation lente constante
        # pour chercher la cible GPS
        cmd.angular.z = 0.2

        self.cmd_pub.publish(cmd)


def main(args=None):

    rclpy.init(args=args)

    node = GPSNavigator()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()