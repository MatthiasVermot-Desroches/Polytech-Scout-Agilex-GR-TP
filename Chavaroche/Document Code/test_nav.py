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

        # Timer pour la boucle principale, appelée à 10Hz
        self.timer = self.create_timer(0.1, self.boucle)

    # Callbacks pour l'odométrie et le LiDAR, appelés à chaque message reçu sur les topics respectifs tout les deux à 10Hz
    # Pour connaitre la fréquence de publication des messages, on peut utiliser la commande `ros2 topic hz /nom_du_topic` dans le terminal. Par exemple, `ros2 topic hz /odom` pour voir la fréquence de publication de l'odométrie.
    def odom_callback(self, msg):
        # Met à jour la position et l'orientation du robot à partir de l'odométrie
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny, cosy)

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
            if z < 0.1 or z > 2.0:
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
        # Calcul de la distance parcourue depuis le début du mouvement
        return math.sqrt(
            (self.x - self.start_x) ** 2 +
            (self.y - self.start_y) ** 2
        )

    def angle_parcouru(self):
        # Calcul de l'angle parcouru depuis le début de la rotation, en gérant le ±pi
        diff = self.yaw - self.start_yaw
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return diff

    # Méthodes pour démarrer un mouvement ou une rotation vers une cible donnée
    def avancer(self, distance):
        # Enregistre la position de départ et la direction du mouvement, puis active le flag de mouvement
        self.start_x = self.x
        self.start_y = self.y
        self.avance  = distance >= 0
        self.distance_cible = distance
        self.en_mouvement   = True

    def tourner(self, angle_deg):
        # Enregistre l'orientation de départ et la cible de rotation, puis active le flag de rotation
        self.start_yaw      = self.yaw
        self.rotation_cible = math.radians(angle_deg)
        self.en_rotation    = True

    def meilleure_direction(self):
        # Choisit la direction avec la plus grande distance libre
        distances = {
            'gauche': self.dist_gauche,
            'droite': self.dist_droite,
        }
        return max(distances, key=distances.get)

     # Boucle principale appelée à 10Hz par le timer, qui gère les mouvements et les rotations en fonction des obstacles et des cibles
    def boucle(self):
        # Crée un message de commande de vitesse
        msg = Twist()
        # Si on est en mouvement, on vérifie les obstacles et la distance parcourue pour ajuster la vitesse
        if self.en_mouvement:
            # Si un obstacle est détecté dans la direction du mouvement, on arrête le robot et on affiche un message d'avertissement
            if self.obstacle_devant and self.avance:
                msg.linear.x = 0.0
                self.get_logger().warn('Obstacle devant — stop !')
                self.en_mouvement = False
            # Si un obstacle est détecté derrière alors qu'on recule, on arrête le robot et on affiche un message d'avertissement
            elif self.obstacle_derriere and not self.avance:
                msg.linear.x = 0.0
                self.get_logger().warn('Obstacle derrière — stop !')
                self.en_mouvement = False
            # Si la distance parcourue est inférieure à la distance cible, on continue d'avancer ou reculer à une vitesse de 0.2 m/s
            elif self.distance_parcourue() < abs(self.distance_cible) and self.distance_cible != 0.0:
                msg.linear.x = 0.2 if self.avance else -0.2
            # Sinon on s'arrête et on affiche un message d'arrivée
            else:
                msg.linear.x = 0.0
                self.en_mouvement = False
                self.get_logger().info('Arrivé !')

        # Si on est en rotation, on vérifie l'angle parcouru pour ajuster la vitesse de rotation
        if self.en_rotation:
            if abs(self.angle_parcouru()) < abs(self.rotation_cible):
                msg.angular.z = 0.5 if self.rotation_cible > 0 else -0.5
            else:
                msg.angular.z = 0.0
                self.en_rotation = False
                self.get_logger().info('Rotation terminée !')

        self.pub.publish(msg)

def main():
    # Initialisation du noeud ROS et création de l'instance du robot
    rclpy.init()
    robot = RobotSimple()

    # Attendre odom et LiDAR
    for _ in range(20):
        rclpy.spin_once(robot, timeout_sec=0.1)

    print("Le robot explore la pièce — Ctrl+C pour arrêter")

    # Boucle principale : le robot avance tant qu'il n'y a pas d'obstacle devant, sinon il tourne vers la meilleure direction
    while rclpy.ok():
        rclpy.spin_once(robot, timeout_sec=0.1)

        # Affichage des distances pour le debug
        print(f"obstacle={robot.obstacle_devant} | devant={robot.dist_devant:.2f}m | gauche={robot.dist_gauche:.2f}m | droite={robot.dist_droite:.2f}m")

        # Si un obstacle est détecté devant, on choisit la meilleure direction (gauche ou droite) et on tourne dans cette direction
        if robot.obstacle_devant:
            # Choix de la meilleure direction en fonction des distances mesurées par le LiDAR
            direction = robot.meilleure_direction()
            print(f"Obstacle ! Je tourne vers : {direction}")

            if direction == 'gauche':
                robot.tourner(50)
            else:
                robot.tourner(-50)

            # Attendre la fin de la rotation avant de continuer
            while robot.en_rotation:
                rclpy.spin_once(robot, timeout_sec=0.1)

        # Si pas d'obstacle, on avance
        else:
            robot.avancer(1.0)  # Avance de 1m

            # Attendre la fin du mouvement ou l'apparition d'un obstacle
            while robot.en_mouvement:
                rclpy.spin_once(robot, timeout_sec=0.1)
                # Condition de sortie du while
                if robot.obstacle_devant:
                    robot.en_mouvement = False

    rclpy.shutdown()

if __name__ == '__main__':
    main()
