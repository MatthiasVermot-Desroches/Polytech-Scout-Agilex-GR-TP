#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
from rcl_interfaces.msg import ParameterDescriptor

class LogitechCameraNode(Node):
    def __init__(self):
        super().__init__('logitech_camera_node')
        
        # Declare parameters (Mis à jour sur /dev/video6 et résolution 1280x720)
        self.declare_parameter('device', '/dev/video6', ParameterDescriptor(description='Video device'))
        self.declare_parameter('camera_name', 'logitech_c505e', ParameterDescriptor(description='Camera name'))
        self.declare_parameter('frame_id', 'camera_frame', ParameterDescriptor(description='Frame ID'))
        self.declare_parameter('framerate', 30, ParameterDescriptor(description='Target framerate'))
        self.declare_parameter('width', 1280, ParameterDescriptor(description='Image width'))
        self.declare_parameter('height', 720, ParameterDescriptor(description='Image height'))
        
        # Get parameters
        device = self.get_parameter('device').value
        self.camera_name = self.get_parameter('camera_name').value
        self.frame_id = self.get_parameter('frame_id').value
        self.framerate = self.get_parameter('framerate').value
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        
        self.get_logger().info(f'Opening camera: {device}')
        
        # Open camera
        self.cap = cv2.VideoCapture(device)
        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open {device}')
            raise RuntimeError(f'Cannot open {device}')
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)
        
        # Get actual values
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        self.get_logger().info(f'Camera opened: {actual_width}x{actual_height} @ {actual_fps} FPS')
        
        # Create publishers
        self.image_pub = self.create_publisher(Image, f'{self.camera_name}/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, f'{self.camera_name}/camera_info', 10)
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Load camera info
        self.camera_info = self._load_camera_info()
        
        # Timer for publishing
        timer_period = 1.0 / self.framerate
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
    def _load_camera_info(self):
        """Load camera calibration info aligned with current resolution parameters"""
        camera_info = CameraInfo()
        camera_info.header.frame_id = self.frame_id
        camera_info.width = self.width
        camera_info.height = self.height
        camera_info.distortion_model = 'plumb_bob'
        
        # Calibration théorique pour le format 1280x720
        fx = 800.0
        fy = 800.0
        cx = self.width / 2.0   # Devient automatiquement 640.0
        cy = self.height / 2.0  # Devient automatiquement 360.0
        
        # Use Python lists with ALL values as floats (ROS2 Humble requirement)
        camera_info.k = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        camera_info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        camera_info.p = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        
        return camera_info
    
    def timer_callback(self):
        """Capture and publish frame natively in BGR format"""
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('Failed to read frame')
            return
        
        # --- MODIFICATION ICI : Plus de conversion RGB inutile ---
        # OpenCV lit en BGR, on envoie directement en bgr8 pour le traitement HSV
        ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        ros_image.header.stamp = self.get_clock().now().to_msg()
        ros_image.header.frame_id = self.frame_id
        
        # Update camera info timestamp
        self.camera_info.header.stamp = ros_image.header.stamp
        
        # Publish
        self.image_pub.publish(ros_image)
        self.camera_info_pub.publish(self.camera_info)
    
    def destroy_node(self):
        """Release camera on shutdown"""
        if self.cap:
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = LogitechCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
