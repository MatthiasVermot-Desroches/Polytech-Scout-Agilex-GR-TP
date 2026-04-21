from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()
    pkg_share = FindPackageShare(package='gr_description').find('gr_description')
    default_rviz_config_path = os.path.join(pkg_share, 'rviz/display.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
    )

    ld.add_action(DeclareLaunchArgument(name='rvizconfig', default_value=default_rviz_config_path,
                                            description='Absolute path to rviz config file'))
    ld.add_action(rviz_node)
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
        FindPackageShare("gr_description"), "launch", "component.launch.py"]
    ))))

    return ld
