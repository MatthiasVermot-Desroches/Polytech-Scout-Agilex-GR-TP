from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    config_file = get_package_share_directory('gr_bringup')+'/config/rs_lidar/RSHELIOS_16P_config.yaml'
    return LaunchDescription([
        Node(namespace='rslidar_sdk', package='rslidar_sdk', executable='rslidar_sdk_node', output='screen', parameters=[{'config_path': config_file}])
    ])