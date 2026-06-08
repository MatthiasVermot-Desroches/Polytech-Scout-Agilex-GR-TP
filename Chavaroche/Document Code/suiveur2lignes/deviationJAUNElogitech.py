#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Header, Float32, Float32MultiArray, Int32MultiArray
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np

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
            '/logitech_c505e/image_raw', 
            self.image_callback,
            10
        )
        
        # Publishers standards
        self.error_pub = self.create_publisher(Float32, '/line_tracking/error_raw', 10)
        self.masse_pub = self.create_publisher(Float32MultiArray, '/camera/zones_masses', 10)
        self.route_pub = self.create_publisher(Int32MultiArray, '/camera/zones_route', 10)
        self.lost_pub = self.create_publisher(Bool, '/line_tracking/route_perdue', 10)
        self.single_line_pub = self.create_publisher(Bool, '/line_tracking/ligne_unique', 10)
        
        # NOUVEAU PUBLISHER : Rendu visuel en temps réel pour Foxglove ou Rviz
        self.debug_img_pub = self.create_publisher(Image, '/camera/debug_image', 10)
        
        self.derniere_ligne_perdue = "AUCUNE"
        
        # ✅ MÉMOIRE : Largeur réelle de la route observée en mode nominal (2 lignes)
        self.largeur_route_memoire = 360  # Valeur par défaut, sera calibrée

    def filtrer_jaune_pur(self, cv_image):
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)

        # Masque de base
        mask_base = cv2.inRange(hsv,
            np.array([10, 50, 60]),
            np.array([30, 255, 255]))

        # Saturation dynamique
        pixels_jaunes = s[mask_base == 255]
        if len(pixels_jaunes) == 0:
            return mask_base

        saturation_mediane = np.median(pixels_jaunes)
        seuil_s = max(80, saturation_mediane * 0.6)

        mask_strict = cv2.inRange(hsv,
            np.array([10, int(seuil_s), 80]),
            np.array([30, 255, 255]))

        # Morphologie légère
        kernel = np.ones((3, 3), np.uint8)
        mask_strict = cv2.morphologyEx(mask_strict, cv2.MORPH_OPEN,  kernel)
        mask_strict = cv2.morphologyEx(mask_strict, cv2.MORPH_CLOSE, kernel)

        # ── NOUVEAU : filtre par taille de contour ──────────────────────────
        # Une ligne de scotch fait ~10-25px de large max
        # Un reflet fait 100-300px de large → on l'élimine
        contours, _ = cv2.findContours(
            mask_strict, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        mask_filtre = np.zeros_like(mask_strict)

        for cnt in contours:
            x, y, w, h_box = cv2.boundingRect(cnt)
            aire = cv2.contourArea(cnt)

            # Filtres :
            # 1. Largeur max 40px — une ligne de scotch ne fait pas plus
            # 2. Hauteur min 20px — une vraie ligne est longue
            # 3. Ratio longueur/largeur > 3 — une ligne est élancée, un reflet est rond/carré
            if w == 0 or h_box == 0:
                continue

            ratio = max(w, h_box) / min(w, h_box)

            self.get_logger().info(
                f"Contour w={w} h={h_box} ratio={ratio:.1f} aire={aire:.0f}",
                throttle_duration_sec=0.1)

            # w       # ← largeur max du scotch en pixels, augmente si trop strict
            # h_box   # ← longueur min, baisse si lignes courtes
            # ratio   # ← forme élancée, baisse à 2 si virages serrés coupent les lignes
            # aire    # ← surface min, baisse si lignes très fines

            if w <= 60 and h_box >= 4 and ratio >= 3 and aire >= 20:
                cv2.drawContours(mask_filtre, [cnt], -1, 255, -1)

        return mask_filtre

    def trouver_centres_ligne(self, masque_ligne, seuil_bruit=5, ecart_max=40, step=0):
        indices_blancs = np.where(masque_ligne == 255)[0] + step
        lignes_x = []

        if len(indices_blancs) == 0:
            return lignes_x

        # Algorithme de clustering (Groupement)
        groupes = []
        groupe_courant = [indices_blancs[0]]

        for x in indices_blancs[1:]:
            if x - groupe_courant[-1] > ecart_max:
                groupes.append(groupe_courant)
                groupe_courant = [x]
            else:
                groupe_courant.append(x)
        groupes.append(groupe_courant)

        # Extraction des centres valides
        for g in groupes:
            if len(g) >= seuil_bruit:
                lignes_x.append(int(np.mean(g)))
                
        return lignes_x
    
    def image_callback(self, msg):

        POIDS_L1 = 0.8
        POIDS_L2 = 0.2

        erreur_calculer = 0.0
        err_L1 = 0.0
        err_L2 = 0.0

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f"Erreur de conversion CvBridge: {e}")
            return

        # cv_image = cv_image[280:, :].copy()

        height, width, _ = cv_image.shape  

        CENTRE_IMAGE = width / 2  
        int_CENTRE_IMAGE = int(CENTRE_IMAGE)

        Y_L3 = 170 
        Y_L2 = 320 
        Y_L1 = 450 

        # --- NOUVEAU : On crée une copie de l'image d'origine pour dessiner nos repères ---
        debug_frame = cv_image.copy()

        # Configuration des seuils HSV
        lower_yellow = np.array([10,  50,  60])
        upper_yellow = np.array([30, 255, 255])

        # Conversion HSV 
        hsv  = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # Filtre temporel si activé
        if hasattr(self, 'historique_masques'):
            self.historique_masques.append(mask.copy())
            if len(self.historique_masques) > self.nb_frames_accumulation:
                self.historique_masques.pop(0)
            if len(self.historique_masques) == self.nb_frames_accumulation:
                accumulation = np.zeros_like(mask, dtype=np.uint8)
                for m in self.historique_masques:
                    accumulation += (m > 0).astype(np.uint8)
                mask = np.where(
                    accumulation >= self.seuil_persistance, 255, 0
                ).astype(np.uint8)


        # Superposer le masque en vert sur l'image debug
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_rgb[:,:,0] = 0   # enlever rouge
        mask_rgb[:,:,2] = 0   # enlever bleu
        debug_frame = cv2.addWeighted(debug_frame, 1.0, mask_rgb, 0.5, 0)


        # Définition des zones X
        w_step = width // 10
        step = width - 1
        X_G = (0, 1)          
        X_C = (1, step)  
        X_D = (step, width)   
        X_Full = (0, width)

        masses = {}
        centres_x = {}
        route_detectee = {}

        partitions = {
            'L3G': (Y_L3, X_G), 'L3': (Y_L3, X_C), 'L3D': (Y_L3, X_D),
            'L2G': (Y_L2, X_G), 'L2': (Y_L2, X_C), 'L2D': (Y_L2, X_D),
                                'L1': (Y_L1, X_Full)
        }

        
        segment_L1 = mask[Y_L1, X_C[0]:X_C[1]]
        segment_L2 = mask[Y_L2, X_C[0]:X_C[1]]

        SEUIL_PRESENCE = 50  # Seuil de pixels blancs pour considérer la route présente dans une zone

        for nom, (y, (x_start, x_end)) in partitions.items():
            segment = mask[y, x_start:x_end].copy()
            masse   = int(np.sum(segment == 255))
            masses[nom] = float(masse)

            if masse > SEUIL_PRESENCE:
                route_detectee[nom] = 1
                lignes = self.trouver_centres_ligne(
                    segment, seuil_bruit=3, ecart_max=40, step=x_start)
                # Centre = ligne la plus proche du centre image
                if lignes:
                    centres_x[nom] = min(lignes, key=lambda x: abs(x - CENTRE_IMAGE))
                else:
                    centres_x[nom] = CENTRE_IMAGE
            else:
                route_detectee[nom] = 0
                centres_x[nom]      = CENTRE_IMAGE

            couleur = (0, 255, 0) if route_detectee[nom] == 1 else (0, 0, 255)
            cv2.line(debug_frame, (x_start, y), (x_end, y), couleur, 2)
            if route_detectee[nom] == 1:
                cv2.circle(debug_frame, (centres_x[nom], y), 5, (255, 0, 0), -1)

        lignes_x_L1 = self.trouver_centres_ligne(segment_L1, seuil_bruit=5, ecart_max=40, step=X_C[0])
        lignes_x_L2 = self.trouver_centres_ligne(segment_L2, seuil_bruit=5, ecart_max=40, step=X_C[0])

        for x in lignes_x_L1:
            cv2.circle(debug_frame, (x, Y_L1), 8, (0, 255, 255), -1)

        for x in lignes_x_L2:
            cv2.circle(debug_frame, (x, Y_L2), 8, (255, 255, 0), -1)

        nb_lignes_L1 = len(lignes_x_L1)
        nb_lignes_L2 = len(lignes_x_L2)

        ordre_fixe = ['L1', 'L2', 'L2G', 'L2D', 'L3', 'L3G', 'L3D']

        # Publication des masses et états de route
        msg_masses = Float32MultiArray()
        msg_masses.data = [masses[z] for z in ordre_fixe]
        self.masse_pub.publish(msg_masses)

        msg_route = Int32MultiArray()
        msg_route.data = [route_detectee[z] for z in ordre_fixe]
        self.route_pub.publish(msg_route)
        
        zones_vitales = [route_detectee['L1'], route_detectee['L2']]
        route_vitale_visible = (sum(zones_vitales) > 0)

        msg_lost = Bool()
        if not route_vitale_visible:
            msg_lost.data = True
            self.lost_pub.publish(msg_lost)
            
            msg_error = Float32()
            msg_error.data = 0.0
            self.error_pub.publish(msg_error)
            
            msg_single = Bool()
            msg_single.data = False
            self.single_line_pub.publish(msg_single)
            
            # On publie l'image de débug même en cas de perte de piste
            self.publier_image_debug(debug_frame)
            return
        else:
            msg_lost.data = False
        self.lost_pub.publish(msg_lost)

        # Extraction géométrique avancée sur L1

        msg_single = Bool()
        msg_single.data = (nb_lignes_L1 == 1)
        self.single_line_pub.publish(msg_single)

        # Calcul de l'erreur globale
        if nb_lignes_L1 == 2:
            self.derniere_ligne_perdue = "AUCUNE"
            centre_L1 = (lignes_x_L1[0] + lignes_x_L1[1]) // 2

            largeur = abs(lignes_x_L1[1] - lignes_x_L1[0])
            if 200 < largeur < 500:
                self.largeur_route_memoire = (0.7 * self.largeur_route_memoire + 0.3 * largeur)

                # L2 — utiliser trouver_centres_ligne si 2 lignes, sinon centres_x
                if len(lignes_x_L2) == 2:
                    centre_L2 = (lignes_x_L2[0] + lignes_x_L2[1]) // 2
                else:
                    centre_L2 = centres_x['L2']

                err_L1          = float(centre_L1  - CENTRE_IMAGE)
                err_L2          = float(centre_L2  - CENTRE_IMAGE)
                erreur_calculer = POIDS_L1 * err_L1 + POIDS_L2 * err_L2

                cv2.line(debug_frame, (int(centre_L1), int(Y_L1)), (int_CENTRE_IMAGE, int(Y_L1)), (255, 255, 255), 2)

        elif nb_lignes_L1 == 1:
            unique_x = lignes_x_L1[0]
            demi_largeur = self.largeur_route_memoire / 2
            
            if nb_lignes_L2 == 2:
                centre_L2 = (lignes_x_L2[0] + lignes_x_L2[1]) // 2
                err_L2    = float(centre_L2 - CENTRE_IMAGE)
                erreur_calculer = err_L2

            else:

                if unique_x > CENTRE_IMAGE:
                    self.derniere_ligne_perdue = "GAUCHE"
                    # ✅ Ligne droite visible → supposer la gauche à distance demi_largeur
                    erreur_calculer = float((unique_x - demi_largeur) - CENTRE_IMAGE)
                else:
                    self.derniere_ligne_perdue = "DROITE"
                    # ✅ Ligne gauche visible → supposer la droite à distance demi_largeur
            
            self.get_logger().warn(
                f"Une ligne visible à {unique_x}px | Ligne perdue: {self.derniere_ligne_perdue} | Erreur: {erreur_calculer:.1f}",
                throttle_duration_sec=1.0)
        else:
            err_L2 = float(centres_x['L2'] - CENTRE_IMAGE)
            erreur_calculer = err_L2 if route_detectee['L2'] else 0.0

        # --- RENDU VISUEL : Ligne verticale centrale de l'écran (Référence CENTRE_IMAGE) ---
        cv2.line(debug_frame, (int_CENTRE_IMAGE, 0), (int_CENTRE_IMAGE, height), (255, 0, 255), 1) # Ligne rose au centre
        
        # Affichage du mode sur l'image
        texte_mode = f"Lignes visibles: {nb_lignes_L1} | Last Lost: {self.derniere_ligne_perdue}"
        cv2.putText(debug_frame, texte_mode, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Envoi de l'erreur finale au robot
        msg_error = Float32()
        msg_error.data = erreur_calculer
        self.error_pub.publish(msg_error)

        # Envoi final de l'image annotée vers ROS 2
        self.publier_image_debug(debug_frame)


    def publier_image_debug(self, frame):
        """Convertit l'image de débug OpenCV et la publie sur le topic ROS 2."""
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
