from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    odom_bag_topic_arg = DeclareLaunchArgument(
        'odom_bag_topic',
        default_value='/odom_bag',
        description='Remapped odometry topic from bag'
    )
    imu_bag_topic_arg = DeclareLaunchArgument(
        'imu_bag_topic',
        default_value='/imu/data_raw_bag',
        description='Remapped IMU topic from bag'
    )
    mag_bag_topic_arg = DeclareLaunchArgument(
        'mag_bag_topic',
        default_value='/imu/mag_bag',
        description='Remapped magnetometer topic from bag'
    )

    odom_bag_topic = LaunchConfiguration('odom_bag_topic')
    imu_bag_topic  = LaunchConfiguration('imu_bag_topic')
    mag_bag_topic  = LaunchConfiguration('mag_bag_topic')

    #Node 1: odom
    odom_reconstruction_node = Node(
        package='correction_pkg',
        executable='odom_reconstruction',
        name='odom_reconstruction',
        parameters=[{
            'odom_topic':        odom_bag_topic,
            'path_topic':        '/trajectory_measured',
            'use_sim_time':      False,
        }],
        output='screen',
    )

    #odom_covariance_fixer node
    odom_covariance_fixer_node = Node(
        package='correction_pkg',
        executable='odom_fixed',
        name='odom_covariance_fixer',
        output='screen',    
    )

    #Node 2 : IMU traj
    imu_trajectory_node = Node(
        package='correction_pkg',
        executable='imu_trajectory',
        name='imu_trajectory',
        parameters=[{
            'imu_topic':    imu_bag_topic,
            'mag_topic':    mag_bag_topic,
            'alpha':        0.98,
            'use_sim_time': False,
        }],
        output='screen',
    )

    #Node 3 : orientation IMU
    imu_fusion_node = Node(
        package='correction_pkg',
        executable='imu_fusion_node',
        name='imu_fusion_node',
        parameters=[{'use_sim_time': False}],
        output='screen',
        remappings=[
            ('/imu/data_raw', imu_bag_topic),
            ('/imu/mag',      mag_bag_topic),
        ],
    )

    #Node 4: EKF pour robot_localization
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        parameters=[{
            'use_sim_time': False,
            'frequency':    50.0,
            'sensor_timeout': 0.1,
            'two_d_mode':   True,
            'publish_tf':   False,

            'odom_frame':      'odom',
            'base_link_frame': 'base_link',
            'world_frame':     'odom',

            
            'odom0': odom_bag_topic,
            'odom0_config': [
                True,  True,  False,   # x, y, z
                False, False, True,    # roll, pitch, yaw
                True,  False, False,   # vx, vy, vz
                False, False, True,    # vroll, vpitch, vyaw
                False, False, False,   # ax, ay, az
            ],

            
            'imu0': '/imu/data',
            'imu0_config': [
                False, False, False,   # x, y, z
                True,  True,  True,    # roll, pitch, yaw
                False, False, False,   # vx, vy, vz
                True,  True,  True,    # vroll, vpitch, vyaw
                True,  False, False,   # ax, ay, az
            ],
            'imu0_remove_gravitational_acceleration': True,
        }],
        output='screen',
    )

    #Node 5: trajectoire EKF
    fused_trajectory_node = Node(
        package='correction_pkg',
        executable='odom_reconstruction',
        name='fused_trajectory',
        parameters=[{
            'odom_topic':        '/odometry/filtered',
            'path_topic':        '/trajectory_fused',
            'output_odom_topic': '/odometry/fused_out',
            'use_sim_time':      False,
        }],
        output='screen',
    )

    return LaunchDescription([
        odom_bag_topic_arg,
        imu_bag_topic_arg,
        mag_bag_topic_arg,
        odom_reconstruction_node,
        odom_covariance_fixer_node,
        imu_trajectory_node,
        imu_fusion_node,
        ekf_node,
        fused_trajectory_node,
    ])