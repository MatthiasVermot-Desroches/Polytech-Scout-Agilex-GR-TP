import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from vision_msgs.msg import Detection2DArray  # Conservé selon ton import
from enum import Enum

# =========================================================
# Robot states
# =========================================================
class RobotState(Enum):
    FOLLOW_LANE      = 0
    STOP_RED_LIGHT   = 1
    STOP_SIGN        = 2
    WAIT_PEDESTRIAN  = 3
    TURN             = 4

# =========================================================
# Behavior Manager Node
# =========================================================
class BehaviorManager(Node):

    def __init__(self):
        super().__init__('behavior_manager')

        # Variables d'état
        self.state = RobotState.FOLLOW_LANE
        self.coeff_vitesse = 1.0
        self.distance_Z = 10.0  # Initialisé grand par sécurité
        self.previous_state = None
        self.pieton_on_psg = False
        self.dist_pieton = None

        # Gestion du temps pour le STOP (sans bloquer ROS)
        self.stop_start_time = None

        # Dernières commandes reçues du suivi de ligne
        self.last_lane_cmd = Twist()

        # Subscribers
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel_lane', self.cmd_callback, 10
        )

        self.detected_sign_sub = self.create_subscription(
            Detection2DArray, '/detection/metadata', self.detection_callback, 10
        )

        # Publisher
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.turn_pub = self.create_publisher(Bool, '/turn_sign', 10)

        # Main timer (20 Hz)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info("Behavior manager started et optimisé.")

    def detection_callback(self, msg):
        # Vérification de la présence de détections
        if len(msg.detections) == 0:
            if self.state == RobotState.WAIT_PEDESTRIAN:
                self.dist_pieton = None
                self.pieton_on_psg = False
                self.get_logger().info("Le piéton est parti -> Reprise de la ligne.")
                self.state = RobotState.FOLLOW_LANE
            else:
                self.get_logger().info("Pas de détection")
                self.state = RobotState.FOLLOW_LANE

            return

        detection_prioritaire = None
        distance_min = float('inf')

        closest_pieton_Z = None

        for det in msg.detections:
            if len(det.results) == 0:
                continue
            if det.results[0].hypothesis.score < 0.2:
                continue
            z_actuel = 10.0
            elements = det.id.split(';')
            for element in elements:
                if element.startswith('Z:'):
                    try:
                        z_actuel = float(element.split(':')[1])
                    except ValueError:
                        pass
                    break
            if z_actuel < distance_min:
                distance_min = z_actuel
                detection_prioritaire = det
                self.distance_Z = z_actuel
            if det.results[0].hypothesis.class_id == "Présence piéton" : #Nom temporaire, demander nom choisi
                if closest_pieton_Z is None or z_actuel < closest_pieton_Z:
                    self.pieton_on_psg = True
                    closest_pieton_Z = z_actuel

        self.dist_pieton = closest_pieton_Z

        if detection_prioritaire is not None:
            self.score = detection_prioritaire.results[0].hypothesis.score
            self.detected_sign = detection_prioritaire.results[0].hypothesis.class_id
        
            # Filtre de confiance
            if self.score < 0.2:
                self.get_logger().info("Confiance trop basse, détection annulée")
                return

            # Machine à état : Transition basées sur les détections
            match self.detected_sign:
                case "stop":
                    if self.state != RobotState.STOP_SIGN and self.previous_state != RobotState.STOP_SIGN:
                        self.get_logger().warn(f"STOP détecté à {self.distance_Z:.2f}m -> Approche en cours")
                        self.state = RobotState.STOP_SIGN
                        self.stop_start_time = None

                case "feu_rouge" | "feu_orange":
                    if self.state != RobotState.STOP_RED_LIGHT:
                        self.get_logger().warn("Feu Rouge/Orange détecté -> Ralentissement/Arrêt")
                        self.state = RobotState.STOP_RED_LIGHT

                case "feu_vert":
                    if self.state == RobotState.STOP_RED_LIGHT:
                        self.get_logger().info("Feu vert ! Reprise de la ligne.")
                        self.state = RobotState.FOLLOW_LANE
                    else :
                        self.get_logger().info("Feu vert, pas de changement")

                case "pieton":
                    if self.state != RobotState.WAIT_PEDESTRIAN:
                        self.get_logger().warn("Piéton détecté !")
                        self.state = RobotState.WAIT_PEDESTRIAN

                case "Présence piéton": #Nom temporaire, demander nom choisi
                    if self.state != RobotState.WAIT_PEDESTRIAN:
                        self.get_logger().warn("Piéton détecté !")
                        self.state = RobotState.WAIT_PEDESTRIAN


                case "tournez":
                    self.get_logger().info("Tournez WIP")
                    if self.state != RobotState.TURN:
                        self.state = RobotState.TURN


                case "cedez":
                    self.get_logger().info("Cédez le passage WIP")

                case _:
                    # Si on ne voit plus rien ou une classe inconnue, on ne force pas le retour
                    # au suivi de ligne immédiatement pour éviter les clignotements de détection.
                    self.get_logger().info("Classe de panneau inconnue ou aucun panneau détecté")
                    pass

    def cmd_callback(self, msg):
        self.last_lane_cmd = msg

    def control_loop(self):
        cmd_out = Twist()

        # Utilisé pour le STOP et le FEU ROUGE
        if self.distance_Z > 5.0:
            self.coeff_vitesse = 1.0
        elif self.distance_Z > 3.0:
            self.coeff_vitesse = 0.6
        elif self.distance_Z > 1.2:
            self.coeff_vitesse = 0.3
        else:
            self.coeff_vitesse = 0.0

        # -------------------------------------------------
        # Application des comportements selon l'état
        # -------------------------------------------------
        if self.state == RobotState.FOLLOW_LANE:
            cmd_out = self.last_lane_cmd
            self.previous_state = RobotState.FOLLOW_LANE

        elif self.state == RobotState.STOP_RED_LIGHT:
            # On suit la ligne mais en appliquant le coefficient de freinage
            cmd_out.linear.x = self.coeff_vitesse * self.last_lane_cmd.linear.x
            cmd_out.angular.z = self.coeff_vitesse * self.last_lane_cmd.angular.z
            self.previous_state = RobotState.STOP_RED_LIGHT

        elif self.state == RobotState.STOP_SIGN:
            if self.coeff_vitesse > 0.0:
                # Phase d'approche : on ralentit en suivant la ligne
                cmd_out.linear.x = self.coeff_vitesse * self.last_lane_cmd.linear.x
                cmd_out.angular.z = self.coeff_vitesse * self.last_lane_cmd.angular.z
            else:
                # Phase d'arrêt complet (coeff_vitesse == 0.0, donc distance_Z <= 1.2m)
                cmd_out.linear.x = 0.0
                cmd_out.angular.z = 0.0

                # Gestion du chrono des 2 secondes d'arrêt au Stop
                current_time = self.get_clock().now()
                if self.stop_start_time is None:
                    self.stop_start_time = current_time
                    self.get_logger().info("Marquage du STOP (Durée : 2s)...")
                else:
                    elapsed_time = (current_time - self.stop_start_time).nanoseconds / 1e9
                    if elapsed_time >= 2.0:
                        self.get_logger().info("STOP effectué -> Reprise de la route.")
                        self.state = RobotState.FOLLOW_LANE
                        self.distance_Z = 10.0 # Reset virtuel de la distance
                        self.previous_state = RobotState.STOP_SIGN

        elif self.state == RobotState.WAIT_PEDESTRIAN:
            if self.dist_pieton is not None:
                if self.dist_pieton > 3 :
                    cmd_out.linear.x = 0.6*self.last_lane_cmd.linear.x
                    cmd_out.angular.z = 0.6*self.last_lane_cmd.angular.z
                elif self.dist_pieton > 1.5 : 
                    cmd_out.linear.x = 0.3*self.last_lane_cmd.linear.x
                    cmd_out.angular.z = 0.3*self.last_lane_cmd.angular.z
                else :
                # Arrêt d'urgence immédiat pour le piéton
                    cmd_out.linear.x = 0.0
                    cmd_out.angular.z = 0.0
            else :
                cmd_out = self.last_lane_cmd
            # Note : Tu pourrais ajouter une logique pour repasser en FOLLOW_LANE 
            # si l'IA ne détecte plus de piéton pendant X secondes.
            self.previous_state = RobotState.WAIT_PEDESTRIAN

        elif self.state == RobotState.TURN:
            self.turn_pub.publish(True)
            cmd_out = self.last_lane_cmd
        else :
            self.turn_pub.publish(False)
            cmd_out = self.last_lane_cmd

        # Publication de la commande finale
        self.cmd_pub.publish(cmd_out)

def main(args=None):
    rclpy.init(args=args)
    node = BehaviorManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()