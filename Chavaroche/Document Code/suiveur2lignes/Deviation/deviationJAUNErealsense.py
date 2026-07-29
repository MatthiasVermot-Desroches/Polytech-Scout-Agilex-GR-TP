#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Header, Float32, Float32MultiArray, Int32MultiArray
from cv_bridge import CvBridge, CvBridgeError
from collections import deque
import cv2
import numpy as np
import math
from sensor_msgs.msg import Imu

try:
    from robot_msgs.msg import LineData
    ROBOT_MSGS_AVAILABLE = True
except ImportError:
    ROBOT_MSGS_AVAILABLE = False


class VisionLineNode(Node):
    def __init__(self):
        super().__init__('vision_line_node')
        
        self.bridge = CvBridge()
        
        # Abonnement au flux RGB
        self.image_sub = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw', 
            self.image_callback,
            10
        )
        
        # Abonnement au topic du panneau de virage
        self.turn_sub = self.create_subscription(
            Bool,
            '/turn_sign',
            self.turn_sign_callback,
            10
        )

        self.turn_pub = self.create_publisher(Bool, '/turn_sign', 10)
        
        # Publishers standards
        self.error_pub = self.create_publisher(Float32, '/line_tracking/error_raw', 10)
        self.masse_pub = self.create_publisher(Float32MultiArray, '/camera/zones_masses', 10)
        self.route_pub = self.create_publisher(Int32MultiArray, '/camera/zones_route', 10)
        self.lost_pub = self.create_publisher(Bool, '/line_tracking/route_perdue', 10)
        self.single_line_pub = self.create_publisher(Bool, '/line_tracking/ligne_unique', 10)
        self.debug_img_pub = self.create_publisher(Image, '/camera/debug_image', 10)
        self.imu_sub = self.create_subscription(Imu, '/imu/data_raw', self.imu_callback, 10)


        self.vitesse_z_gyro = 0.0
        self.angle_parcouru_virage = 0.0
        self.last_time_imu = None
                
        self.derniere_ligne_perdue = "AUCUNE"

        self.nb_frames_accumulation = 5  # Nombre d'images en mémoire
        self.seuil_persistance = 3       # Un pixel doit être là au moins 3 fois sur 5
        self.historique_masques = deque(maxlen=self.nb_frames_accumulation)
        
        self.largeurs_memoire = {
            'L1': 540,  # Palier bas
            'L2': 450,  # Palier milieu
            'L3': 310   # Palier haut
        }

        # Variables d'état pour la gestion du panneau
        # États possibles : "VEILLE", "ATTENTE_VIRAGE", "FORCAGE_DROITE"
        self.statut_virage = "VEILLE"
        self.frames_confirmation_sortie = 0
    
    def imu_callback(self, msg):
        current_time = self.get_clock().now()
        self.vitesse_z_gyro = msg.angular_velocity.z # en rad/s
        
        # Si on est en train de tourner, on intègre la vitesse pour calculer l'angle
        if self.statut_virage == "FORCAGE_DROITE":
            if self.last_time_imu is not None:
                # Calcul du dt (intervalle de temps en secondes)
                dt = (current_time - self.last_time_imu).nanoseconds / 1e9
                # Intégration : Angle = Vitesse * Temps
                # On prend la valeur absolue car on veut mesurer l'amplitude de la rotation
                self.angle_parcouru_virage += abs(self.vitesse_z_gyro * dt)
                
        self.last_time_imu = current_time

    def calcul_delta_angle(self, angle1, angle2):
        # Calcule l'écart minimal entre deux angles en radians [-pi, pi]
        diff = angle1 - angle2
        return abs((diff + math.pi) % (2 * math.pi) - math.pi)

    # Callback pour intercepter le panneau
    def turn_sign_callback(self, msg):
        if msg.data and self.statut_virage == "VEILLE":
            self.statut_virage = "ATTENTE_VIRAGE"
            self.get_logger().info("🛑 Panneau détecté ! FSM en attente de l'amorce du virage serré.")

    def trouver_centres_ligne(self, masque_ligne, seuil_bruit=5, ecart_max=30, step=0):
        indices_blancs = np.where(masque_ligne == 255)[0] + step
        lignes_x = []

        if len(indices_blancs) == 0:
            return lignes_x

        groupes = []
        groupe_courant = [indices_blancs[0]]

        for x in indices_blancs[1:]:
            if x - groupe_courant[-1] > ecart_max:
                groupes.append(groupe_courant)
                groupe_courant = [x]
            else:
                groupe_courant.append(x)
        groupes.append(groupe_courant)

        for g in groupes:
            x_debut = g[0]
            x_fin = g[-1]
            largeur_paquet = x_fin - x_debut

            if largeur_paquet < 3:
                continue 

            if len(g) >= seuil_bruit:
                lignes_x.append(int(np.mean(g)))
                
        return lignes_x

    def filtrer_paire_par_largeur(self, liste_lignes, nom_palier, tolerance=0.35):
        nb_lignes = len(liste_lignes)
        if nb_lignes < 2:
            return None, None, False

        largeur_cible = self.largeurs_memoire[nom_palier]
        largeur_min = largeur_cible * (1.0 - tolerance)
        largeur_max = largeur_cible * (1.0 + tolerance)

        for i in range(nb_lignes):
            for j in range(i + 1, nb_lignes):
                cand_droite = liste_lignes[i]
                cand_gauche = liste_lignes[j]
                largeur_calculee = cand_droite - cand_gauche

                if largeur_min <= largeur_calculee <= largeur_max:
                    self.largeurs_memoire[nom_palier] = int(0.9 * largeur_cible + 0.1 * largeur_calculee)
                    return cand_droite, cand_gauche, True

        return None, None, False
    
    def image_callback(self, msg):
        POIDS_L1 = 0.3
        POIDS_L2 = 0.7

        erreur_calculer = 0.0
        err_L1 = 0.0
        err_L2 = 0.0

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f"Erreur de conversion CvBridge: {e}")
            return

        height, width, _ = cv_image.shape  
        CENTRE_IMAGE = width / 2  

        Y_L3 = 170 
        Y_L2 = 320 
        Y_L1 = 450 

        debug_frame = cv_image.copy()

        lower_yellow = np.array([18,  35,  70])
        upper_yellow = np.array([32, 255, 255])

        hsv  = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        self.historique_masques.append(mask.copy())
        ratio_seuil = self.seuil_persistance / self.nb_frames_accumulation
        seuil_actuel = max(1, int(len(self.historique_masques) * ratio_seuil))

        bloc_images = np.array(self.historique_masques)
        accumulation = np.sum(bloc_images == 255, axis=0)
        mask = np.where(accumulation >= seuil_actuel, 255, 0).astype(np.uint8)

        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_rgb[:,:,0] = 0   
        mask_rgb[:,:,2] = 0   
        debug_frame = cv2.addWeighted(debug_frame, 1.0, mask_rgb, 0.5, 0)

        step = width - 1
        X_G, X_C, X_D = (0, 1), (1, step), (step, width)

        masses = {}
        route_detectee = {}

        partitions = {
            'L3G': (Y_L3, X_G), 'L3': (Y_L3, X_C), 'L3D': (Y_L3, X_D),
            'L2G': (Y_L2, X_G), 'L2': (Y_L2, X_C), 'L2D': (Y_L2, X_D),
            'L1':  (Y_L1, X_C)  
        }

        segment_L1 = mask[Y_L1, X_C[0]:X_C[1]]
        segment_L2 = mask[Y_L2, X_C[0]:X_C[1]]
        segment_L3 = mask[Y_L3, X_C[0]:X_C[1]]

        SEUIL_PRESENCE = 30  

        for nom, (y, (x_start, x_end)) in partitions.items():
            segment = mask[y, x_start:x_end].copy()
            masse = int(np.sum(segment == 255))
            masses[nom] = float(masse)
            route_detectee[nom] = 1 if masse > SEUIL_PRESENCE else 0

            couleur = (0, 255, 0) if route_detectee[nom] == 1 else (0, 0, 255)
            cv2.line(debug_frame, (x_start, y), (x_end, y), couleur, 2)

        # 1. Extraction des centres et tris
        lignes_x_L1 = self.trouver_centres_ligne(segment_L1, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L2 = self.trouver_centres_ligne(segment_L2, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L3 = self.trouver_centres_ligne(segment_L3, seuil_bruit=5, ecart_max=30, step=X_C[0])

        lignes_L1_droite = sorted(lignes_x_L1, reverse=True)
        lignes_L2_droite = sorted(lignes_x_L2, reverse=True)
        lignes_L3_droite = sorted(lignes_x_L3, reverse=True)

        droite_L1, gauche_L1, route_L1_complete = self.filtrer_paire_par_largeur(lignes_L1_droite, 'L1')
        droite_L2, gauche_L2, route_L2_complete = self.filtrer_paire_par_largeur(lignes_L2_droite, 'L2')
        droite_L3, gauche_L3, route_L3_complete = self.filtrer_paire_par_largeur(lignes_L3_droite, 'L3')

        # 🔄 REPETITION 1 CORRIGÉE : On regroupe la configuration du dessin de debug dans une liste
        # Structure : (liste_des_lignes, route_complete, x_droite, x_gauche, position_Y, couleur_si_complet, couleur_si_incomplet)
        config_affichage = [
            (lignes_L1_droite, route_L1_complete, droite_L1, gauche_L1, Y_L1, (120, 255, 255), (0, 100, 100)),
            (lignes_L2_droite, route_L2_complete, droite_L2, gauche_L2, Y_L2, (255, 255, 130), (100, 100, 0)),
            (lignes_L3_droite, route_L3_complete, droite_L3, gauche_L3, Y_L3, (255, 130, 255), (100, 0, 100))
        ]

        # Une seule double boucle trace l'intégralité des cercles pour les 3 horizons
        for lignes, complete, d, g, y_val, col_complete, col_incomplete in config_affichage:
            for x in lignes:
                if complete and (x == d or x == g):
                    cv2.circle(debug_frame, (int(x), int(y_val)), 9, col_complete, -1)
                else:
                    cv2.circle(debug_frame, (int(x), int(y_val)), 4, col_incomplete, -1)

        # Publication ROS 2
        ordre_fixe = ['L1', 'L2', 'L2G', 'L2D', 'L3', 'L3G', 'L3D']
        self.masse_pub.publish(Float32MultiArray(data=[masses[z] for z in ordre_fixe]))
        self.route_pub.publish(Int32MultiArray(data=[route_detectee[z] for z in ordre_fixe]))

        # =====================================================================
        # 🔄 LOGIQUE DE VOTE NETTOYÉE
        # =====================================================================
        
        # Détermination de la visibilité (on remplace directement nb_lignes_LX par len())
        l1_droite_visible = route_L1_complete or (len(lignes_L1_droite) == 1 and lignes_L1_droite[0] > CENTRE_IMAGE)
        l2_droite_visible = route_L2_complete or (len(lignes_L2_droite) == 1 and lignes_L2_droite[0] > CENTRE_IMAGE)
        l3_droite_visible = route_L3_complete or (len(lignes_L3_droite) == 1 and lignes_L3_droite[0] > CENTRE_IMAGE)

        # 🔄 REPETITION 2 CORRIGÉE : En Python, True vaut 1 et False vaut 0. 
        nb_niveaux_droite = sum([l1_droite_visible, l2_droite_visible, l3_droite_visible])

        deux_lignes_visibles = (route_L1_complete or route_L2_complete or route_L3_complete)
        route_vitale_visible = (deux_lignes_visibles or len(lignes_L1_droite) == 1 or len(lignes_L2_droite) == 1 or len(lignes_L3_droite) == 1)
        
        self.lost_pub.publish(Bool(data=not route_vitale_visible))

        # OPTIMISATION SÉCURITÉ : Si on est en train de forcer le virage, on ignore le "route perdue" 
        # car le robot tourne sur place très vite et peut perdre momentanément le visuel complet.
        if not route_vitale_visible:
            if self.statut_virage == "FORCAGE_DROITE":
                erreur_calculer = 380.0  # Assure la continuité du pivot à droite toute
                msg_error = Float32(data=erreur_calculer)
                self.error_pub.publish(msg_error)
                
                cv2.putText(debug_frame, "FSM: PIVOT AVEUGLE SÉCURISÉ", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.publier_image_debug(debug_frame)
                return
            else:
                self.error_pub.publish(Float32(data=0.0))
                self.single_line_pub.publish(Bool(data=False))
                self.publier_image_debug(debug_frame)
                return

        self.single_line_pub.publish(Bool(data=(not route_L1_complete and len(lignes_L1_droite) == 1)))

        # ──── ARBRE DE DÉCISION DU SUIVEUR NOMINAL ────
        if route_L1_complete and route_L2_complete:
            centre_L1 = (droite_L1 + gauche_L1) // 2
            centre_L2 = (droite_L2 + gauche_L2) // 2
            err_L1 = float(centre_L1 - CENTRE_IMAGE)
            err_L2 = float(centre_L2 - CENTRE_IMAGE)
            erreur_calculer = (POIDS_L1 * err_L1) + (POIDS_L2 * err_L2)
            cv2.line(debug_frame, (int(centre_L1), int(Y_L1)), (int(centre_L2), int(Y_L2)), (255, 255, 255), 3)
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 8, (255, 0, 0), -1)
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 8, (255, 0, 0), -1)

        elif route_L1_complete:
            centre_L1 = (droite_L1 + gauche_L1) // 2
            erreur_calculer = float(centre_L1 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 8, (255, 0, 0), -1)

        elif route_L2_complete:
            centre_L2 = (droite_L2 + gauche_L2) // 2
            erreur_calculer = float(centre_L2 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 8, (255, 0, 0), -1)

        elif route_L3_complete:
            centre_L3 = (droite_L3 + gauche_L3) // 2
            erreur_calculer = float(centre_L3 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L3), int(Y_L3)), 8, (255, 0, 0), -1)

        else:
            if len(lignes_L1_droite) == 1:
                unique_x = lignes_L1_droite[0]
                demi_largeur = self.largeurs_memoire['L1'] / 2
                if unique_x > CENTRE_IMAGE:
                    self.derniere_ligne_perdue = "GAUCHE"
                    erreur_calculer = float((unique_x - demi_largeur) - CENTRE_IMAGE)
                else:
                    self.derniere_ligne_perdue = "DROITE"
                    erreur_calculer = float((unique_x + demi_largeur) - CENTRE_IMAGE)

            elif len(lignes_L2_droite) == 1:
                unique_x = lignes_L2_droite[0]
                demi_largeur = self.largeurs_memoire['L2'] / 2
                if unique_x > CENTRE_IMAGE:
                    self.derniere_ligne_perdue = "GAUCHE"
                    erreur_calculer = float((unique_x - demi_largeur) - CENTRE_IMAGE)
                else:
                    self.derniere_ligne_perdue = "DROITE"
                    erreur_calculer = float((unique_x + demi_largeur) - CENTRE_IMAGE)

            self.get_logger().warn(
                f"Mode Dégradé (1 ligne) | Perdue: {self.derniere_ligne_perdue} | Erreur: {erreur_calculer:.1f}",
                throttle_duration_sec=1.0
            )

        # ---------------------------------------------------------------------
        # MACHINE À ÉTATS MISE À JOUR (AVEC PHASE D'APPROCHE + GYRO)
        # ---------------------------------------------------------------------
        
        SEUIL_ANGLE_SECURITE = math.radians(45.0)

        if self.statut_virage == "ATTENTE_VIRAGE":
            # Étape 1 : Détection de l'intersection (perte de la ligne droite sur L1 et L2)
            if not l1_droite_visible and not l2_droite_visible:
                self.statut_virage = "APPROCHE_VIRAGE"
                self.get_logger().info("Ligne droite perdue. Phase d'approche : on attend que L1 recroise la piste.")

        elif self.statut_virage == "APPROCHE_VIRAGE":
            # Pendant cet état, on ne modifie PAS 'erreur_calculer'.
            # Le robot continue sur sa lancée avec le PID nominal pour bien se placer.
            
            # Étape 2 : Condition de déclenchement du vrai virage
            # On attend que le regard bas (L1) revoie les deux lignes
            if route_L1_complete:
                self.statut_virage = "FORCAGE_DROITE"
                self.frames_confirmation_sortie = 0
                
                # IMPORTANT : On reset l'intégrateur du Gyro pile au moment où on commence à tourner !
                self.angle_parcouru_virage = 0.0 
                self.last_time_imu = self.get_clock().now()
                
                self.get_logger().warn("L1 est alignée ! Lancement du virage forcé à droite au Gyroscope.")

        elif self.statut_virage == "FORCAGE_DROITE":
            # Étape 3 : Le virage est en cours
            erreur_calculer = 180.0 

            # Condition de sortie (comme validé précédemment) : 
            # Il faut avoir tourné d'au moins 75° ET que la caméra revoie la nouvelle route de manière stable
            if deux_lignes_visibles and (self.angle_parcouru_virage >= SEUIL_ANGLE_SECURITE):
                self.frames_confirmation_sortie += 1
                if self.frames_confirmation_sortie >= 5:
                    self.statut_virage = "VEILLE"
                    self.frames_confirmation_sortie = 0
                    self.get_logger().info(f"Virage terminé avec succès ! Angle Gyro : {math.degrees(self.angle_parcouru_virage):.1f}°")
                    
                    # Reset du topic /turn_sign
                    msg_reset = Bool()
                    msg_reset.data = False
                    self.turn_pub.publish(msg_reset)
            else:
                self.frames_confirmation_sortie = 0

        # ──── COUCHE VISUELLE FINALE (REPERES) ────
        cv2.line(debug_frame, (int(CENTRE_IMAGE), 0), (int(CENTRE_IMAGE), height), (255, 0, 255), 1)
        
        texte_mode = f"L1: {route_L1_complete} L2: {route_L2_complete} | Erreur: {erreur_calculer:.1f}"
        cv2.putText(debug_frame, texte_mode, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Affichage visuel de l'état du panneau sur l'image de debug
        couleur_fsm = (0, 0, 255) if self.statut_virage == "FORCAGE_DROITE" else (255, 255, 0)
        cv2.putText(debug_frame, f"PANNEAU FSM: {self.statut_virage} (Scans Droite Ok: {nb_niveaux_droite}/3)", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, couleur_fsm, 2)

        # Envoi de l'erreur finale (potentiellement écrasée par la FSM) au nœud de commande
        msg_error = Float32()
        msg_error.data = erreur_calculer
        self.error_pub.publish(msg_error)

        self.publier_image_debug(debug_frame)

    def Santize_coordinates(self, value, max_val):
        return int(max(0, min(value, max_val)))

    def publier_image_debug(self, frame):
        try:
            img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            self.debug_img_pub.publish(img_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"Erreur lors de la publication de l'image de débug : {e}")


def main(args=None):
    rclpy.init(args=args)
    node = VisionLineNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
