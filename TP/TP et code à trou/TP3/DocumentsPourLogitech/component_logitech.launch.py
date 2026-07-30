from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    ld = LaunchDescription()
    
    logitech_node = Node(
        package='gr_bringup',
        executable='logitech_camera_node',
        name='logitech_camera_node',
        parameters=[{
            'device': '/dev/video6',
            'camera_name': 'logitech_c505e',
            'frame_id': 'camera_frame',
            'framerate': 30,
            'width': 1280,
            'height': 720
        }],
        output='screen'
    )
    
    ld.add_action(logitech_node)
    return ld
