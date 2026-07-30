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
        self.start_x = 0.0
        self.start_y = 0.0
        self.distance_cible = 0.0
        self.en_mouvement = False

        self.timer = self.create_timer(0.1, self.boucle)

    def odom_callback(self, msg):
        # Mise à jour position réelle
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

    def distance_parcourue(self):
        return math.sqrt(
            (self.x - self.start_x) ** 2 +
            (self.y - self.start_y) ** 2
        )

    def boucle(self):
        msg = Twist()

        if self.en_mouvement:
            if self.distance_parcourue() < self.distance_cible:
                msg.linear.x = 0.2  # avance
            else:
                msg.linear.x = 0.0  # stop
                self.en_mouvement = False
                self.get_logger().info('Arrivé !')

        self.pub.publish(msg)

    def avancer(self, distance):
        self.start_x = self.x
        self.start_y = self.y
        self.distance_cible = distance
        self.en_mouvement = True

def main():
    rclpy.init()
    robot = RobotSimple()

    # Attendre le premier message odom
    rclpy.spin_once(robot, timeout_sec=1.0)

    distance = float(input("Combien de mètres ? "))
    robot.avancer(distance)

    rclpy.spin(robot)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
