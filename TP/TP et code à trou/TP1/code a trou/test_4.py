#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import math

class RobotSimple(Node):
    def __init__(self):
        super().__init__('robot_simple')
        # Publisher pour les commandes de vitesse
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        # Subscriptions pour l'odométrie et le LiDAR
        self.sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.sub_lidar = self.create_subscription(PointCloud2, '/rslidar_points', self.lidar_callback, 10)
        # Dans le subscriber, on retrouve le type de donnée (ici PointCloud2) et le nom du topic (ici /rslidar_points) ainsi que la fonction de callback (ici lidar_callback) et la taille de la file d'attente (ici 10)
        # La file d'attente est utilisée pour stocker les messages reçus lorsque le robot ne peut pas les traiter immédiatement. Si la file d'attente est pleine, les messages les plus anciens seront supprimés pour faire de la place aux nouveaux.

        # Variables d'état du robot
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.start_x = 0.0
        self.start_y = 0.0
        self.start_yaw = 0.0

        # Cibles de mouvement et rotation
        self.distance_cible = 0.0
        self.avance = True
        self.en_mouvement = False

        self.rotation_cible = 0.0
        self.en_rotation = False

        # Sécurité LiDAR
        self.obstacle_devant   = False
        self.obstacle_derriere = False
        self.distance_securite = 0.8

        # Distances par secteur
        self.dist_devant   = float('inf')
        self.dist_derriere = float('inf')
        self.dist_gauche   = float('inf')
        self.dist_droite   = float('inf')

        self.etat = "AVANCER"

        # Timer pour la boucle principale, appelée à 10Hz
        self.timer = self.create_timer(0.1, self.boucle)

    # Callbacks pour l'odométrie et le LiDAR, appelés à chaque message reçu sur les topics respectifs tout les deux à 10Hz
    # Pour connaitre la fréquence de publication des messages, on peut utiliser la commande `ros2 topic hz /nom_du_topic` dans le terminal. Par exemple, `ros2 topic hz /odom` pour voir la fréquence de publication de l'odométrie.
    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        q = msg.pose.pose.orientation
        
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

    def lidar_callback(self, msg):
        # Initialisation des distances à l'infini pour trouver les minimums
        dist_devant   = float('inf')
        dist_derriere = float('inf')
        dist_gauche   = float('inf')
        dist_droite   = float('inf')

        # On parcourt les points du LiDAR pour trouver les distances minimales dans chaque secteur
        for point in pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True):
            x, y, z = point

            # Filtre hauteur adapté au RS-Helios monté haut
            if z < -0.5 or z > 0.2:
                continue

            dist = math.sqrt(x**2 + y**2)

            # Couloir large de 2m pour bien détecter les murs
            if x > 0.2 and abs(y) < 2.0:
                dist_devant = min(dist_devant, dist)

            if x < -0.2 and abs(y) < 2.0:
                dist_derriere = min(dist_derriere, dist)

            # Largeur du robot + marge pour détecter les obstacles sur les côtés
            if y > 0.2 and abs(x) < 2.0:
                dist_gauche = min(dist_gauche, dist)

            if y < -0.2 and abs(x) < 2.0:
                dist_droite = min(dist_droite, dist)

        # Met à jour les distances et les flags d'obstacle
        self.dist_devant   = dist_devant
        self.dist_derriere = dist_derriere
        self.dist_gauche   = dist_gauche
        self.dist_droite   = dist_droite

        # On considère qu'il y a un obstacle si la distance est inférieure à la distance de sécurité
        self.obstacle_devant   = dist_devant   < self.distance_securite
        self.obstacle_derriere = dist_derriere < self.distance_securite

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

    def meilleure_direction(self):
        # Choisit la direction avec la plus grande distance libre
        distances = {
            'gauche': self.dist_gauche,
            'droite': self.dist_droite,
        }
        return max(distances, key=distances.get) # distances.get renvoie vers les valeurs (plutot que les noms des items) du dictionnaire, et max choisit la clé associée à la plus grande valeur

    # La boucle est maintenant un machine à états. 
    def boucle(self):
        msg = Twist()

        # ÉTAT 1 : Le robot avance et surveille la route
        if self.etat == "AVANCER":
            if self.obstacle_devant:
                direction = 
                self.get_logger().info(f"Obstacle ! Changement d'etat -> Tourner a {direction}")
                
                angle = 30 if direction == 'gauche' else -30
                self.rotation_cible = math.radians(angle)
                self.start_yaw = 
                
                self.etat = ""
            else:
                msg.linear.x =

        # ÉTAT 2 : Le robot est en train de pivoter pour s'enfuir
        elif self.etat == "TOURNER":
            msg.linear.x =
            if abs(self.angle_parcouru()) < abs(self.rotation_cible):
                msg.angular.z =  if self.rotation_cible > 0 else 
            else:
                # La rotation est finie, on coupe la rotation et on re-teste le champ libre
                msg.angular.z = 
                self.etat = ""
                self.get_logger().info("Fin de rotation, reprise de la marche avant.")

        # On publie le message unique à la toute fin
        self.pub.publish(msg)

def main():
    rclpy.init()
    robot = RobotSimple()

    # On laisse ROS 2 gérer le timing de manière totalement asynchrone
    print("Le robot explore la pièce en mode Machine à États — Ctrl+C pour arrêter")
    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        pass
        
    robot.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
