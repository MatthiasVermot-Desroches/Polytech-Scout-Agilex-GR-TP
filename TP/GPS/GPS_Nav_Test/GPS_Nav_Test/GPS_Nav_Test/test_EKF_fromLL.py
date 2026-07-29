#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from scipy.spatial.transform import Rotation

from robot_localization.srv import FromLL


#Test du GPS avec les 2 EKFs et node navsat_transform, avec ajout d'une connexion au service from_LL pour convertir les coordonnées géographiques en coordonnées cartésiennes et mieux calculer la distance

class GPSNavigationEKF(Node):

    def __init__(self):
        super().__init__('gps_navigation_ekf')

        self.target_lat = 43.6147098
        self.target_lon = 7.072223099

        self.target_x = None
        self.target_y = None

        self.goal_tolerance = 0.2  # m
        self.kp_angular = 0.5
        self.linear_speed = 0.5

        self.current_lat = None
        self.current_lon = None
        self.current_x = None
        self.current_y = None
        self.current_yaw = None

        self._waiting_for_service_response = False

        self.create_subscription(NavSatFix, '/fix', self.gps_callback, 10)
        self.create_subscription(Odometry, '/odometry/global', self.odom_callback, 10)

        self.from_ll_client = self.create_client(FromLL, '/fromLL')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("GPS + EKF GLOBAL Navigation started (with /from_ll service)")

    def gps_callback(self, msg):
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]
        r = Rotation.from_quat(quat)
        self.current_yaw = r.as_euler('zyx')[0]

    def stop(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def from_ll_callback(self, future):
        try:
            response = future.result()
            self.target_x = response.map_point.x
            self.target_y = response.map_point.y
            self.get_logger().info(
                f"🎯 Cible initialisée via le service /from_ll ! "
                f"Target X: {self.target_x:.2f}m | Y: {self.target_y:.2f}m"
            )
        except Exception as e:
            self.get_logger().error(f"Échec de l'appel au service /from_ll : {e}")
            self._waiting_for_service_response = False

    def control_loop(self):
        if self.current_lat is None or self.current_x is None or self.current_yaw is None:
            self.get_logger().info("En attente des données GPS et EKF...")
            return

        if self.target_x is None:
            if not self.from_ll_client.service_is_ready():
                self.get_logger().info("En attente de la disponibilité du service /from_ll...")
                return

            if self._waiting_for_service_response:
                return

            self._waiting_for_service_response = True

            req = FromLL.Request()
            req.ll_point.latitude = self.target_lat
            req.ll_point.longitude = self.target_lon
            req.ll_point.altitude = 0.0

            self.get_logger().info(f"Demande de conversion de la cible ({self.target_lat}, {self.target_lon}) au service /from_ll...")
            
            future = self.from_ll_client.call_async(req)
            future.add_done_callback(self.from_ll_callback)
            return

        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y

        dist = math.sqrt(dx**2 + dy**2)
        
        bearing_ros_enu = math.atan2(dy, dx)

        error = bearing_ros_enu - self.current_yaw
        error = math.atan2(math.sin(error), math.cos(error))

        self.get_logger().info(
            f"dist={dist:.2f}m | error={math.degrees(error):.1f}° | "
            f"Robot X={self.current_x:.2f}m Y={self.current_y:.2f}m"
        )

        # self.get_logger().info(
        #     f"Cap Cible (ENU): {math.degrees(bearing_ros_enu):.1f}° | "
        #     f"Cap Robot (Yaw): {math.degrees(self.current_yaw):.1f}° | "
        #     f"Erreur calculée: {math.degrees(error):.1f}°"
        # )

        if dist < self.goal_tolerance:
            self.stop()
            self.get_logger().info("Objectif atteint ! Arrêt du robot.")
            return

        cmd = Twist()

        if abs(error) > 0.25:
            cmd.linear.x = 0.0
            cmd.angular.z = self.kp_angular * error
        else:                 
            cmd.linear.x = self.linear_speed
            cmd.angular.z = self.kp_angular * error

        max_angular_speed = 0.5
        cmd.angular.z = max(min(cmd.angular.z, max_angular_speed), -max_angular_speed)

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = GPSNavigationEKF()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()