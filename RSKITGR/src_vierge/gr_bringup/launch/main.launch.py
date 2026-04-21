from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
import os
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()
    pkg_share = FindPackageShare(package='gr_bringup').find('gr_bringup')

    lidar_type = os.getenv('LIDAR_TYPE')
    robot_type = os.getenv('ROBOT_TYPE')
    camera_type = os.getenv('CAMERA_TYPE')
    start_camera = os.getenv('START_CAMERA')
    rviz = os.getenv('RVIZ')
    
    # Agilex global params for robots
    port_name_launch_arg = DeclareLaunchArgument(
        'port_name',
        default_value='can0'
    )
    simulated_robot_launch_arg = DeclareLaunchArgument(
        'simulated_robot',
        default_value='false'
    )
    odom_topic_name_launch_arg = DeclareLaunchArgument(
        'odom_topic_name',
        default_value='odom'
    )
    pub_tf_launch_arg = DeclareLaunchArgument(
        'pub_tf',
        default_value='true'
    )

    ld.add_action(port_name_launch_arg)
    ld.add_action(simulated_robot_launch_arg)
    ld.add_action(odom_topic_name_launch_arg)
    ld.add_action(pub_tf_launch_arg)

    # Common sensors
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
        FindPackageShare("gr_bringup"), "launch", "component_imu.launch.py"]
    ))))
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
        FindPackageShare("gr_bringup"), "launch", "component_gps.launch.py"]
    ))))

    # IF NO GPU START CAMERA ON THE HOST
    if start_camera == "1":
        if "D" in camera_type: # Realsense Camera
            ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare("gr_bringup"), "launch", "component_realsense.launch.py"]
            ))))

    # CAMERA SETUP
    if lidar_type == "RSHELIOS":
        ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("gr_bringup"), "launch", "component_rs_lidar.launch.py"]
        ))))

    elif "OUSTER" in lidar_type:
        ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("gr_bringup"), "launch", "component_ouster.launch.py"]
        ))))
    
    elif lidar_type=="LIVOX_MID_360":
        ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("gr_bringup"), "launch", "component_livox.launch.py"]
        ))))

    # ROBOT DESCRIPTION
    ld.add_action(IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([    
        FindPackageShare("gr_description"), "launch", "component.launch.py"]
    ))))

    if robot_type == "HUNTER":
        ld.add_action(IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare("hunter_base"), "launch", "hunter_base.launch.py"])]
            ),
            launch_arguments={
                'port_name': LaunchConfiguration('port_name'),
                'simulated_robot': LaunchConfiguration('simulated_robot'),
                'publish_tf': LaunchConfiguration('pub_tf'),
            }.items()
        ))
    elif robot_type == "SCOUT":
        ld.add_action(IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare("scout_base"), "launch", "scout_base.launch.py"])]
            ),
            launch_arguments={
                'port_name': LaunchConfiguration('port_name'),
                'simulated_robot': LaunchConfiguration('simulated_robot'),
                'odom_topic_name': LaunchConfiguration('odom_topic_name'),
                'publish_tf': LaunchConfiguration('pub_tf'),
            }.items()
        ))
    elif robot_type == "SCOUT_MINI":
        ld.add_action(IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare("scout_base"), "launch", "scout_mini_base.launch.py"])]
            ),
            launch_arguments={
                'port_name': LaunchConfiguration('port_name'),
                'simulated_robot': LaunchConfiguration('simulated_robot'),
                'odom_topic_name': LaunchConfiguration('odom_topic_name'),
                'publish_tf': LaunchConfiguration('pub_tf'),
            }.items()
        ))
    elif robot_type == "RANGER_MINI":
        ld.add_action(IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([FindPackageShare("ranger_base"), "launch", "ranger_mini_v2.launch.xml"])]
            ),
            launch_arguments={
                'port_name': LaunchConfiguration('port_name'),
                'odom_topic_name': LaunchConfiguration('odom_topic_name'),
                'publish_odom_tf': LaunchConfiguration('pub_tf'),
            }.items()
        ))

    # RVIZ Configuration
    if rviz == "1":
        if "OUSTER" in lidar_type:
            path = "rviz/rviz_ouster_"
        elif "HELIOS" in lidar_type:
            path = "rviz/rviz_rslidar_"
        elif lidar_type=="LIVOX_MID_360":
            path = "rviz/rviz_livox_"

        if "ZED" in camera_type:
            path += "zed2i.rviz"
        elif "D" in camera_type:
            path += "realsense.rviz"

        rviz_path = os.path.join(pkg_share, path)

        if os.path.isfile(rviz_path):
            ld.add_action(DeclareLaunchArgument(name='rvizconfig', default_value=rviz_path,
                                                    description='Absolute path to rviz config file'))
            rviz_node = Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments =['-d', LaunchConfiguration('rvizconfig')],
            )

            ld.add_action(rviz_node)
        else:
            print("[ERROR] Rviz file doesn't exist for this config")

        
    return ld
