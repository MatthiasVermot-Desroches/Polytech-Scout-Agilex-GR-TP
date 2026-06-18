#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

# from tf_transformations import euler_from_quaternion
from scipy.spatial.transform import Rotation


class GPSNavigationEKF(Node):

    def __init__(self):

        super().__init__('gps_navigation_ekf')

        # ==========================================================
        # PARAMÈTRES
        # ==========================================================

        # Coordonnée GPS cible
        self.target_lat = 43.61550
        self.target_lon = 7.07280

        # Distance d'arrêt
        self.goal_tolerance = 0.2  # mètres

        # Gains du contrôleur
        self.kp_angular = 1.2
        self.linear_speed = 0.5

        # ==========================================================
        # ÉTAT ROBOT
        # ==========================================================

        # GPS
        self.current_lat = None
        self.current_lon = None

        # Pose EKF
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # ==========================================================
        # SUBSCRIBERS
        # ==========================================================

        # GPS brut
        self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
            10
        )

        # Pose filtrée EKF
        self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.filtered_odom_callback,
            10
        )

        # ==========================================================
        # PUBLISHER CMD_VEL
        # ==========================================================

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # ==========================================================
        # TIMER
        # ==========================================================

        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.get_logger().info('====================================')
        self.get_logger().info('GPS + EKF Navigation Started')
        self.get_logger().info('====================================')

    # ==============================================================
    # CALLBACK GPS
    # ==============================================================

    def gps_callback(self, msg):

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    # ==============================================================
    # CALLBACK EKF
    # ==============================================================

    def filtered_odom_callback(self, msg):

        # Position filtrée
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Orientation filtrée
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
        # self.current_yaw = yaw + math.pi
        self.current_yaw = yaw

    # ==============================================================
    # DISTANCE GPS
    # ==============================================================

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

    # ==============================================================
    # ANGLE VERS CIBLE
    # ==============================================================

    def compute_bearing_to_target(self):

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

    # ==============================================================
    # NORMALISATION ANGLE
    # ==============================================================

    def normalize_angle(self, angle):

        return math.atan2(
            math.sin(angle),
            math.cos(angle)
        )

    # ==============================================================
    # STOP ROBOT
    # ==============================================================

    def stop_robot(self):

        cmd = Twist()

        cmd.linear.x = 0.0
        cmd.angular.z = 0.0

        self.cmd_pub.publish(cmd)

    # ==============================================================
    # BOUCLE PRINCIPALE
    # ==============================================================

    def control_loop(self):

        # Attente GPS
        if self.current_lat is None:

            self.get_logger().info(
                'Waiting for GPS...'
            )

            return

        # ==========================================================
        # CALCULS
        # ==========================================================

        distance = self.compute_distance_to_target()

        target_bearing = self.compute_bearing_to_target()

        angle_error = self.normalize_angle(
            target_bearing - self.current_yaw
        )

        # ==========================================================
        # AFFICHAGE DEBUG
        # ==========================================================

        self.get_logger().info(
            f'Distance: {distance:.2f} m | '
            f'Heading error: {math.degrees(angle_error):.1f} deg'
        )

        self.get_logger().info(
            f"Bearing={math.degrees(target_bearing):.1f} "
            f"Yaw={math.degrees(self.current_yaw):.1f}"
        )

        # ==========================================================
        # OBJECTIF ATTEINT
        # ==========================================================

        if distance < self.goal_tolerance:

            self.get_logger().info(
                '===================================='
            )

            self.get_logger().info(
                'TARGET REACHED'
            )

            self.get_logger().info(
                '===================================='
            )

            self.stop_robot()

            return

        # ==========================================================
        # CONTRÔLE PROPORTIONNEL
        # ==============================================================

        cmd = Twist()

        # Mauvaise orientation :
        # rotation sur place

        if abs(angle_error) > 0.25:

            cmd.linear.x = 0.0

            cmd.angular.z = (
                self.kp_angular
                * angle_error
            )

        # Bonne orientation :
        # avance + correction

        else:

            cmd.linear.x = self.linear_speed

            cmd.angular.z = (
                0.5
                * angle_error
            )

        # Saturation sécurité

        max_angular_speed = 1.0

        if cmd.angular.z > max_angular_speed:
            cmd.angular.z = max_angular_speed

        if cmd.angular.z < -max_angular_speed:
            cmd.angular.z = -max_angular_speed

        # ==========================================================
        # PUBLICATION
        # ==============================================================

        self.cmd_pub.publish(cmd)


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):

    rclpy.init(args=args)

    node = GPSNavigationEKF()

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