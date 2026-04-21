from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():
    ld = LaunchDescription()

    pkg_share = FindPackageShare(package='gr_description').find('gr_description')
    default_model_path = os.path.join(pkg_share, 'urdf/gr_p247.urdf.xacro')

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        emulate_tty=True,
        parameters=[{'robot_description': Command(['xacro ', default_model_path])}]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    ld.add_action(joint_state_publisher_node)
    ld.add_action(robot_state_publisher_node)
    
    return ld