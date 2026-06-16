#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool
from std_msgs.msg import Float32
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import Float32MultiArray, Int32MultiArray
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
            '/camera/camera/color/image_raw', 
            self.image_callback,
            10
        )
        
        # Publishers
        self.error_pub = self.create_publisher(Float32, '/line_tracking/error_raw', 10)
        self.masse_pub = self.create_publisher(Float32MultiArray, '/camera/zones_masses', 10)
        self.route_pub = self.create_publisher(Int32MultiArray, '/camera/zones_route', 10)
        self.lost_pub = self.create_publisher(Bool, '/line_tracking/route_perdue', 10)
    
    def image_callback(self, msg):

        # Poids des lignes (la somme fait 1.0)
        # L1 (0.8) a beaucoup plus d'importance que L2 (0.2)
        POIDS_L1 = 0.8
        POIDS_L2 = 0.2
        
        # Initialisation de notre erreur finale
        erreur_calculer = 0.0

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f"Erreur de conversion CvBridge: {e}")
            return

        height, width, _ = cv_image.shape

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        lower_yellow = np.array([12,  70,  60])   
        upper_yellow = np.array([28, 255, 255])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Définition des coordonnées Y exactes pour nos 3 lignes de 1 pixel de haut
        Y_L3 = 320
        Y_L2 = 400
        Y_L1 = 479

        # Définition des limites des secteurs verticaux (Quarts)
        w_step = width // 10
        X_G = (0, w_step)          # Gauche : 0 à 212
        X_C = (w_step, 9 * w_step)  # Centre (2 quarts) : 212 à 636
        X_D = (9 * w_step, width)   # Droite : 636 à 848

        masses = {}
        centres_x = {}
        route_detectee = {}

        partitions = {
            'L3G': (Y_L3, X_G), 'L3': (Y_L3, X_C), 'L3D': (Y_L3, X_D),
            'L2G': (Y_L2, X_G), 'L2': (Y_L2, X_C), 'L2D': (Y_L2, X_D),
                                'L1': (Y_L1, X_C)
        }

        SEUIL_PRESENCE = 15 

        # Extraction et analyse de chaque segment de 1 pixel
        for nom, (y, (x_start, x_end)) in partitions.items():
            segment = mask[y, x_start:x_end]
            
            masse = int(np.sum(segment) / 255)
            masses[nom] = float(masse)
            
            route_detectee[nom] = 1 if masse > SEUIL_PRESENCE else 0
            
            if masse > 0:
                indices_jaunes = np.where(segment == 255)[0]
                cx_local = np.mean(indices_jaunes)
                centres_x[nom] = x_start + int(cx_local)
            else:
                centres_x[nom] = (x_start + x_end) // 2
        
        ordre_fixe = ['L1', 'L2', 'L2G', 'L2D', 'L3', 'L3G', 'L3D']

        # Publication des masses
        msg_masses = Float32MultiArray()
        msg_masses.data = [masses[z] for z in ordre_fixe]
        self.masse_pub.publish(msg_masses)

        # Publication des flags de présence
        msg_route = Int32MultiArray()
        msg_route.data = [route_detectee[z] for z in ordre_fixe]
        self.route_pub.publish(msg_route)
        
        # sum() sur les valeurs du dictionnaire : si ça vaut 0, c'est le vide absolu
        total_zones_detectees = sum(route_detectee.values())

        msg_lost = Bool()
        if total_zones_detectees == 0:
            msg_lost.data = True
            # On maintient l'erreur à 0.0 car on ne sait plus où aller
            erreur_calculer = 0.0
            self.get_logger().warn("ALERTE : Route totalement perdue !")
        else:
            msg_lost.data = False
            
        # On publie immédiatement l'état de santé de la trajectoire
        self.lost_pub.publish(msg_lost)

        # On calcule les erreurs individuelles par rapport au centre de l'image (424)
        err_L1 = float(centres_x['L1'] - 424)
        err_L2 = float(centres_x['L2'] - 424)
        
        # Cas 1 : On voit la route sur les deux lignes (Le cas nominal)
        if route_detectee['L1'] and route_detectee['L2']:
            erreur_calculer = (POIDS_L1 * err_L1) + (POIDS_L2 * err_L2)
            
        # Cas 2 : Perte de contact avec L1, mais L2 voit encore la route
        # On bascule à 100% sur L2 pour que le robot continue d'avancer/anticiper
        elif not route_detectee['L1'] and route_detectee['L2']:
            erreur_calculer = err_L2
            
        # Cas 3 : L1 voit la route mais L2 l'a perdue (ex: entrée sous un pont, ombre locale)
        # On fait confiance à L1 à 100%
        elif route_detectee['L1'] and not route_detectee['L2']:
            erreur_calculer = err_L1
            
        # Cas 4 : Perte totale de trajectoire sur l'axe central (Cul-de-sac ou virage à 90°)
        else:
            # Ici tu décideras quoi faire plus tard (ex: s'arrêter, ou chercher L2G/L2D)
            erreur_calculer = 0.0
            
        msg_error = Float32()
        msg_error.data = erreur_calculer
        self.error_pub.publish(msg_error)


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
