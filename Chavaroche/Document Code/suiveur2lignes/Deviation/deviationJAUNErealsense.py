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
            '/camera/camera/color/image_raw', 
            self.image_callback,
            10
        )
        
        # Publishers standards
        self.error_pub = self.create_publisher(Float32, '/line_tracking/error_raw', 10)
        self.masse_pub = self.create_publisher(Float32MultiArray, '/camera/zones_masses', 10)
        self.route_pub = self.create_publisher(Int32MultiArray, '/camera/zones_route', 10)
        self.lost_pub = self.create_publisher(Bool, '/line_tracking/route_perdue', 10)
        self.single_line_pub = self.create_publisher(Bool, '/line_tracking/ligne_unique', 10)
        self.debug_img_pub = self.create_publisher(Image, '/camera/debug_image', 10)
        
        self.derniere_ligne_perdue = "AUCUNE"

        self.nb_frames_accumulation = 5  # Nombre d'images en mémoire
        self.seuil_persistance = 3       # Un pixel doit être là au moins 3 fois sur 5
        self.historique_masques = deque(maxlen=self.nb_frames_accumulation)
        
        # ✅ AJUSTEMENT À TON ÉCHELLE (Proportionnel à tes 360px d'origine)
        self.largeurs_memoire = {
            'L1': 540,  # Palier bas (Ta valeur nominale)
            'L2': 450,  # Palier milieu (Éléments plus éloignés donc plus étroits)
            'L3': 310   # Palier haut
        }

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

            # ✅ CORRECTION : On vire uniquement les bruits minuscules (< 3px). 
            # On ne plafonne plus ici, la perspective s'en chargera plus tard.
            if largeur_paquet < 3:
                continue 

            if len(g) >= seuil_bruit:
                lignes_x.append(int(np.mean(g)))
                
        return lignes_x

    # ──── NOUVEAU : FONCTION DE FILTRAGE ANTI-REFLET ET VÉRIFICATION GÉOMÉTRIQUE ────
    def filtrer_paire_par_largeur(self, liste_lignes, nom_palier, tolerance=0.35):
        """
        Explore toutes les combinaisons de lignes détectées et retourne le premier couple
        (droite, gauche) dont la largeur correspond à la mémoire de ce palier.
        """
        nb_lignes = len(liste_lignes)
        if nb_lignes < 2:
            return None, None, False

        largeur_cible = self.largeurs_memoire[nom_palier]
        largeur_min = largeur_cible * (1.0 - tolerance)
        largeur_max = largeur_cible * (1.0 + tolerance)

        # Double boucle pour tester toutes les paires possibles
        for i in range(nb_lignes):
            for j in range(i + 1, nb_lignes):
                cand_droite = liste_lignes[i]
                cand_gauche = liste_lignes[j]
                largeur_calculee = cand_droite - cand_gauche

                # Si la largeur calculée entre dans nos critères géométriques
                if largeur_min <= largeur_calculee <= largeur_max:
                    # Mise à jour douce de la mémoire (Filtre passe-bas)
                    self.largeurs_memoire[nom_palier] = int(0.9 * largeur_cible + 0.1 * largeur_calculee)
                    return cand_droite, cand_gauche, True

        # Aucune paire ne correspond à la structure d'une route
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

        # ---- FILTRE TEMPOREL DE PERSISTANCE ----
        self.historique_masques.append(mask.copy())
        ratio_seuil = self.seuil_persistance / self.nb_frames_accumulation
        seuil_actuel = max(1, int(len(self.historique_masques) * ratio_seuil))

        bloc_images = np.array(self.historique_masques)
        accumulation = np.sum(bloc_images == 255, axis=0)
        mask = np.where(accumulation >= seuil_actuel, 255, 0).astype(np.uint8)

        # Superposer le masque en vert sur l'image debug
        mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        mask_rgb[:,:,0] = 0   
        mask_rgb[:,:,2] = 0   
        debug_frame = cv2.addWeighted(debug_frame, 1.0, mask_rgb, 0.5, 0)

        # ──── DEFINITION GÉOMÉTRIQUE DES ZONES ────
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

        # ──── RECHERCHE ET TRI DES LIGNES PAR LA DROITE ────
        lignes_x_L1 = self.trouver_centres_ligne(segment_L1, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L2 = self.trouver_centres_ligne(segment_L2, seuil_bruit=5, ecart_max=30, step=X_C[0])
        lignes_x_L3 = self.trouver_centres_ligne(segment_L3, seuil_bruit=5, ecart_max=30, step=X_C[0])

        lignes_L1_droite = sorted(lignes_x_L1, reverse=True)
        lignes_L2_droite = sorted(lignes_x_L2, reverse=True)
        lignes_L3_droite = sorted(lignes_x_L3, reverse=True)

        # ✅ FILTRAGE GEOMETRIQUE : Extraction des vraies routes immunisées contre les reflets
        droite_L1, gauche_L1, route_L1_complete = self.filtrer_paire_par_largeur(lignes_L1_droite, 'L1')
        droite_L2, gauche_L2, route_L2_complete = self.filtrer_paire_par_largeur(lignes_L2_droite, 'L2')
        droite_L3, gauche_L3, route_L3_complete = self.filtrer_paire_par_largeur(lignes_L3_droite, 'L3')

        # Comptages bruts pour l'affichage et la sécurité
        nb_lignes_L1 = len(lignes_L1_droite)
        nb_lignes_L2 = len(lignes_L2_droite)

        # Dessins des centres bruts détectés pour le débug (petits cercles transparents)
        # --- PALIER L1 (Thème Jaune) ---
        for x in lignes_L1_droite:
            # Si la route L1 est complète ET que ce point est l'un des deux retenus
            if route_L1_complete and (x == droite_L1 or x == gauche_L1):
                cv2.circle(debug_frame, (int(x), int(Y_L1)), 9, (120, 255, 255), -1)  # Jaune très clair/Brillant
            else:
                cv2.circle(debug_frame, (int(x), int(Y_L1)), 4, (0, 100, 100), -1)    # Jaune foncé/Olive (Rejeté)

        # --- PALIER L2 (Thème Cyan) ---
        for x in lignes_L2_droite:
            # Si la route L2 est complète ET que ce point est l'un des deux retenus
            if route_L2_complete and (x == droite_L2 or x == gauche_L2):
                cv2.circle(debug_frame, (int(x), int(Y_L2)), 9, (255, 255, 130), -1)  # Cyan très clair/Brillant
            else:
                cv2.circle(debug_frame, (int(x), int(Y_L2)), 4, (100, 100, 0), -1)    # Cyan foncé/Bleu nuit (Rejeté)

        # --- PALIER L3 (Thème Magenta) ---
        for x in lignes_L3_droite:
            # Si la route L3 est complète ET que ce point est l'un des deux retenus
            if route_L3_complete and (x == droite_L3 or x == gauche_L3):
                cv2.circle(debug_frame, (int(x), int(Y_L3)), 9, (255, 130, 255), -1)  # Magenta très clair/Brillant
            else:
                cv2.circle(debug_frame, (int(x), int(Y_L3)), 4, (100, 0, 100), -1)    # Magenta foncé/Violine (Rejeté)

        # ──── GESTION DES PUBLICATIONS ROS 2 STANDARD ────
        ordre_fixe = ['L1', 'L2', 'L2G', 'L2D', 'L3', 'L3G', 'L3D']
        self.masse_pub.publish(Float32MultiArray(data=[masses[z] for z in ordre_fixe]))
        self.route_pub.publish(Int32MultiArray(data=[route_detectee[z] for z in ordre_fixe]))

        # Sécurité : On est perdu si aucune route complète n'est validée ET aucune ligne unique n'est exploitable
        route_vitale_visible = (route_L1_complete or route_L2_complete or route_L3_complete or nb_lignes_L1 == 1 or nb_lignes_L2 == 1)
        self.lost_pub.publish(Bool(data=not route_vitale_visible))

        if not route_vitale_visible:
            self.error_pub.publish(Float32(data=0.0))
            self.single_line_pub.publish(Bool(data=False))
            self.publier_image_debug(debug_frame)
            return

        self.single_line_pub.publish(Bool(data=(not route_L1_complete and nb_lignes_L1 == 1)))

        # ──── TREE DE DÉCISION NETTOYÉ ET SÉCURISÉ ────
        
        # CONDITION A : Route validée sur L1 ET L2
        if route_L1_complete and route_L2_complete:
            centre_L1 = (droite_L1 + gauche_L1) // 2
            centre_L2 = (droite_L2 + gauche_L2) // 2

            err_L1 = float(centre_L1 - CENTRE_IMAGE)
            err_L2 = float(centre_L2 - CENTRE_IMAGE)
            erreur_calculer = (POIDS_L1 * err_L1) + (POIDS_L2 * err_L2)

            # Dessin du couloir de guidage validé
            cv2.line(debug_frame, (int(centre_L1), int(Y_L1)), (int(centre_L2), int(Y_L2)), (255, 255, 255), 3)
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 8, (255, 0, 0), -1)
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 8, (255, 0, 0), -1)

        # CONDITION B : Route validée sur L1 uniquement
        elif route_L1_complete:
            centre_L1 = (droite_L1 + gauche_L1) // 2
            erreur_calculer = float(centre_L1 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L1), int(Y_L1)), 8, (255, 0, 0), -1)

        # CONDITION C : Route validée sur L2 uniquement
        elif route_L2_complete:
            centre_L2 = (droite_L2 + gauche_L2) // 2
            erreur_calculer = float(centre_L2 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L2), int(Y_L2)), 8, (255, 0, 0), -1)

        # CONDITION D : Route validée sur L3 uniquement
        elif route_L3_complete:
            centre_L3 = (droite_L3 + gauche_L3) // 2
            erreur_calculer = float(centre_L3 - CENTRE_IMAGE)
            cv2.circle(debug_frame, (int(centre_L3), int(Y_L3)), 8, (255, 0, 0), -1)

        # CONDITION E : Mode dégradé (1 seule ligne isolée, pas de paire valide trouvée)
        else:
            # On utilise la ligne unique de L1 si disponible
            if nb_lignes_L1 == 1:
                unique_x = lignes_L1_droite[0]
                demi_largeur = self.largeurs_memoire['L1'] / 2
                if unique_x > CENTRE_IMAGE:
                    self.derniere_ligne_perdue = "GAUCHE"
                    erreur_calculer = float((unique_x - demi_largeur) - CENTRE_IMAGE)
                else:
                    self.derniere_ligne_perdue = "DROITE"
                    erreur_calculer = float((unique_x + demi_largeur) - CENTRE_IMAGE)

            # Sinon on se rabat sur la ligne unique de L2
            elif nb_lignes_L2 == 1:
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

        # ──── COUCHE VISUELLE FINALE (REPERES) ────
        cv2.line(debug_frame, (int(CENTRE_IMAGE), 0), (int(CENTRE_IMAGE), height), (255, 0, 255), 1) # Axe central rose
        
        texte_mode = f"Validé -> L1: {route_L1_complete} L2: {route_L2_complete} | Erreur: {erreur_calculer:.1f}"
        cv2.putText(debug_frame, texte_mode, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Envoi de l'erreur calculée au nœud de commande
        msg_error = Float32()
        msg_error.data = erreur_calculer
        self.error_pub.publish(msg_error)

        # Envoi final de l'image annotée vers le topic de débug
        self.publier_image_debug(debug_frame)

    def Santize_coordinates(self, value, max_val):
        return int(max(0, min(value, max_val)))

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
