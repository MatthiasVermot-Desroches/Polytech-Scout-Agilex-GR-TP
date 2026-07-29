#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Imu, MagneticField


class ImuFusionNode(Node):

    def __init__(self):

        super().__init__('imu_fusion_node')

        self.last_imu = None
        self.last_mag = None

        self.last_time = None

        self.yaw = 0.0
        
        self.yaw_initialized = False

        self.mag_alpha = 0.01 

        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0
        self.alpha_accel = 0.02  

        self.create_subscription(
            Imu,
            '/imu/data_raw',
            self.imu_callback,
            qos_profile_sensor_data
        )

        self.create_subscription(
            MagneticField,
            '/imu/mag',
            self.mag_callback,
            qos_profile_sensor_data
        )

        self.imu_pub = self.create_publisher(
            Imu,
            '/imu/data',
            10
        )

        self.get_logger().info("IMU Fusion Node started (complementary filter WITH Magnetometer)")

    def imu_callback(self, msg):

        self.last_imu = msg

        now = self.get_clock().now()

        if self.last_time is None:
            self.last_time = now
            return

        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        gz = msg.angular_velocity.z
        self.yaw += gz * dt

        self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        self.compute_and_publish()

    def mag_callback(self, msg):

        self.last_mag = msg

    def compute_and_publish(self):

        if self.last_imu is None:
            return

        ax = self.last_imu.linear_acceleration.x
        ay = self.last_imu.linear_acceleration.y
        az = self.last_imu.linear_acceleration.z

        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

        self.roll_filtered = (1.0 - self.alpha_accel) * self.roll_filtered + self.alpha_accel * roll
        self.pitch_filtered = (1.0 - self.alpha_accel) * self.pitch_filtered + self.alpha_accel * pitch

        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0

        roll = self.roll_filtered
        pitch = self.pitch_filtered

        if self.last_mag is not None:

            mx = self.last_mag.magnetic_field.x
            my = self.last_mag.magnetic_field.y
            mz = self.last_mag.magnetic_field.z

            mx2 = mx * math.cos(pitch) + mz * math.sin(pitch)

            my2 = (mx * math.sin(roll) * math.sin(pitch)
                   + my * math.cos(roll)
                   - mz * math.sin(roll) * math.cos(pitch))

            yaw_mag_raw = math.atan2(my2, mx2)

            # yaw_mag_enu = yaw_mag_raw + (math.pi / 2.0)
            yaw_mag_enu = -yaw_mag_raw + (math.pi / 2.0)
            yaw_mag_enu = math.atan2(math.sin(yaw_mag_enu), math.cos(yaw_mag_enu))

            if not self.yaw_initialized:
                self.yaw = yaw_mag_enu
                self.yaw_initialized = True
                self.get_logger().info(f"Cap initial fixé par le magnétomètre : {math.degrees(self.yaw):.1f}° ENU")
            else:
                error = yaw_mag_enu - self.yaw
                error = math.atan2(math.sin(error), math.cos(error))

                self.yaw += self.mag_alpha * error
                self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        cy = math.cos(self.yaw * 0.5)
        sy = math.sin(self.yaw * 0.5)

        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)

        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        qw = cr * cp * cy + sr * sp * sy
        qx = sr * cp * cy - cr * sp * sy
        qy = cr * sp * cy + sr * cp * sy
        qz = cr * cp * sy - sr * sp * cy

        imu_msg = Imu()

        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'imu_link'

        imu_msg.orientation.w = qw
        imu_msg.orientation.x = qx
        imu_msg.orientation.y = qy
        imu_msg.orientation.z = qz

        imu_msg.angular_velocity = self.last_imu.angular_velocity
        imu_msg.linear_acceleration = self.last_imu.linear_acceleration

        imu_msg.orientation_covariance[0] = 0.01
        imu_msg.orientation_covariance[4] = 0.01
        imu_msg.orientation_covariance[8] = 0.01

        imu_msg.angular_velocity_covariance[0] = 0.02
        imu_msg.angular_velocity_covariance[4] = 0.02
        imu_msg.angular_velocity_covariance[8] = 0.02

        imu_msg.linear_acceleration_covariance[0] = 0.04
        imu_msg.linear_acceleration_covariance[4] = 0.04
        imu_msg.linear_acceleration_covariance[8] = 0.04

        self.imu_pub.publish(imu_msg)

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