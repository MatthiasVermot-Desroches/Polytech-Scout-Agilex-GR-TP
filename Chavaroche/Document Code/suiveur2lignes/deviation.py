#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np

class VisionLineNode(Node):
    def __init__(self):
        super().__init__('vision_line_node')
        
        # Outil pour convertir les images ROS en images OpenCV
        self.bridge = CvBridge()
        
        # Abonnement au flux RGB de la RealSense D435
        self.image_sub = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw', # Ajuste le topic si ton driver utilise un autre nom
            self.image_callback,
            10
        )
        
        # Publication de l'erreur calculée (en pixels)
        self.error_pub = self.create_publisher(Float32, '/line_tracking/error', 10)
        
        self.get_logger().info("Noeud de vision Realsense D435 Initialisé.")

    def image_callback(self, msg):
        try:
            # 1. Conversion du message ROS en image OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f"Erreur de conversion CvBridge: {e}")
            return

        # Dimensions de ton image : 848x480
        height, width, _ = cv_image.shape
        
        # 2. Conversion en niveaux de gris
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 3. Masquage (ROI) : On ignore le haut car le sol n'est visible qu'en bas (distance > 82cm)
        # On ne garde que les 120 derniers pixels verticaux (de 360 à 480)
        roi_start_row = 420
        roi_gray = gray[roi_start_row:height, :]
        
        # 4. Seuillage pour détecter les lignes grasses (Exemple ici : lignes NOIRES sur sol clair)
        # Tout ce qui est au-dessus de 200 (très clair/blanc) devient BLANC (255)
        # Tout le reste (sol gris foncé, lignes noires) devient NOIR (0)
        _, thresh = cv2.threshold(roi_gray, 200, 255, cv2.THRESH_BINARY)
        
        # 5. Calcul du centre de la ligne avec les moments d'OpenCV
        M = cv2.moments(thresh)
        
        if M['m00'] > 0:
            # Centre horizontal (cx) de la masse des deux lignes
            cx = int(M['m10'] / M['m00'])
            
            # L'erreur est la distance entre le centre de la caméra (848 / 2 = 424) et le cx trouvé
            # Erreur > 0 : le robot doit tourner à droite / Erreur < 0 : à gauche
            error = float(cx - (width / 2))
            
            # Publication de l'erreur
            error_msg = Float32()
            error_msg.data = error
            self.error_pub.publish(error_msg)

        else:
            # Si on ne voit aucune ligne, on publie une erreur nulle ou on gère la perte de ligne
            self.get_logger().warn("Aucune ligne détectée dans la zone de tracking !")

def main(args=None):
    rclpy.init(args=args)
    node = VisionLineNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
