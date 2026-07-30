#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import math
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np

class RobotSimple(Node):
    def __init__(self):
        super().__init__('control_line_node')
        # Publisher pour les commandes de vitesse
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        # Abonnement au flux RGB de la RealSense D435
        self.image_sub = self.create_subscription(Float32, '/line_tracking/error', self.error_callback, 10)
        # Ajuste le topic si ton driver utilise un autre nom

        # Timer pour la boucle principale, appelée à 10Hz
        self.timer = self.create_timer(0.1, self.boucle)

        self.error = 0.0

    def error_callback(self, msg):
        # Met à jour l'erreur de suivi de ligne à partir du message reçu
        self.error = msg.data
        return

    # Boucle principale appelée à 10Hz par le timer, qui gère les mouvements et les rotations en fonction des obstacles et des cibles
    def boucle(self):
        # Crée un message de commande de vitesse
        msg = Twist()
        # Si on n'a pas d'erreur, on avance
        if -10 <= self.error <= 10:
            msg.linear.x = 0.2
            print("Suivi de ligne correct, avance à 0.2 m/s")
        # Si l'erreur est trop grande, on tourne pour corriger la trajectoire
        else:
        # On utilise un gain plus doux (0.003) car l'erreur peut monter à 424 pixels !
            gain_kp = 0.003
            
            # En ros pour tourner à gauche, on met une valeur positive sur angular.z, et pour tourner à droite, on met une valeur négative. 
            # Comme l'erreur est positive quand la ligne est à droite du robot, on doit inverser le signe pour que le robot tourne dans la bonne direction.
            msg.angular.z = - (self.error * gain_kp)
            
            # On ralentit la vitesse linéaire dans les virages pour ne pas rater la piste
            msg.linear.x = 0.1
            
        self.pub.publish(msg)

def main():
    # Initialisation du noeud ROS et création de l'instance du robot
    rclpy.init()
    robot = RobotSimple()

    print("Le robot suit le chemin — Ctrl+C pour arrêter")

    try:
        # rclpy.spin gère nativement et proprement les timers et les publishers en tâche de fond
        rclpy.spin(robot)
    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur.")
    finally:
        # Par sécurité, on publie un message d'arrêt complet avant de fermer le nœud
        stop_msg = Twist()
        robot.pub.publish(stop_msg)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
