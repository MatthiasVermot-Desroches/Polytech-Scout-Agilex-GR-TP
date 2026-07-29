#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Imu, MagneticField


class ImuFusionNode(Node):

    def __init__(self):

        super().__init__('imu_fusion_node')

        # =========================
        # STATE
        # =========================

        self.last_imu = None
        self.last_mag = None

        self.last_time = None

        # yaw estimé (fusion)
        self.yaw = 0.0
        
        # 🔥 NOUVEAU : Drapeau pour aligner le yaw sur la boussole au démarrage
        self.yaw_initialized = False

        # 🔥 CORRECTION : On active la boussole (0.05 = correction douce mais continue)
        self.mag_alpha = 0.01 

        # 🔥 NOUVEAU : Filtre passe-bas pour ignorer l'accélération des moteurs
        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0
        self.alpha_accel = 0.02  # Filtre très lissant (plus la valeur est petite, plus on ignore les secousses)

        # =========================
        # SUBSCRIBERS
        # =========================

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

        # =========================
        # PUBLISHER
        # =========================

        self.imu_pub = self.create_publisher(
            Imu,
            '/imu/data',
            10
        )

        self.get_logger().info("IMU Fusion Node started (complementary filter WITH Magnetometer)")

    # ==========================================================
    # CALLBACK IMU (gyro + accel)
    # ==========================================================

    def imu_callback(self, msg):

        self.last_imu = msg

        now = self.get_clock().now()

        if self.last_time is None:
            self.last_time = now
            return

        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now

        # =========================
        # GYRO INTEGRATION (yaw)
        # =========================

        gz = msg.angular_velocity.z
        self.yaw += gz * dt

        # normalize
        self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        self.compute_and_publish()

    # ==========================================================
    # CALLBACK MAG
    # ==========================================================

    def mag_callback(self, msg):
        self.last_mag = msg

    # ==========================================================
    # COMPUTE FUSION
    # ==========================================================

    def compute_and_publish(self):

        if self.last_imu is None:
            return

        # =========================
        # ACCELEROMETER (roll/pitch)
        # =========================

        ax = self.last_imu.linear_acceleration.x
        ay = self.last_imu.linear_acceleration.y
        az = self.last_imu.linear_acceleration.z

        # roll & pitch from accel
        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

        # Application du filtre passe-bas pour lisser les accélérations de démarrage/freinage
        self.roll_filtered = (1.0 - self.alpha_accel) * self.roll_filtered + self.alpha_accel * roll
        self.pitch_filtered = (1.0 - self.alpha_accel) * self.pitch_filtered + self.alpha_accel * pitch

        # --- OPTION ROBUSTESSE ---
        # Si vous testez sur un sol parfaitement PLAT (labo, bitume droit) :
        # Décommentez les deux lignes ci-dessous. Cela désactivera complètement la sensibilité
        # aux accélérations des moteurs et rendra le cap d'une stabilité absolue en ligne droite.
        #
        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0

        roll = self.roll_filtered
        pitch = self.pitch_filtered

        # =========================
        # MAGNETOMETER (yaw correction)
        # =========================

        if self.last_mag is not None:

            mx = self.last_mag.magnetic_field.x
            my = self.last_mag.magnetic_field.y
            mz = self.last_mag.magnetic_field.z

            # tilt compensation
            mx2 = mx * math.cos(pitch) + mz * math.sin(pitch)

            my2 = (mx * math.sin(roll) * math.sin(pitch)
                   + my * math.cos(roll)
                   - mz * math.sin(roll) * math.cos(pitch))

            # Angle brut de la boussole (0 = Nord magnétique)
            yaw_mag_raw = math.atan2(my2, mx2)

            # 🔥 CORRECTION REPERE : Conversion vers ROS ENU (0 = Est, Anti-horaire)
            # yaw_mag_enu = yaw_mag_raw + (math.pi / 2.0)
            yaw_mag_enu = -yaw_mag_raw + (math.pi / 2.0)
            yaw_mag_enu = math.atan2(math.sin(yaw_mag_enu), math.cos(yaw_mag_enu))

            # 🔥 NOUVEAU : Si c'est le premier calcul, on force le yaw à la valeur de la boussole
            if not self.yaw_initialized:
                self.yaw = yaw_mag_enu
                self.yaw_initialized = True
                self.get_logger().info(f"Cap initial fixé par le magnétomètre : {math.degrees(self.yaw):.1f}° ENU")
            else:
                # Calcul de l'erreur et application du filtre complémentaire
                error = yaw_mag_enu - self.yaw
                error = math.atan2(math.sin(error), math.cos(error))

                # Ajustement de l'intégration du gyro par la boussole
                self.yaw += self.mag_alpha * error
                self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        # =========================
        # QUATERNION BUILD
        # =========================

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

        # =========================
        # PUBLISH IMU
        # =========================

        imu_msg = Imu()

        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'imu_link'

        imu_msg.orientation.w = qw
        imu_msg.orientation.x = qx
        imu_msg.orientation.y = qy
        imu_msg.orientation.z = qz

        # copy gyro + accel
        imu_msg.angular_velocity = self.last_imu.angular_velocity
        imu_msg.linear_acceleration = self.last_imu.linear_acceleration

        # covariances 
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