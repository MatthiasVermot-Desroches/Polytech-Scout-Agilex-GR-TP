#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32, Int32MultiArray, Bool
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType
import math

class RobotSimple(Node):
    def __init__(self):

        time.sleep(2.0)  # Attente pour s'assurer que tous les nœuds sont prêts (notamment la caméra)

        super().__init__('control_line_node')

        self.pub        = self.create_publisher(Twist, '/cmd_vel', 10)
        self.error_sub  = self.create_subscription(Float32, '/line_tracking/error_raw', self.error_callback, 10)
        self.route_sub  = self.create_subscription(Int32MultiArray, '/camera/zones_route', self.route_callback, 10)
        self.lost_sub   = self.create_subscription(Bool, '/line_tracking/route_perdue', self.lost_callback, 10)
        self.single_sub = self.create_subscription(Bool, '/line_tracking/ligne_unique', self.single_callback, 10)

        

        # État
        self.erreur       = 0.0
        self.last_error   = 0.0
        self.route_perdue = False
        self.ligne_unique = False
        self.zones_route  = [0, 0, 0, 0, 0, 0, 0]
        self.last_time    = self.get_clock().now()

        # Mémoire géométrique
        self.angle_accumule      = 0.0
        self.dernier_sens_virage = "DROITE"
        self.seuil_vrai_virage   = 0.43
        self.en_epingle            = False

        # Historique pour détecter les virages serrés
        self.historique_angles           = []
        self.SEUIL_MIN_RALENTISSEMENT    = math.radians(20.0)

        # PID
        self.gain_kp = 0.0025
        self.gain_kd = 0.0008

        # Secours solaire
        self.client_realsense          = self.create_client(SetParameters, '/camera/camera/set_parameters')
        self.tentative_secours_solaire = False
        self.timer_secours_commence    = None
        self.exposition_originale      = 1000
        self.exposition_actuelle       = self.exposition_originale
        self.exposition_soleil         = 50
        # Timer unique pour initialiser l'exposition après démarrage
        self.timer_init = self.create_timer(2.0, self.init_exposition)

        self.test_mode = True  # Mettre à True pour forcer les vitesses à 0
        self.timer = self.create_timer(1 if self.test_mode else 0.1, self.boucle)

        self.get_logger().info("Mode test :" + ("Activé, la boucle est ralentie" if self.test_mode else "Désactivé"))
        self.get_logger().info("Nœud suiveur de ligne prêt.")

    def init_exposition(self):
        """Appelé une seule fois 2 secondes après le démarrage."""
        if self.client_realsense.service_is_ready():
            self.changer_exposition(self.exposition_soleil)
            self.get_logger().info(f"Exposition initiale → {self.exposition_soleil}")
        else:
            self.get_logger().warn("Service caméra pas encore prêt, nouvel essai...")
            return  # le timer réessaiera dans 2s
        # Désactiver ce timer — on ne veut l'appeler qu'une seule fois
        self.timer_init.cancel()

    # ── Callbacks ──────────────────────────────────────────────────────────────
    def error_callback(self, msg):   self.erreur = msg.data
    def lost_callback(self, msg):    self.route_perdue = msg.data
    def single_callback(self, msg):  self.ligne_unique = msg.data
    def route_callback(self, msg):
        if len(msg.data) == 7:
            self.zones_route = list(msg.data)

    # ── Exposition caméra ───────────────────────────────────────────────────────
    def changer_exposition(self, valeur):
        if self.exposition_actuelle == valeur:
            return
        if not self.client_realsense.service_is_ready():
            self.get_logger().warn("Service caméra non disponible")
            return

        req   = SetParameters.Request()
        param = Parameter()
        param.name                    = 'rgb_camera.exposure'
        param.value.type              = ParameterType.PARAMETER_INTEGER
        param.value.integer_value     = int(valeur)
        req.parameters.append(param)

        self.client_realsense.call_async(req)
        self.exposition_actuelle = valeur
        self.get_logger().info(f"Exposition caméra → {valeur}")

    # ── Boucle principale ───────────────────────────────────────────────────────
    def boucle(self):

        if self.erreur is None or self.zones_route is None:
            self.get_logger().warn("Données non encore reçues, attente...")
            return

        msg = Twist()

        # 1. dt
        now  = self.get_clock().now()
        dt   = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0.0:
            dt = 0.1

        # 2. Extraction zones
        l1_ok  = self.zones_route[0]
        l2_ok  = self.zones_route[1]
        l3_ok  = self.zones_route[4]
        l3g_ok = self.zones_route[5]
        l3d_ok = self.zones_route[6]

        # 3. CALCULER D'ABORD LE CONTRÔLE PID (nécessaire pour déterminer le mode)
        # ✅ Calcul immédiat du PID qui sera utilisé pour tous les modes
        P = self.gain_kp * self.erreur
        D = self.gain_kd * (self.erreur - self.last_error) / dt
        angular_z_pid = -(P + D)

        print(angular_z_pid)
        
        # Historique pour détecter les manoeuvres (basée sur le contrôle réel)
        self.historique_angles.append(abs(angular_z_pid * dt))
        if len(self.historique_angles) > 10:
            self.historique_angles.pop(0)
        angle_manoeuvre_1s = sum(self.historique_angles)

        # 4. Détermination du mode (maintenant basé sur les vraies valeurs)
        mode_actuel = "NOMINAL"  # valeur par défaut

        # ÉTAT A : MODE DÉTRESSE (Piste complètement perdue)
        if self.route_perdue:
            mode_actuel = "DETRESSE"

        # ÉTAT B : MODE ÉPINGLE / VIRAGE SERRÉ
        elif angle_manoeuvre_1s > self.SEUIL_MIN_RALENTISSEMENT or (l1_ok and not l3_ok) or self.en_epingle:
            mode_actuel = "EPINGLE"

        # ÉTAT C : MODE BIFURCATION / INTERSECTION
        elif l1_ok and (l3g_ok and l3d_ok):
            mode_actuel = "BIFURCATION"

        # ÉTAT D : MODE NOMINAL (Ligne droite ou courbe légère)
        else:
            mode_actuel = "NOMINAL"

        # 5. Comportement selon le mode
        if mode_actuel == "DETRESSE":
            msg.linear.x  = 0.10
            msg.angular.z = 0.60 if self.dernier_sens_virage == "GAUCHE" else -0.60
            self.get_logger().warn(
                f"[DETRESSE] Pivot → {self.dernier_sens_virage}",
                throttle_duration_sec=1.0)

        elif mode_actuel == "EPINGLE":
            print("Mode EPINGLE")

            self.en_epingle = True  # On reste en mode épingle tant que les conditions sont réunies

            msg.angular.z = angular_z_pid

            if l1_ok and not l3_ok:
                # tant qu'on n'a pas de ligne 3 devant et qu'on detect une ligne 1, on est en épingle 
                # on tourne lentement

                V_MAX = 0.20
                V_MIN = 0.10
                MAX_ERR = 100.0
                facteur  = min(abs(self.erreur), MAX_ERR) / MAX_ERR
                msg.linear.x = V_MAX - facteur * (V_MAX - V_MIN) * 0.5

                # Intersection droite — on passe tout droit
                if abs(self.erreur) < 15.0 and (self.zones_route[2] or self.zones_route[3]):
                    msg.linear.x = V_MAX

                msg.linear.x = min(1/(abs(P + D + 0.05)) , 0.25)

            elif not l1_ok and not l3_ok:
                # si on ne voit pas de ligne 1, on a surement loupé le virage et on doit se repositionner
                msg.linear.x = 0.10
                if self.dernier_sens_virage == "GAUCHE":
                    msg.angular.z = 0.40
                else:
                    msg.angular.z = - 0.40

            elif l1_ok and l3_ok:
                # si on voit la ligne 1 et la ligne 3, on est sorti de l'épingle
                self.en_epingle = False

            elif not l1_ok and l3_ok:

                msg.linear.x = 0.0

                if self.dernier_sens_virage == "GAUCHE":
                    msg.angular.z = 0.40
                else:
                    msg.angular.z = - 0.40


        elif mode_actuel == "BIFURCATION":
            msg.linear.x  = 0.30
            msg.angular.z = angular_z_pid
            biais = 0.15 if self.dernier_sens_virage == "GAUCHE" else -0.15
            msg.angular.z += biais
            self.get_logger().info(
                f"[BIFURCATION] → {self.dernier_sens_virage}",
                throttle_duration_sec=2.0)

        else:  # NOMINAL
            print("Mode NOMINAL")
            msg.angular.z = angular_z_pid

            V_MAX = 0.20
            V_MIN = 0.10
            MAX_ERR = 100.0
            facteur  = min(abs(self.erreur), MAX_ERR) / MAX_ERR
            msg.linear.x = V_MAX - facteur * (V_MAX - V_MIN)

            # Intersection droite — on passe tout droit
            if abs(self.erreur) < 15.0 and (self.zones_route[2] or self.zones_route[3]):
                msg.linear.x = V_MAX
        
        # 6. Sécurité ligne unique
        if self.ligne_unique and mode_actuel != "DETRESSE":
            msg.linear.x = min(msg.linear.x, 0.12)
            self.get_logger().info(
                "Une seule ligne — vitesse bridée",
                throttle_duration_sec=1.0)

        # 7. Mémoire géométrique
        self.last_error = self.erreur

        # Accumulation pour détecter le sens du virage
        self.angle_accumule += msg.angular.z * dt
        if abs(msg.angular.z) < 0.1:
            self.angle_accumule *= 0.85

        if self.angle_accumule > self.seuil_vrai_virage:
            if self.dernier_sens_virage != "GAUCHE":
                self.dernier_sens_virage = "GAUCHE"
                self.get_logger().info("Mémorisation : virage GAUCHE")
            self.angle_accumule = 0.0
        elif self.angle_accumule < -self.seuil_vrai_virage:
            if self.dernier_sens_virage != "DROITE":
                self.dernier_sens_virage = "DROITE"
                self.get_logger().info("Mémorisation : virage DROITE")
            self.angle_accumule = 0.0
        
        # print(msg.linear.x, msg.angular.z)

        if self.test_mode:
            # POUR QUE LE ROBOT NE BOUGE PAS POUR LES TESTS
            # print("Vitesse linéaire et angulaire forcées à 0 pour les tests")
            msg.linear.x = 0.0
            msg.angular.z = 0.0


        self.pub.publish(msg)

def main():
    rclpy.init()
    robot = RobotSimple()
    print("Suiveur de ligne — Ctrl+C pour arrêter")
    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        pass
    finally:
        stop = Twist()
        robot.pub.publish(stop)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
