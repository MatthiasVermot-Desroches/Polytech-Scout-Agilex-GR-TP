#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

#Script pour inverser l'IMU et la faire correspondre aux normes ROS2


class ImuCorrectionNode(Node):
    def __init__(self):
        super().__init__('imu_correction_node')
        
        # Configuration de la QoS (Quality of Service) standard pour les capteurs
        qos_profile = rclpy.qos.QoSProfile(
            reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
            history=rclpy.qos.HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Souscription au topique de l'IMU inversée
        self.subscription = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            qos_profile
        )
        
        # Publication sur le nouveau topique corrigé
        self.publisher = self.create_publisher(
            Imu,
            '/imu/data_corrected',
            qos_profile
        )
        
        self.get_logger().info('Nœud de correction IMU initialisé. Axe Z inversé !')

    def imu_callback(self, msg):
        # 1. Correction de la vitesse angulaire (Règle de la main droite pour le Yaw)
        msg.angular_velocity.z = -msg.angular_velocity.z
        
        # 2. Correction de l'accélération linéaire (Axe Z vers le haut)
        msg.linear_acceleration.z = -msg.linear_acceleration.z
        
        # 3. Correction du Quaternion (Remapping de [w, x, y, z] vers [x, y, z, w])
        # On sauvegarde les valeurs brutes erronées reçues du driver
        raw_x = msg.orientation.x  # Contient en réalité 'w' (~0.97)
        raw_y = msg.orientation.y  # Contient en réalité 'x' (~0.24)
        raw_z = msg.orientation.z  # Contient en réalité 'y' (~0.01)
        raw_w = msg.orientation.w  # Contient en réalité 'z' (~0.007)
        
        # On les réassigne dans les bonnes cases au standard ROS 2
        msg.orientation.x = raw_y  # Vrai X
        msg.orientation.y = raw_z  # Vrai Y
        msg.orientation.z = raw_w  # Vrai Z (Le Cap / Yaw)
        msg.orientation.w = raw_x  # Vrai W (La Magnitude)

        # On republie le message corrigé
        self.publisher.publish(msg)
def main(args=None):
    rclpy.init(args=args)
    node = ImuCorrectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Arrêt du nœud de correction IMU.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()