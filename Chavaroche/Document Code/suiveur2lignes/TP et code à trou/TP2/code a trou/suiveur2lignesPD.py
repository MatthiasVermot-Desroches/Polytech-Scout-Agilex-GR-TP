#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
import time

class RobotSuiveur(Node):
    def __init__(self):
        super().__init__('control_line_node')
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.image_sub = self.create_subscription(Float32, '/line_tracking/error', self.error_callback, 10)

        self.timer = self.create_timer(0.1, self.boucle)

        self.error = 0.0
        self.last_error = 0.0
        self.state = 'LIGNE_DROITE' # État initial de la FSM

        self.kp = 0.002
        self.kd = 0.001

        self.last_time = time.time()

    def error_callback(self, msg):
        """Met à jour l'erreur de suivi dès qu'un nouveau message arrive."""
        self.error = msg.data

    def boucle(self):
        """Boucle de contrôle principale exécutée à 10Hz."""
        msg = Twist()
        current_time = time.time()
        
        dt = current_time - self.last_time
        
        if dt <= 0.0: 
            dt = 0.1
            
        self.last_time = current_time
        
        current_error = self.error
        delta_error = current_error - self.last_error
        
       
        erreur_absolue = abs(current_error)
        
        if erreur_absolue < 15.0:
            self.state = 'LIGNE_DROITE'
            msg.linear.x = 0.2  # Vitesse nominale rapide sur ligne droite
            
        elif 15.0 <= erreur_absolue < 60.0:
            self.state = 'VIRAGE_BRUSQUE'
            msg.linear.x = 0.1  # On ralentit de moitié pour laisser le temps de tourner
            
        else:
            self.state = 'DEMI_TOUR'
            msg.linear.x = 0.0  

        P_correction = self.kp * current_error
        D_correction = self.kd * (delta_error / dt)
        
        correction_totale = P_correction + D_correction
        if self.state == 'DEMI_TOUR':
            msg.angular.z = -0.5 if self.last_error >= 0 else 0.5
        else:
            msg.angular.z = -correction_totale
        
        self.last_error = current_error

        print(f"[{self.state}] Erreur: {current_error:.2f} | Cmd Vg: {msg.linear.x:.2f} m/s | Cmd Wz: {msg.angular.z:.2f} rad/s")
        self.pub.publish(msg)

def main():
    rclpy.init()
    robot = RobotSuiveur()
    print("Nœud de contrôle initialisé. Le robot suit le chemin — Ctrl+C pour arrêter")
    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur.")
    finally:
        # Sécurité : arrêt des moteurs avant la fermeture
        stop_msg = Twist()
        robot.pub.publish(stop_msg)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
