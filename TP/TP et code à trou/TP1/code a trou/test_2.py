#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class RobotSimple(Node):
    def __init__(self):
        super().__init__('robot_simple')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.start_x = 0.0
        self.start_y = 0.0
        self.distance_cible = 0.0
        self.rotation_cible = 0.0
        self.avance = True
        self.rota_horloge = True
        self.en_mouvement = False
        self.en_rotation = False

        self.timer = self.create_timer(0.1, self.boucle)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

    def distance_parcourue(self):
        return math.sqrt(
            (self.x - self.start_x) ** 2 +
            (self.y - self.start_y) ** 2
        )

  
    def angle_parcouru(self):
        diff = self.yaw - self.start_yaw
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return diff

    def boucle(self):
        msg = Twist()

        if self.en_mouvement:
            if self.distance_parcourue() < self.distance_cible and self.avance:
                
            elif self.distance_parcourue() < abs(self.distance_cible) and not self.avance:
                
            else:
                
                self.en_mouvement = 
                self.get_logger().info('Arrivé !')
      
        if self.en_rotation:                      
            if abs(self.angle_parcouru()) < abs(self.target_angle):
                if self.target_angle > 0
                
                else :
                  
            else:
                
                self.en_rotation = 
                self.get_logger().info('Rotation terminée !')

        self.pub.publish(msg)



    def avancer(self, distance):
        self.start_x = self.x
        self.start_y = self.y
        self.avance = distance >= 0
        self.distance_cible = distance
        self.en_mouvement = True

    def tourner(self, angle_deg):
        self.target_angle = math.radians(angle_deg)
        self.start_yaw = self.yaw                  
        self.en_rotation = True


def main():
    rclpy.init()
    robot = RobotSimple()

    rclpy.spin_once(robot, timeout_sec=1.0)  # attendre odom

    while rclpy.ok():
        # On utilise try/except pour éviter les crashs si l'utilisateur entre une valeur non numérique
        try:
            distance = float(input("Combien de mètres ? "))
            rotation = float(input("Combien de degrés ? "))
        except ValueError:
            print('Valeur invalide.')
            continue

        robot.avancer(distance)
        while robot.en_mouvement and rclpy.ok():
            rclpy.spin_once(robot, timeout_sec=0.1)

        robot.tourner(rotation)
        while robot.en_rotation and rclpy.ok():
            rclpy.spin_once(robot, timeout_sec=0.1)

        print("Arrivé ! Prochaine commande ?")

        continuer = input('Continuer ? (o/n) : ')
        if continuer != 'o':
            break

    rclpy.shutdown()



if __name__ == '__main__':
    main()
