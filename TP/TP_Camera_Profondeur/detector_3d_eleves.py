import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
import cv2
import os
import numpy as np
import openvino as ov

class detector_3d(Node):
    def __init__(self):
        super().__init__('detector_3d')

        # Initialisation des paramètres du nœud
        self.declare_parameter('device', 'CPU')
        self.declare_parameter('confidence', 0.5)
        self.declare_parameter('model_path', os.path.join(os.path.dirname(__file__), '..', 'models', 'yolo11n_openvino_model'))

        device = self.get_parameter('device').value
        self.confidence = self.get_parameter('confidence').value
        model_path = self.get_parameter('model_path').value

        self.bridge = CvBridge()

        # Variables pour stocker les paramètres intrinsèques de la caméra
        self.fx = self.fy = self.cx = self.cy = None

        # Configuration et chargement du modèle OpenVINO
        core = ov.Core()
        model_xml = os.path.join(model_path, 'yolo11n.xml')
        model = core.read_model(model_xml)
        self.compiled = core.compile_model(model, device)
        self.output = self.compiled.output(0)
        self.input_w, self.input_h = 640, 640

        # Liste des classes YOLO utiles
        self.class_names = [#liste des classes de votre modèle]

        # Profil de Qualité de Service (QoS) pour le flux vidéo
        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.BEST_EFFORT

        # ----------------------------------------------------------------------
        # EXERCICE 1 : CONFIGURATION DES COMMUNICATIONS ROS 2 (TOPICS ET MESSAGES)
        # ----------------------------------------------------------------------
        
        # TODO: Remplir le type de message et le nom du topic de calibration
        # Indice : Utilisez "ros2 topic list" et "ros2 interface show" pour trouver le topic de la RealSense et son type 
        # (on les importent au début vous pouvez aller vérifier)
        self.sub_info = self.create_subscription( # À COMPLÉTER, # À COMPLÉTER, self.callback_camera_info, 1)

        # TODO: Configurer les abonnés Message Filters pour la synchronisation temporelle
        # Trouvez les bons noms de topics pour l'image couleur (RGB) et l'image de profondeur rectifiée (Depth)
        self.sub_rgb = Subscriber(self, # À COMPLÉTER, # À COMPLÉTER, qos_profile=qos)
        self.sub_depth = Subscriber(self, # À COMPLÉTER, # À COMPLÉTER, qos_profile=qos)

        # Synchronisation temporelle des flux RGB et Depth (tolérance de 50ms)
        self.sync = ApproximateTimeSynchronizer([self.sub_rgb, self.sub_depth], queue_size=10, slop=0.05)
        self.sync.registerCallback(self.callback_rgbd)

        # TODO: Configurer les publishers avec les bons types de messages
        # pub_image doit publier l'image annotée, pub_points doit publier les coordonnées 3D
        self.pub_image = self.create_publisher(# À COMPLÉTER, '/detection/image_3d', 10)
        self.pub_points = self.create_publisher(# À COMPLÉTER, '/detection/position_3d', 10)
        self.pub_meta = self.create_publisher(Detection2DArray, '/detection/metadata', 10) # topic que vous creez et qui renvoie les valeurs
        
        self.get_logger().info('Nœud initialisé. En attente des flux de la caméra...')

    def callback_camera_info(self, msg):
        # ----------------------------------------------------------------------
        # EXERCICE 2 : EXTRACTION DE LA MATRICE INTRINSÈQUE K
        # ----------------------------------------------------------------------
        # Utilisez "ros2 interface show" sur le message CameraInfo pour comprendre la structure du tableau 'k'
        self.fx = # À COMPLÉTER
        self.fy = # À COMPLÉTER
        self.cx = # À COMPLÉTER
        self.cy = # À COMPLÉTER

    def detecter_couleur_feu(self, roi_bgr):
        """ Analyse la zone du feu pour déterminer si c'est ROUGE, VERT ou INCONNU """
        if roi_bgr.size == 0:
            return "inconnu"

        # Passage en HSV
        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

        # Seuils pour le Rouge (début et fin du spectre H)
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = mask_red1 + mask_red2

        # Seuils pour le Vert
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([90, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)

        # Compter les pixels correspondants
        nb_red = cv2.countNonZero(mask_red)
        nb_green = cv2.countNonZero(mask_green)

        seuil_pixels = 5

        if nb_red > nb_green and nb_red > seuil_pixels:
            return "rouge"
        elif nb_green > nb_red and nb_green > seuil_pixels:
            return "vert"
        
        return "inconnu"
    
    def pixel_to_3d(self, u, v, depth_image):
        if self.fx is None:
            return None

        # Définition d'une fenêtre de 10x10 pixels autour du centre pour filtrer le bruit
        half = 5
        u, v = int(u), int(v)
        h, w = depth_image.shape
        u1, u2 = max(0, u - half), min(w, u + half)
        v1, v2 = max(0, v - half), min(h, v + half)
        patch = depth_image[v1:v2, u1:u2]
        valid = patch[patch > 0]

        # Suppression des pixels aberrants (trous de mesure de la RealSense)
        valid = patch[patch > 0]
        if len(valid) == 0:
            return None

        # ----------------------------------------------------------------------
        # EXERCICE 3 : CONVERSION DE L'UNITÉ DE PROFONDEUR
        # ----------------------------------------------------------------------
        # La RealSense fournit la profondeur en millimètres (uint16).
        # TODO: Calculez la médiane du patch et convertissez la distance Z en mètres.
        Z = # À COMPLÉTER

        # ----------------------------------------------------------------------
        # EXERCICE 4 : MODÈLE STÉNOPÉ (PROJECTION INVERSE)
        # ----------------------------------------------------------------------
        # TODO: Appliquez les équations géométriques pour calculer X et Y en mètres.
        X = # À COMPLÉTER
        Y = # À COMPLÉTER

        return X, Y, Z

    def taille_reelle(self, x1, y1, x2, y2, Z):
        # ----------------------------------------------------------------------
        # EXERCICE 5 : CALCUL DES DIMENSIONS PHYSIQUES
        # ----------------------------------------------------------------------
        # TODO: Utilisez le théorème de Thalès appliqué à l'optique pour trouver la taille en mètres.
        largeur_m = # À COMPLÉTER
        hauteur_m = # À COMPLÉTER
        return largeur_m, hauteur_m

    def callback_rgbd(self, rgb_msg, depth_msg):
        if self.fx is None:
            return

        # Conversion des messages ROS au format d'images OpenCV
        frame = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding='bgr8')
        depth_image = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='passthrough')
        orig_h, orig_w = frame.shape[:2]

        if depth_image.shape != frame.shape[:2]:
            depth_image = cv2.resize(
                depth_image,
                (orig_w, orig_h),
                interpolation= cv2.INTER_NEAREST
            )

        # Traitement de l'image couleur par le réseau de neurones YOLO
        inp = self.preprocess(frame)
        output = self.compiled([inp])[self.output]
        detections = self.postprocess(output, orig_w, orig_h)

        meta_array = Detection2DArray()
        meta_array.header = rgb_msg.header

        # Boucle sur les objets détectés par l'IA
        for x1, y1, x2, y2, conf, cls in detections:
            cx_box = (x1 + x2) / 2.0
            cy_box = (y1 + y2) / 2.0

            # Calcul des coordonnées 3D réelles
            pos3d = self.pixel_to_3d(cx_box, cy_box, depth_image)

            if pos3d is not None:
                X, Y, Z = pos3d
                largeur, hauteur = self.taille_reelle(x1, y1, x2, y2, Z)

                # ----------------------------------------------------------------------
                # EXERCICE 6 : REMPLISSAGE DU MESSAGE DE SORTIE ROS 2
                # ----------------------------------------------------------------------
                # TODO: Renseignez les coordonnées X, Y, Z calculées dans le message PointStamped.
                pt = PointStamped()
                pt.header = rgb_msg.header
                pt.point.x = # À COMPLÉTER
                pt.point.y = # À COMPLÉTER
                pt.point.z = # À COMPLÉTER
                self.pub_points.publish(pt)

                nom_classe = self.class_names[cls]

                # --------------------------------------------------------------
                # ANALYSE COULEUR SI LE MODÈLE DÉTECTE UN FEU (PEU IMPORTE SA CLASSE DE BASE)
                # --------------------------------------------------------------
                couleur_box = (0, 255, 0) # Vert par défaut
                
                if nom_classe in ["feu_orange", "feu_rouge", "feu_vert"]:
                    h_img, w_img = frame.shape[:2]
                    roi = frame[max(0, y1):min(h_img, y2), max(0, x1):min(w_img, x2)]
                    
                    couleur = self.detecter_couleur_feu(roi)
                    nom_classe = f"feu_{couleur}" # Devient feu_rouge, feu_vert ou feu_inconnu
                    
                    if couleur == "rouge":
                        couleur_box = (0, 0, 255)
                    elif couleur == "vert":
                        couleur_box = (0, 255, 0)
                    else:
                        couleur_box = (0, 255, 255) # Jaune pour inconnu/orange
                # --------------------------------------------------------------

                det = Detection2D()
                hyp = ObjectHypothesisWithPose()
                hyp.hypothesis.class_id = nom_classe
                hyp.hypothesis.score = conf
                det.results = [hyp]
                
                det.bbox.center.position.x = cx_box
                det.bbox.center.position.y = cy_box
                det.bbox.size_x = float(x2 - x1)
                det.bbox.size_y = float(y2 - y1)
                
                det.id = f"Z:{Z:.2f};W:{largeur:.2f};H:{hauteur:.2f};X:{X:.2f};Y:{Y:.2f}"
                meta_array.detections.append(det)

                cv2.rectangle(frame, (x1, y1), (x2, y2), couleur_box, 2)
                cv2.putText(frame, f"{nom_classe} Z:{Z:.2f}m", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, couleur_box, 2)

        self.pub_meta.publish(meta_array)

        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        out_msg.header = rgb_msg.header
        self.pub_image.publish(out_msg)

    def preprocess(self, frame):
        img = cv2.resize(frame, (self.input_w, self.input_h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)
        return np.expand_dims(img, axis=0)

    def postprocess(self, output, orig_w, orig_h):
        preds = output[0].T
        boxes = preds[:, :4]
        scores = preds[:, 4:]
        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]
        
        scale_x, scale_y = orig_w / self.input_w, orig_h / self.input_h
        results = []
        
        for box, conf, cls in zip(boxes, confidences, class_ids):
            if np.isnan(box).any() or np.isnan(conf):
                continue
            
            # Index 1, 2, 3 correspondent à feu_orange, feu_rouge, feu_vert dans self.class_names
            if cls in [1, 2, 3]:
                seuil_actuel = 0.3 # Confiance abaissée à 30% pour attraper tous les feux loin ou sombres
            else:
                seuil_actuel = self.confidence
                
            if conf < seuil_actuel:
                continue
                
            cx, cy, w, h = box
            x1 = int((cx - w / 2) * scale_x)
            y1 = int((cy - h / 2) * scale_y)
            x2 = int((cx + w / 2) * scale_x)
            y2 = int((cy + h / 2) * scale_y)
            results.append((x1, y1, x2, y2, float(conf), int(cls)))
            
        return results

def main(args=None):
    rclpy.init(args=args)
    node = detector_3d()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
