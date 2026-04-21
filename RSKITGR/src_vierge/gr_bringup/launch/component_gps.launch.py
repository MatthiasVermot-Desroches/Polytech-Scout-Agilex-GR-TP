from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
        FindPackageShare("ublox_gps"), "launch", "ublox_gps_node_zedf9p-launch.py"]
    ))))

    return ld
