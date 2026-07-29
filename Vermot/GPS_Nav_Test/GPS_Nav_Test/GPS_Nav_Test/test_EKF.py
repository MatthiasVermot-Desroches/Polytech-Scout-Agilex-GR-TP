#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

from scipy.spatial.transform import Rotation


#Test du GPS avec 2 EKFs et une node navsat_transform pour filtrer avec l'odométrie, l'orientation et les données GPS

class GPSNavigationEKF(Node):

    def __init__(self):

        super().__init__('gps_navigation_ekf')

        #target terrain de sport
        # self.target_lat = 43.6149513
        # self.target_lon = 7.0725748

        #target entre les batiments B et D
        # self.target_lat = 43.61550
        # self.target_lon = 7.07280

        #target BU
        self.target_lat = 43.6147098
        self.target_lon = 7.072223099

        self.goal_tolerance = 0.2  # m

        self.kp_angular = 1.0#0.5 #1.2
        self.linear_speed = 0.5

        self.startup_time = self.get_clock().now()
        self.mag_offset_deg = 0

        self.current_lat = None
        self.current_lon = None

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
            10
        )

        self.create_subscription(
            Odometry,
            '/odometry/global',
            # '/odom',
            self.odom_callback,
            10
        )


        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info("GPS + EKF GLOBAL Navigation started")


    def gps_callback(self, msg):
        self.current_lat = msg.latitude
        self.current_lon = msg.longitude

    def odom_callback(self, msg):

        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]

        r = Rotation.from_quat(quat)

        yaw = r.as_euler('zyx')[0]

        self.current_yaw = yaw + math.radians(self.mag_offset_deg)

        euler_xyz = r.as_euler('xyz', degrees=True)
        euler_zyx = r.as_euler('zyx', degrees=True)

    def compute_distance(self):

        # R = 6371000.0

        # lat1 = math.radians(self.current_lat)
        # lon1 = math.radians(self.current_lon)
        # lat2 = math.radians(self.target_lat)
        # lon2 = math.radians(self.target_lon)

        # dlat = lat2 - lat1
        # dlon = lon2 - lon1

        # a = (math.sin(dlat/2)**2 +
        #      math.cos(lat1) * math.cos(lat2) *
        #      math.sin(dlon/2)**2)

        # return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

        dy = (self.target_lat - self.current_lat) * 111139.0

        lat_rad = math.radians(self.current_lat)
        dx = (self.target_lon - self.current_lon) * 111139.0 * math.cos(lat_rad)

        dist = math.sqrt(dx**2 + dy**2)

        return dist

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


    def norm(self, a):
        return math.atan2(math.sin(a), math.cos(a))

    def stop(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def control_loop(self):

        if self.current_lat is None:
            self.get_logger().info("NONE LAT XD")
            return

        # now = self.get_clock().now()
        # elapsed_time = (now - self.startup_time).nanoseconds * 1e-9
        # if elapsed_time < 5.0:
        #     self.get_logger().info(f"Convergence IMU en cours... Patiente ({elapsed_time:.1f}/5.0s)")
        #     return

        self.get_logger().info("CONTROL LOOP")
        dist = self.compute_distance()
        
        bearing_geo = self.compute_bearing()

        bearing_ros_enu = (math.pi / 2.0) - bearing_geo
        bearing_ros_enu = math.atan2(math.sin(bearing_ros_enu), math.cos(bearing_ros_enu))

        # error = self.norm(bearing_ros_enu - self.current_yaw)
        # error = math.atan2(math.sin(bearing_ros_enu - self.current_yaw), math.cos(bearing_ros_enu - self.current_yaw))
        error = bearing_ros_enu - self.current_yaw
        error = math.atan2(math.sin(error), math.cos(error))

        self.get_logger().info(
            f"dist={dist:.2f}m | error={math.degrees(error):.1f}°"
        )     

        self.get_logger().info(
            f"bearing_geo={math.degrees(bearing_geo):.1f}° | "
            f"bearing_enu={math.degrees(bearing_ros_enu):.1f}° | "
            f"current_yaw_enu={math.degrees(self.current_yaw):.1f}°"
        )

        if dist < self.goal_tolerance:
            self.stop()
            self.get_logger().info("Objectif GPS atteint ! Arret du robot.")
            return

        cmd = Twist()

        if abs(error) > 0.25:
            cmd.linear.x = 0.0
            # if error > 0:
            #     cmd.angular.z = 0.4  # Tourne à gauche, ptet inverser le signe...
            # else:
            #     cmd.angular.z = -0.4 # Tourne à droite, ptet inverser le signe...
            # cmd.angular.z = self.kp_angular * error
            # cmd.angular.z = -self.kp_angular * error
        else:
            cmd.linear.x = self.linear_speed
            # cmd.angular.z = -0.5 * error
            # cmd.angular.z = 0.5 * error
            #cmd.angular.z = self.kp_angular * error
        cmd.angular.z = self.kp_angular * error

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