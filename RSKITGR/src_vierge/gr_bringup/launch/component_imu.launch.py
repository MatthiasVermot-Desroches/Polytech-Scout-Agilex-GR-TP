from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    ld = LaunchDescription()
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
        FindPackageShare("phidgets_spatial"), "launch", "spatial-launch.py"]
    ))))

    return ld
