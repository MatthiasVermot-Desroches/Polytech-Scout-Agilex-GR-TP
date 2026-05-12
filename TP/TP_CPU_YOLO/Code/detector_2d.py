import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ament_index_python.packages import get_package_share_directory
import cv2
import os
import numpy as np
import openvino as ov

class Detector2D(Node):
    def __init__(self):
        super().__init__('detector_2d')

        # 1. On récupère le chemin du dossier "share" du paquet
        package_share_dir = get_package_share_directory('detection_pkg')

        # 2. On définit le chemin par défaut vers le dossier du modèle
        default_model_path = os.path.join(package_share_dir, 'models', 'yolo11n_openvino_model')

        self.declare_parameter('device', 'GPU')
        self.declare_parameter('confidence', 0.5)
        self.declare_parameter('model_path',default_model_path)

        device     = self.get_parameter('device').value
        confidence = self.get_parameter('confidence').value
        model_path = self.get_parameter('model_path').value

        self.confidence = confidence
        self.bridge     = CvBridge()

        # Chargement via OpenVINO directement
        self.get_logger().info(f'Chargement du modèle OpenVINO sur {device}...')
        core = ov.Core()
        model_xml = os.path.join(model_path, 'yolo11n.xml')
        model = core.read_model(model_xml)
        self.compiled = core.compile_model(model, device)
        self.output    = self.compiled.output(0)

        # Taille d'entrée du modèle (640x640 pour yolo11n)
        self.input_w = 640
        self.input_h = 640

        # Noms des classes COCO (base de donnée utilisée ici par yolov11n, tous les objets ne sont pas utiles on utilise ca en tant qu'exemple)
        self.class_names = [
            'person','bicycle','car','motorcycle','airplane','bus','train','truck',
            'boat','traffic light','fire hydrant','stop sign','parking meter','bench',
            'bird','cat','dog','horse','sheep','cow','elephant','bear','zebra','giraffe',
            'backpack','umbrella','handbag','tie','suitcase','frisbee','skis','snowboard',
            'sports ball','kite','baseball bat','baseball glove','skateboard','surfboard',
            'tennis racket','bottle','wine glass','cup','fork','knife','spoon','bowl',
            'banana','apple','sandwich','orange','broccoli','carrot','hot dog','pizza',
            'donut','cake','chair','couch','potted plant','bed','dining table','toilet',
            'tv','laptop','mouse','remote','keyboard','cell phone','microwave','oven',
            'toaster','sink','refrigerator','book','clock','vase','scissors','teddy bear',
            'hair drier','toothbrush'
        ]

        # on s'abonne au bon topic de la caméra 
        self.sub = self.create_subscription(Image , '/camera/camera/color/image_raw' , self.callback , 10)

        # on publie sur un topic que l'on creer
        self.pub_image = self.create_publisher(Image, '/detection/image', 10)

        self.get_logger().info(f'Detector2D prêt sur {device}')

    def preprocess(self, frame):
        # Resize + normalize pour YOLOv11
        img = cv2.resize(frame, (self.input_w, self.input_h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)          # HWC → CHW
        img = np.expand_dims(img, axis=0)     # CHW → NCHW
        return img

    def postprocess(self, output, orig_w, orig_h):
        # output shape : (1, 84, 8400) pour yolo11n COCO
        preds = output[0]  # (84, 8400)
        preds = preds.T    # (8400, 84)

        boxes  = preds[:, :4]   # cx, cy, w, h
        scores = preds[:, 4:]   # 80 classes

        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(len(scores)), class_ids]

        # Filtre par confiance
        mask = confidences > self.confidence
        boxes       = boxes[mask]
        confidences = confidences[mask]
        class_ids   = class_ids[mask]

        # Conversion cx,cy,w,h → x1,y1,x2,y2 en coordonnées originales
        scale_x = orig_w / self.input_w
        scale_y = orig_h / self.input_h

        results = []
        for box, conf, cls in zip(boxes, confidences, class_ids):
            cx, cy, w, h = box
            x1 = int((cx - w / 2) * scale_x)
            y1 = int((cy - h / 2) * scale_y)
            x2 = int((cx + w / 2) * scale_x)
            y2 = int((cy + h / 2) * scale_y)
            results.append((x1, y1, x2, y2, float(conf), int(cls)))

        return results

    def callback(self, msg):
        frame    = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        orig_h, orig_w = frame.shape[:2]

        inp     = self.preprocess(frame)
        output  = self.compiled([inp])[self.output]
        detections = self.postprocess(output, orig_w, orig_h)

        for x1, y1, x2, y2, conf, cls in detections:
            label = self.class_names[cls] if cls < len(self.class_names) else str(cls)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f'{label} {conf:.2f}',
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

        out_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        out_msg.header = msg.header
        self.pub_image.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = Detector2D()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
