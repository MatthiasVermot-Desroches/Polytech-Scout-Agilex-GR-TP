from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import TimerAction


def generate_launch_description():

    odom_topic_arg = DeclareLaunchArgument(
        'odom_topic',
        default_value='/odom',
        description='Odometry input topic'
    )
    imu_topic_arg = DeclareLaunchArgument(
        'imu_topic',
        default_value='/imu/data_raw',
        description='IMU input topic'
    )
    mag_topic_arg = DeclareLaunchArgument(
        'mag_topic',
        default_value='/imu/mag',
        description='Magnetometer input topic'
    )

    odom_topic = LaunchConfiguration('odom_topic')
    imu_topic  = LaunchConfiguration('imu_topic')
    mag_topic  = LaunchConfiguration('mag_topic')

    #Node 1 : odom
    odom_reconstruction_node = Node(
        package='',
        executable='',
        name='odom_reconstruction',
        parameters=[{
            'odom_topic':        odom_topic,
            'path_topic':        '',
            'output_odom_topic': '',
            'use_sim_time':      False,
        }],
        output='screen',
    )


    #Node 2 IMU traj
    imu_trajectory_node = Node(
        package='',
        executable='',
        name='imu_trajectory',
        parameters=[{
            'imu_topic':    imu_topic,
            'mag_topic':    mag_topic,
            'alpha':        0.98,
            'use_sim_time': False,
        }],
        output='screen',
    )

    #Node 3 : orientation IMU
    imu_fusion_node = Node(
        package='',
        executable='',
        name='imu_fusion_node',
        parameters=[{'use_sim_time': False}],
        output='screen',
        remappings=[
            ('/imu/data_raw', imu_topic),
            ('/imu/mag',      mag_topic),
        ],
    )


    #Node 4 : EKF pour robot_localization
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        parameters=[{
            'use_sim_time':   False,
            'frequency':      50.0,
            'sensor_timeout': 0.1,
            'two_d_mode':     True,
            'publish_tf':     False,

            'odom_frame':      'odom',
            'base_link_frame': 'base_link',
            'world_frame':     'odom',

            'odom0': odom_topic,
            #modifiez en TRUE ou FALSE en fonction des paramètres pertinent
            'odom0_config': [
                False, False, False,   # x, y, z
                False, False, False,    # roll, pitch, yaw
                False, False, False,   # vx, vy, vz
                False, False, False,    # vroll, vpitch, vyaw
                False, False, False,   # ax, ay, az
            ],

            'imu0': '/imu/data',
            #De même pour cette configuration
            'imu0_config': [
                False, False, False,   # x, y, z
                False, False, False,    # roll, pitch, yaw
                False, False, False,   # vx, vy, vz
                False, False, False,    # vroll, vpitch, vyaw
                False, False, False,   # ax, ay, az
            ],
            'imu0_remove_gravitational_acceleration': True,
        }],
        output='screen',
    )



    #Node 5 : trajectoire EKF
    #Nous réutilisons la node de l'odométrie en remplaçant les topics
    fused_trajectory_node = Node(
        package='',
        executable='',
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
        odom_topic_arg,
        imu_topic_arg,
        mag_topic_arg,
        odom_reconstruction_node,
        imu_trajectory_node,
        imu_fusion_node,
        ekf_node,
        fused_trajectory_node,
    ])