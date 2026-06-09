#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Header, Float32, Float32MultiArray, Int32MultiArray
from cv_bridge import CvBridge, CvBridgeError
from collections import deque
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

        self.nb_frames_accumulation = 5  # Nombre d'images en mémoire
        self.seuil_persistance = 3       # Un pixel doit être là au moins 3 fois sur 5
        self.historique_masques = deque(maxlen=self.nb_frames_accumulation)
        
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

        # ──── 1. ALGORITHME DE CLUSTERING (On rassemble les pixels proches) ────
        groupes = []
        groupe_courant = [indices_blancs[0]]

        for x in indices_blancs[1:]:
            if x - groupe_courant[-1] > ecart_max:
                groupes.append(groupe_courant)
                groupe_courant = [x]
            else:
                groupe_courant.append(x)
        groupes.append(groupe_courant)

        # ──── 2. FILTRAGE ET EXTRACTION DES CENTRES ────
        for g in groupes:
            # Comme le groupe est trié, le début est à l'index 0 et la fin à l'index -1
            x_debut = g[0]
            x_fin = g[-1]
            # largeur_paquet = x_fin - x_debut

            # SÉCURITÉ TAILLE : On vire les bruits (<5px) et la caisse orange (>60px)
            # if largeur_paquet < 4 or largeur_paquet > 50:
            #     continue # On ignore ce paquet et on passe au suivant

            # SÉCURITÉ DENSITÉ : Est-ce qu'il y a assez de pixels blancs dedans ?
            if len(g) >= seuil_bruit:
                lignes_x.append(int(np.mean(g)))
                
        return lignes_x
    
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
        lower_yellow = np.array([18,  35,  70])
        upper_yellow = np.array([32, 255, 255])

        # Conversion HSV 
        hsv  = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # ---- FILTRE TEMPOREL DE PERSISTANCE ----
        # 1. On ajoute la copie du masque actuel dans notre rolling-buffer
        self.historique_masques.append(mask.copy())

        # 2. On calcule le seuil de persistance dynamique (pour le démarrage)
        # Si on n'a que 2 images en mémoire, on adapte le seuil pour ne pas bloquer le robot
        ratio_seuil = self.seuil_persistance / self.nb_frames_accumulation
        seuil_actuel = max(1, int(len(self.historique_masques) * ratio_seuil))

        # 3. Somme vectorisée (Ultra rapide)
        # On empile les images et on compte combien de fois chaque pixel est à 255
        bloc_images = np.array(self.historique_masques)
        accumulation = np.sum(bloc_images == 255, axis=0)

        # 4. On ne garde que les pixels stables (qui dépassent le seuil)
        mask = np.where(accumulation >= seuil_actuel, 255, 0).astype(np.uint8)


        # Superposer le masque en vert sur l'image debug
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_rgb[:,:,0] = 0   # enlever rouge
        mask_rgb[:,:,2] = 0   # enlever bleu
        debug_frame = cv2.addWeighted(debug_frame, 1.0, mask_rgb, 0.5, 0)


        # ──── 1. DEFINITION GÉOMÉTRIQUE DES ZONES ────
        w_step = width // 10
        step = width - 1
        X_G, X_C, X_D, X_Full = (0, 1), (1, step), (step, width), (0, width)

        masses = {}
        route_detectee = {}
        centres_x = {}

        # Les partitions pour les topics d'état (on conserve ta structure de dictionnaire)
        partitions = {
            'L3G': (Y_L3, X_G), 'L3': (Y_L3, X_C), 'L3D': (Y_L3, X_D),
            'L2G': (Y_L2, X_G), 'L2': (Y_L2, X_C), 'L2D': (Y_L2, X_D),
            'L1':  (Y_L1, X_C)  # Harmonisé sur X_C pour éviter le bruit des bords de l'image
        }

        # Extraction des segments principaux L1 et L2
        segment_L1 = mask[Y_L1, X_C[0]:X_C[1]]
        segment_L2 = mask[Y_L2, X_C[0]:X_C[1]]
        segment_L3 = mask[Y_L3, X_C[0]:X_C[1]]

        SEUIL_PRESENCE = 30  # Seuil de pixels blancs

        # ──── 2. BOUCLE DE DIAGNOSTIC DES ZONES (MASSES & ETATS) ────
        for nom, (y, (x_start, x_end)) in partitions.items():
            segment = mask[y, x_start:x_end].copy()
            masse = int(np.sum(segment == 255))
            masses[nom] = float(masse)
            route_detectee[nom] = 1 if masse > SEUIL_PRESENCE else 0

            # Rendu visuel des rectangles de partition (Vert si détecté, Rouge sinon)
            couleur = (0, 255, 0) if route_detectee[nom] == 1 else (0, 0, 255)
            cv2.line(debug_frame, (x_start, y), (x_end, y), couleur, 2)

        # ──── 3. RECHERCHE ET TRI DES LIGNES PAR LA DROITE ────
        lignes_x_L1 = self.trouver_centres_ligne(segment_L1, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L2 = self.trouver_centres_ligne(segment_L2, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L3 = self.trouver_centres_ligne(segment_L3, seuil_bruit=5, ecart_max=30, step=X_C[0])

        # LE SECRET : On trie par ordre décroissant (Du plus grand X au plus petit X -> de Droite à Gauche)
        lignes_L1_droite = sorted(lignes_x_L1, reverse=True)
        lignes_L2_droite = sorted(lignes_x_L2, reverse=True)
        lignes_L3_droite = sorted(lignes_x_L3, reverse=True)


        nb_lignes_L1 = len(lignes_L1_droite)
        nb_lignes_L2 = len(lignes_L2_droite)
        nb_lignes_L3 = len(lignes_L3_droite)

        # Dessins des lignes détectées (Points Jaunes pour L1, Points Cyan pour L2)
        for x in lignes_L1_droite:
            cv2.circle(debug_frame, (int(x), int(Y_L1)), 8, (0, 255, 255), -1)
        for x in lignes_L2_droite:
            cv2.circle(debug_frame, (int(x), int(Y_L2)), 8, (255, 255, 0), -1)
        for x in lignes_L3_droite:
            cv2.circle(debug_frame, (int(x), int(Y_L3)), 8, (255, 0, 255), -1)

        # ──── 4. GESTION DES PUBLICATIONS ROS 2 STANDARD ────
        ordre_fixe = ['L1', 'L2', 'L2G', 'L2D', 'L3', 'L3G', 'L3D']
        
        self.masse_pub.publish(Float32MultiArray(data=[masses[z] for z in ordre_fixe]))
        self.route_pub.publish(Int32MultiArray(data=[route_detectee[z] for z in ordre_fixe]))

        # Sécurité : Si aucune ligne n'est visible nulle part sur L1 et L2 -> Arrêt d'urgence
        route_vitale_visible = (nb_lignes_L1 > 0 or nb_lignes_L2 > 0 or nb_lignes_L3 > 0)
        self.lost_pub.publish(Bool(data=not route_vitale_visible))

        if not route_vitale_visible:
            self.error_pub.publish(Float32(data=0.0))
            self.single_line_pub.publish(Bool(data=False))
            self.publier_image_debug(debug_frame)
            return

        self.single_line_pub.publish(Bool(data=(nb_lignes_L1 == 1)))

        # ──── 5. NOUVEL ARBRE DE DÉCISION (LOGIQUE DEMANDÉE) ────
        erreur_calculer = 0.0
        route_L1_complete = (nb_lignes_L1 >= 2)
        route_L2_complete = (nb_lignes_L2 >= 2)
        route_L3_complete = (nb_lignes_L3 >= 2)

        # CONDITION A : Route détectée sur L1 ET L2
        if route_L1_complete and route_L2_complete:
            # On prend les 2 lignes les plus à droite pour chaque niveau
            centre_L1 = (lignes_L1_droite[0] + lignes_L1_droite[1]) // 2
            centre_L2 = (lignes_L2_droite[0] + lignes_L2_droite[1]) // 2

            err_L1 = float(centre_L1 - CENTRE_IMAGE)
            err_L2 = float(centre_L2 - CENTRE_IMAGE)
            erreur_calculer = (POIDS_L1 * err_L1) + (POIDS_L2 * err_L2)

            # Mémorisation de la largeur de la route active (via L1)
            largeur_L1 = abs(lignes_L1_droite[0] - lignes_L1_droite[1])
            if 200 < largeur_L1 < 500:
                self.largeur_route_memoire = (0.7 * self.largeur_route_memoire + 0.3 * largeur_L1)

            # Dessin de la ligne de guidage blanche au sol
            cv2.line(debug_frame, (int(centre_L1), int(Y_L1)), (int(CENTRE_IMAGE), int(Y_L1)), (255, 255, 255), 2)
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 5, (255, 0, 0), -1)
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 5, (255, 0, 0), -1)

        # CONDITION B : Route détectée sur L1 uniquement
        elif route_L1_complete and not route_L2_complete:
            centre_L1 = (lignes_L1_droite[0] + lignes_L1_droite[1]) // 2
            erreur_calculer = float(centre_L1 - CENTRE_IMAGE)

            largeur_L1 = abs(lignes_L1_droite[0] - lignes_L1_droite[1])
            if 200 < largeur_L1 < 500:
                self.largeur_route_memoire = (0.7 * self.largeur_route_memoire + 0.3 * largeur_L1)
            
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 5, (255, 0, 0), -1)

        # CONDITION C : Route détectée sur L2 uniquement
        elif route_L2_complete and not route_L1_complete:
            centre_L2 = (lignes_L2_droite[0] + lignes_L2_droite[1]) // 2
            erreur_calculer = float(centre_L2 - CENTRE_IMAGE)
            
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 5, (255, 0, 0), -1)

        # CONDITION D : Route détectée sur L3 uniquement (Cas très dégradé, on se fie à la ligne la plus à droite de L3)
        elif route_L3_complete and not route_L1_complete and not route_L2_complete:
            centre_L3 = (lignes_L3_droite[0] + lignes_L3_droite[1]) // 2
            erreur_calculer = float(centre_L3 - CENTRE_IMAGE)
            
            cv2.circle(debug_frame, (int(centre_L3), int(Y_L3)), 5, (255, 0, 0), -1)

        # CONDITION E : Mode dégradé (Moins de 2 lignes partout -> Simulation de la ligne perdue)
        else:
            demi_largeur = self.largeur_route_memoire / 2

            # Option 1 : On se rabat sur la ligne unique de L1 si elle existe
            if nb_lignes_L1 == 1:
                unique_x = lignes_L1_droite[0]
                if unique_x > CENTRE_IMAGE:
                    self.derniere_ligne_perdue = "GAUCHE"
                    erreur_calculer = float((unique_x - demi_largeur) - CENTRE_IMAGE)
                else:
                    self.derniere_ligne_perdue = "DROITE"
                    erreur_calculer = float((unique_x + demi_largeur) - CENTRE_IMAGE)

            # Option 2 : Sinon, on se rabat sur la ligne unique de L2
            elif nb_lignes_L2 == 1:
                unique_x = lignes_L2_droite[0]
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

        # ──── 6. COUCHE VISUELLE FINALE (REPERES) ────
        # Correction syntaxique : Remplacement des 'int_CENTRE_IMAGE' défectueux par 'int(CENTRE_IMAGE)'
        cv2.line(debug_frame, (int(CENTRE_IMAGE), 0), (int(CENTRE_IMAGE), height), (255, 0, 255), 1) # Axe central rose
        
        texte_mode = f"L1: {nb_lignes_L1} L2: {nb_lignes_L2} | Erreur: {erreur_calculer:.1f}"
        cv2.putText(debug_frame, texte_mode, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Envoi de l'erreur calculée au nœud de commande
        msg_error = Float32()
        msg_error.data = erreur_calculer
        self.error_pub.publish(msg_error)

        # Envoi final de l'image annotée vers le topic de débug
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
