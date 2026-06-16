#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
import time  # Correction du bug d'import

class RobotSimpleFSM(Node):
    def __init__(self):
        super().__init__('control_line_node')
        
        # Publisher pour les commandes de vitesse
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Abonnement à l'erreur du noeud de vision simple
        self.image_sub = self.create_subscription(Float32, '/line_tracking/error', self.error_callback, 10)

        # Timer pour la boucle principale à 10Hz
        self.timer = self.create_timer(0.1, self.boucle)

        # Variables de contrôle
        self.error = 0.0
        self.last_error = 0.0
        self.last_time = time.time()

        # Gains du correcteur PD (Correction du bug de portée avec self.)
        self.gain_kp = 0.0025
        self.gain_kd = 0.0012

        # Variable d'état pour la FSM : "LIGNE_DROITE", "VIRAGE_BRUSQUE", "DEMI_TOUR"
        self.etat_actuel = "LIGNE_DROITE"
        self.get_logger().info("Noeud de commande FSM prêt.")

    def error_callback(self, msg):
        self.error = msg.data

    def boucle(self):
        msg = Twist()
        
        # Calcul du pas de temps (dt)
        new_time = time.time()
        dt = new_time - self.last_time
        self.last_time = new_time
        if dt <= 0.0: dt = 0.1

        # Calcul du PID (Termes Proportionnel et Dérivé)
        delta_error = self.error - self.last_error
        self.last_error = self.error

        P_Correcteur = self.gain_kp * self.error
        D_Correcteur = self.gain_kd * (delta_error / dt)
        
        # Commande angulaire de base
        commande_angulaire = - (P_Correcteur + D_Correcteur)

        # ---------------------------------------------------------------------
        # ZONE À COMPLÉTER PAR LES ÉTUDIANTS : MACHINE À ÉTATS (FSM)
        # ---------------------------------------------------------------------
        
        # 1. Logique de transition des états
        if abs(self.error) <= 30.0:
            self.etat_actuel = "LIGNE_DROITE"
        elif 30.0 < abs(self.error) <= 250.0:
            # ------ À COMPLÉTER : Quel état si l'erreur devient modérée/forte ? ------
            self.etat_actuel = "VIRAGE_BRUSQUE"
        else:
            # ------ À COMPLÉTER : Quel état si l'erreur devient extrême (> 250 pixels) ? ------
            self.etat_actuel = "DEMI_TOUR"

        # 2. Logique cinématique selon l'état actif
        if self.etat_actuel == "LIGNE_DROITE":
            msg.linear.x = 0.25
            msg.angular.z = commande_angulaire
            
        elif self.etat_actuel == "VIRAGE_BRUSQUE":
            # En virage brusque, on réduit la vitesse linéaire pour ne pas glisser/rater la ligne
            # ------ À COMPLÉTER : Proposer des vitesses adaptées ------
            msg.linear.x = 0.12
            msg.angular.z = commande_angulaire

        elif self.etat_actuel == "DEMI_TOUR":
            # La ligne est presque perdue sur le côté, on pivote fortement sur place
            msg.linear.x = 0.0  # Arrêt de la translation
            # ------ À COMPLÉTER : Asservir le sens de rotation au signe de l'erreur ------
            if self.error > 0:
                msg.angular.z = -0.5  # Tourner à droite toute
            else:
                msg.angular.z = 0.5   # Tourner à gauche toute
                
        # ---------------------------------------------------------------------
        # FIN DE LA ZONE À COMPLÉTER
        # ---------------------------------------------------------------------

        # Publication de la commande de vitesse
        self.pub.publish(msg)

def main():
    rclpy.init()
    robot = RobotSimpleFSM()
    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        pass
    finally:
        stop_msg = Twist()
        robot.pub.publish(stop_msg)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
