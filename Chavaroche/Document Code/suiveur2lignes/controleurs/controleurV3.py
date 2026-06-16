#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32, Int32MultiArray, Bool
import math

class RobotSimple(Node):
    def __init__(self):
        super().__init__('control_line_node')
        
        # Publishers et Subscribers
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.error_sub = self.create_subscription(Float32, '/line_tracking/error_raw', self.error_callback, 10)
        self.route_sub = self.create_subscription(Int32MultiArray, '/camera/zones_route', self.route_callback, 10)
        self.lost_sub = self.create_subscription(Bool, '/line_tracking/route_perdue', self.lost_callback, 10)

        # Timer (10Hz)
        self.timer = self.create_timer(0.1, self.boucle)

        # Variables d'état classiques
        self.error = 0.0
        self.last_error = 0.0
        self.route_perdue = False
        self.zones_route = [0, 0, 0, 0, 0, 0, 0] 

        # --- AJOUT : HISTORIQUE ET MÉMOIRE GÉOMÉTRIQUE ---
        self.angle_accumule = 0.0          # En radians. Positif = Gauche, Négatif = Droite
        self.dernier_sens_virage = "DROITE" # Stocke "GAUCHE" ou "DROITE" pour les intersections
        self.seuil_vrai_virage = 0.43      # Environ 25 degrés. En dessous, c'est juste de la correction


        # Configuration PID
        self.gain_kp = 0.0025  
        self.gain_kd = 0.0008  
        self.last_time = self.get_clock().now()

        # --- MÉMOIRE DE VIRAGE GLISSANTE (1 seconde = 10 échantillons à 10Hz) ---
        self.historique_angles = []
        self.SEUIL_MIN_RALENTISSEMENT = math.radians(20.0) # 0.35 rad
        self.SEUIL_MAX_RALENTISSEMENT = math.radians(35.0) # 0.61 rad
        
        self.get_logger().info("Nœud Agilex avec mémoire de trajectoire prêt.")

    def error_callback(self, msg):
        self.error = msg.data

    def lost_callback(self, msg):
        self.route_perdue = msg.data

    def route_callback(self, msg):
        if len(msg.data) == 7:
            self.zones_route = msg.data

    def boucle(self):
        msg = Twist()

        # 1. Calcul du temps (dt)
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0.0: dt = 0.1

        # 2. CAS DE DETRESSE : RECHERCHE INTELLIGENTE DU CHEMIN PERDU
        if self.route_perdue:
            msg.linear.x = 0.0
            # On cherche dans la direction du dernier virage enregistré pour ne pas faire demi-tour vers l'arrière
            if self.dernier_sens_virage == "GAUCHE":
                msg.angular.z = 0.35  # Tourne à gauche
            else:
                msg.angular.z = -0.35 # Tourne à droite
                
            self.pub.publish(msg)
            self.get_logger().warn(f"Piste perdue. Recherche orientée à {self.dernier_sens_virage}...")
            return 


        # 3. CALCUL DU PID (Cas nominal)
        delta_error = self.error - self.last_error
        self.last_error = self.error

        P_Correcteur = self.gain_kp * self.error 
        D_Correcteur = self.gain_kd * delta_error / dt
        Correction_totale = P_Correcteur + D_Correcteur

        # Application de la vitesse angulaire de régulation
        msg.angular.z = - Correction_totale

        # --- 4. GESTION DE L'HISTORIQUE DE L'ANGLE DE MANŒUVRE ---
        variation_angle = abs(msg.angular.z * dt)
        self.historique_angles.append(variation_angle)
        
        # On garde uniquement les 10 derniers échantillons (les 10 dernières boucles = 1 seconde)
        if len(self.historique_angles) > 10:
            self.historique_angles.pop(0)
            
        # Calcul de l'angle total accumulé sur cette dernière seconde
        angle_manoeuvre_1s = sum(self.historique_angles)


        # --- 4.5. ANCIEN BLOC MÉMOIRE (Pour la direction générale du circuit) ---
        # On garde ton intégration à long terme pour savoir si le circuit est globalement à Droite/Gauche
        self.angle_accumule += msg.angular.z * dt
        if abs(msg.angular.z) < 0.1:
            self.angle_accumule *= 0.85 

        if self.angle_accumule > self.seuil_vrai_virage:
            if self.dernier_sens_virage != "GAUCHE":
                self.dernier_sens_virage = "GAUCHE"
            self.angle_accumule = 0.0
        elif self.angle_accumule < -self.seuil_vrai_virage:
            if self.dernier_sens_virage != "DROITE":
                self.dernier_sens_virage = "DROITE"
            self.angle_accumule = 0.0

        # 5. DÉTERMINATION DE LA VITESSE LINÉAIRE ADAPTATIVE
        V_MAX = 0.4       
        V_MIN = 0.15      
        MAX_ERR_CONFIANCE = 150.0
        facteur_erreur = min(abs(self.error), MAX_ERR_CONFIANCE) / MAX_ERR_CONFIANCE
        vitesse_cible = V_MAX - (facteur_erreur * (V_MAX - V_MIN))

        # Si l'angle tourné sur la dernière seconde dépasse 20°
        if angle_manoeuvre_1s > self.SEUIL_MIN_RALENTISSEMENT:
            # Calcul du ratio entre 0.0 (à 20°) et 1.0 (à 35° et plus)
            plage = self.SEUIL_MAX_RALENTISSEMENT - self.SEUIL_MIN_RALENTISSEMENT
            ratio_virage = (angle_manoeuvre_1s - self.SEUIL_MIN_RALENTISSEMENT) / plage
            ratio_virage = min(1.0, ratio_virage) # Hardcap du ratio à 1.0 pour éviter l'arrêt complet
            
            # Vitesse plancher de sécurité absolue pour ne jamais caler au milieu du virage
            V_PLANCHER_EPINGLE = 0.10 
            
            # Interpolation linéaire : plus on tourne, plus on descend vers V_PLANCHER_EPINGLE
            vitesse_cible = vitesse_cible - (ratio_virage * (vitesse_cible - V_PLANCHER_EPINGLE))
            
            angle_degres = math.degrees(angle_manoeuvre_1s)
            self.get_logger().info(f"Épingle en cours ({angle_degres:.1f}° sur 1s). Vitesse réduite à : {vitesse_cible:.2f} m/s", throttle_duration_sec=0.4)

        # 6. APPLICATION DE LA STRATÉGIE AUX INTERSECTIONS / BIFURCATIONS
        # Index de ta grille : L1=0, L2=1, L2G=2, L2D=3, L3=4, L3G=5, L3D=6
        l1_ok = self.zones_route[0]
        l3_ok = self.zones_route[4]
        l3g_ok = self.zones_route[5]
        l3d_ok = self.zones_route[6]

        # Cas d'une bifurcation en "Y" ou d'un embranchement lointain détecté par L3
        if l1_ok and (l3g_ok and l3d_ok):
            # La route se sépare au loin mais on est encore bien centré sur notre ligne actuelle.
            # Pour ne pas revenir en arrière ou hésiter, on force le robot à se pré-positionner
            # du côté du sens général du circuit en appliquant un léger biais d'anticipation.
            if self.dernier_sens_virage == "GAUCHE":
                msg.angular.z += 0.1  # Incite doucement à pencher à gauche
            else:
                msg.angular.z -= 0.1  # Incite doucement à pencher à droite
                
            msg.linear.x = 0.4 # Vitesse modérée pré-intersection
            self.get_logger().info(f"Bifurcation en vue (L3). Choix automatique : {self.dernier_sens_virage}", throttle_duration_sec=2.0)

        # Cas d'une intersection latérale classique sans virage sous les roues
        elif l1_ok and abs(self.error) < 20.0 and (self.zones_route[2] or self.zones_route[3]):
            msg.linear.x = V_MAX # On ignore et on trace tout droit
            
        # Cas nominal classique
        else:
            msg.linear.x = vitesse_cible

        # Envoi de la commande finale
        self.pub.publish(msg)

def main():
    rclpy.init()
    robot = RobotSimple()
    print("Le robot suit le chemin intelligent — Ctrl+C pour arrêter")

    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        print("Arrêt demandé par l'utilisateur.")
    finally:
        stop_msg = Twist()
        robot.pub.publish(stop_msg)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
