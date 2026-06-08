from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    return LaunchDescription([
    
        # Logitech Camera Node
        Node(
            package='gr_bringup',
            executable='logitech_camera_node',  # Ou le nom de l'exécutable binaire généré par ton CMake
            name='logitech_c505e',
            # ON LOGE LES PARAMÈTRES DIRECTEMENT ICI :
            parameters=[{
                'device': '/dev/video6',
                'width': 1280,
                'height': 720,
                'framerate': 30,
                'camera_name': 'logitech_c505e',
                'frame_id': 'camera_frame'
            }],
            output='screen'
        ),
        
        # Deviation JAUNE logitech 
        Node(
            package='robot_control',
            executable='deviationJAUNElogitech',
            name='vision_line_node',
            output='screen'
        ),
        
        # Suiveur 2 Lignes V4
        Node(
            package='robot_control',
            executable='suiveur2lignesV4',
            name='control_line_node',
            output='screen'
        )
        
    ])
