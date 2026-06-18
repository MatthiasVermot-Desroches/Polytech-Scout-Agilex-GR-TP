#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Imu
from sensor_msgs.msg import MagneticField


class ImuFusionNode(Node):

    def __init__(self):

        super().__init__('imu_fusion_node')

        # ======================================================
        # DERNIERS MESSAGES
        # ======================================================

        self.last_imu = None
        self.last_mag = None

        # ======================================================
        # SUBSCRIBERS
        # ======================================================

        self.imu_sub = self.create_subscription(
            Imu,
            '/imu/data_raw',
            self.imu_callback,
            qos_profile_sensor_data
        )

        self.mag_sub = self.create_subscription(
            MagneticField,
            '/imu/mag',
            self.mag_callback,
            qos_profile_sensor_data
        )

        # ======================================================
        # PUBLISHER
        # ======================================================

        self.imu_pub = self.create_publisher(
            Imu,
            '/imu/data',
            10
        )

        self.get_logger().info('IMU Fusion Node started')

    # ==========================================================
    # CALLBACK IMU
    # ==========================================================

    def imu_callback(self, msg):

        self.last_imu = msg

        self.compute_and_publish()

    # ==========================================================
    # CALLBACK MAG
    # ==========================================================

    def mag_callback(self, msg):

        self.last_mag = msg

        self.compute_and_publish()

    # ==========================================================
    # COMPUTE ORIENTATION
    # ==========================================================

    def compute_and_publish(self):

        if self.last_imu is None:
            return

        if self.last_mag is None:
            return

        # ======================================================
        # ACCELEROMETER
        # ======================================================

        ax = self.last_imu.linear_acceleration.x
        ay = self.last_imu.linear_acceleration.y
        az = self.last_imu.linear_acceleration.z

        # inversion axe Z si nécessaire
        # az = -az

        roll = math.atan2(ay, az)

        pitch = math.atan2(
            -ax,
            math.sqrt(ay * ay + az * az)
        )

        # ======================================================
        # MAGNETOMETER
        # ======================================================

        mx = self.last_mag.magnetic_field.x
        my = self.last_mag.magnetic_field.y
        mz = self.last_mag.magnetic_field.z

        # ======================================================
        # TILT COMPENSATION
        # ======================================================

        mx2 = (
            mx * math.cos(pitch)
            + mz * math.sin(pitch)
        )

        my2 = (
            mx * math.sin(roll) * math.sin(pitch)
            + my * math.cos(roll)
            - mz * math.sin(roll) * math.cos(pitch)
        )

        # yaw = math.atan2(-my2, mx2)
        yaw = math.atan2(my2, mx2)

        # ======================================================
        # QUATERNION
        # ======================================================

        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)

        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy

        # ======================================================
        # IMU MESSAGE
        # ======================================================

        imu_msg = Imu()

        imu_msg.header.stamp = self.get_clock().now().to_msg()

        imu_msg.header.frame_id = 'imu_link'

        # ======================================================
        # ORIENTATION
        # ======================================================

        imu_msg.orientation.w = qw
        imu_msg.orientation.x = qx
        imu_msg.orientation.y = qy
        imu_msg.orientation.z = qz

        # ======================================================
        # COPY GYRO + ACCEL
        # ======================================================

        imu_msg.angular_velocity = (
            self.last_imu.angular_velocity
        )

        imu_msg.linear_acceleration = (
            self.last_imu.linear_acceleration
        )

        # ======================================================
        # COVARIANCES
        # ======================================================

        # Orientation covariance
        imu_msg.orientation_covariance[0] = 0.01
        imu_msg.orientation_covariance[4] = 0.01
        imu_msg.orientation_covariance[8] = 0.01

        # Angular velocity covariance
        imu_msg.angular_velocity_covariance[0] = 0.02
        imu_msg.angular_velocity_covariance[4] = 0.02
        imu_msg.angular_velocity_covariance[8] = 0.02

        # Linear acceleration covariance
        imu_msg.linear_acceleration_covariance[0] = 0.04
        imu_msg.linear_acceleration_covariance[4] = 0.04
        imu_msg.linear_acceleration_covariance[8] = 0.04

        # ======================================================
        # PUBLISH
        # ======================================================

        self.imu_pub.publish(imu_msg)


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):

    rclpy.init(args=args)

    node = ImuFusionNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()