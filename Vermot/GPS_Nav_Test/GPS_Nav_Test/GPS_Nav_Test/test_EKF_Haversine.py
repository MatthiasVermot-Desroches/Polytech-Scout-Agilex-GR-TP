#!/usr/bin/env python3

import math
import time
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from scipy.spatial.transform import Rotation

#Test avec les 2 EKFs et la node navsat_transform, en utilisant Haversine pour calculer la distance à partir des données brutes du GPS

class DirectGPSNavigation(Node):

    def __init__(self):
        super().__init__('gps_navigation_ekf')

        self.target_lat = 43.6147098
        self.target_lon = 7.072223099

        self.goal_tolerance = 1.0  
        self.kp_angular = 0.8      
        self.linear_speed = 0.35 

        self.current_lat = None
        self.current_lon = None
        self.current_yaw = None

        self.last_lat = None
        self.last_lon = None
        self.gps_stable_start_time = None
        self.gps_is_stable = False
        self.stability_threshold = 1.5
        self.required_stable_duration = 3.0

        self.current_x = 0.0
        self.current_y = 0.0

        self.create_subscription(NavSatFix, '/fix', self.gps_callback, 10)
        self.create_subscription(Odometry, '/odometry/global', self.odom_callback, 10)

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("Système de Navigation Directe GPS (Haversine) Initialisé.")

    def gps_callback(self, msg):
        self.get_logger().info(f"📥 Message GPS reçu ! Lat: {msg.latitude:.8f}, Lon: {msg.longitude:.8f}")


        if msg.status.status < 0:
            return

        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

        if not self.gps_is_stable:
            if self.last_lat is not None and self.last_lon is not None:
                dist_drift = self.haversine_distance(self.current_lat, self.current_lon, self.last_lat, self.last_lon)
                
                if dist_drift < self.stability_threshold:
                    if self.gps_stable_start_time is None:
                        self.gps_stable_start_time = time.time()
                    elif time.time() - self.gps_stable_start_time >= self.required_stable_duration:
                        self.gps_is_stable = True
                        self.get_logger().info("Signal GPS stabilisé au sol ! Démarrage de la navigation.")
                else:
                    self.gps_stable_start_time = None

            self.last_lat = self.current_lat
            self.last_lon = self.current_lon

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]
        r = Rotation.from_quat(quat)
        self.current_yaw = r.as_euler('zyx')[0]

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dlambda = math.radians(lon2 - lon1)

        y = math.sin(dlambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
        
        bearing_clockwise_north = math.atan2(y, x)
        
        bearing_ros_enu = -bearing_clockwise_north + math.pi/2.0
        return math.atan2(math.sin(bearing_ros_enu), math.cos(bearing_ros_enu))

    def stop(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def control_loop(self):
        if self.current_lat is None or self.current_yaw is None:
            return

        if not self.gps_is_stable:
            self.get_logger().info("Attente de la stabilisation du signal GPS...", throttle_duration_sec=3.0)
            return

        dist = self.haversine_distance(self.current_lat, self.current_lon, self.target_lat, self.target_lon)
        target_bearing = self.calculate_bearing(self.current_lat, self.current_lon, self.target_lat, self.target_lon)

        error = target_bearing - self.current_yaw
        error = math.atan2(math.sin(error), math.cos(error))

        self.get_logger().info(
            f"DISTANCE RÉELLE = {dist:.2f}m | Erreur angulaire = {math.degrees(error):.1f}° | "
            f"Yaw EKF = {math.degrees(self.current_yaw):.1f}° | Cap requis = {math.degrees(target_bearing):.1f}°",
            throttle_duration_sec=0.5
        )

        if dist < self.goal_tolerance:
            self.stop()
            self.get_logger().info("Cible GPS atteinte ! Arrêt du robot.")
            self.timer.cancel()
            return

        cmd = Twist()

        if abs(error) > 0.43:
            cmd.linear.x = 0.0
            cmd.angular.z = self.kp_angular * error
        else:
            cmd.linear.x = self.linear_speed
            cmd.angular.z = self.kp_angular * error

        max_angular_speed = 0.4
        cmd.angular.z = max(min(cmd.angular.z, max_angular_speed), -max_angular_speed)

        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = DirectGPSNavigation()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()