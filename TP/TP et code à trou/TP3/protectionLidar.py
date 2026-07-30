import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import Twist
import sensor_msgs_py.point_cloud2 as pc2 # Bibliothèque standard ROS 2 pour lire les points 3D

class SafetyGate3DNode(Node):
    def __init__(self):
        super().__init__('safety_gate_3d_node')
        
        # --- CONFIGURATION DE LA BOÎTE DE SÉCURITÉ (En mètres) ---
        # Devant le robot (Axe X)
        self.x_min = 0.1
        self.x_max = 0.50  # Ta distance de sécurité demandée (1m50)
        
        # Largeur du corridor (Axe Y : gauche/droite)
        # Permet d'ignorer les obstacles sur les côtés qui ne gênent pas le passage
        self.y_min = -0.35  # 35 cm à droite
        self.y_max = 0.35   # 35 cm à gauche
        
        # Hauteur de détection (Axe Z : haut/bas)
        # Ajuste z_min pour passer JUSTE au-dessus du sol (et éviter de détecter le sol comme un obstacle !)
        self.z_min = -0.20  # Si ton LiDAR est à 30cm du sol, -0.20m évite de toucher le sol
        self.z_max = 0.50   # Ignore ce qui est trop haut (plafond, ponts)

        # Nombre de points minimum dans la boîte pour déclencher l'arrêt (évite les fausses alertes/bruit)
        self.seuil_bruit_points = 5 
        
        # --- COMMUNICATIONS ROS 2 ---
        # Remplace '/points' par le vrai nom de ton topic PointCloud2 si nécessaire (ex: /velodyne_points)
        self.sub_cloud = self.create_subscription(PointCloud2, '/points', self.cloud_callback, 10)
        self.sub_cmd_s2l = self.create_subscription(Twist, '/cmd_vel_s2l', self.cmd_callback, 10)
        
        self.pub_cmd_lane = self.create_publisher(Twist, '/cmd_vel_lane', 10)
        
        self.obstacle_detecte = False

    def cloud_callback(self, msg):
        """ Analyse le nuage de points 3D """
        points_dans_boite = 0
        obstacle_trouve = False
        
        # Lecture optimisée des coordonnées X, Y, Z du PointCloud2
        for point in pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True):
            x, y, z = point
            
            # On vérifie si le point 3D tombe dans notre boîte de sécurité
            if (self.x_min < x < self.x_max) and (self.y_min < y < self.y_max) and (self.z_min < z < self.z_max):
                points_dans_boite += 1
                
                # Dès qu'on dépasse le seuil de bruit, on valide la présence d'un obstacle
                if points_dans_boite >= self.seuil_bruit_points:
                    obstacle_trouve = True
                    break
                    
        self.obstacle_detecte = obstacle_trouve

    def cmd_callback(self, msg):
        """ Reçoit l'ordre du suiveur de ligne et applique le filtre de sécurité """
        commande_filtree = Twist()
        
        if self.obstacle_detecte:
            # Obstacle présent -> On force tout à 0 (vitesse linéaire et angulaire)
            commande_filtree.linear.x = 0.0
            commande_filtree.angular.z = 0.0
            self.get_logger().warn("⚠️ OBSTACLE 3D DÉTECTÉ ! Robot stoppé.", throttle_duration_sec=1.0)
        else:
            # Pas d'obstacle -> On laisse passer le suiveur de ligne normalement
            commande_filtree = msg
            
        self.pub_cmd_lane.publish(commande_filtree)

def main(args=None):
    rclpy.init(args=args)
    node = SafetyGate3DNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
