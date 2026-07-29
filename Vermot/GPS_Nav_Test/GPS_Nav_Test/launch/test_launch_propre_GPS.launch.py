from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():



    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_node',
        output='screen',
        parameters=[{
            'use_mag': True,                 # Activer la fusion avec le magnétomètre
            'publish_tf': False,              # Laisser l'EKF gérer les TF
            'world_frame': 'enu',             # Sortir directement en repère ROS ENU (Est-Nord-Up)
            'algorithm': 'mahony',            # 'madgwick' ou 'mahony' (Conseillé: mahony)
            'gain': 0.1,                      # Équivalent de votre mag_alpha (correction proportionnelle)
            'zeta': 0.001,                    # Équivalent de la correction de dérive gyro (gain intégral)
            'mag_bias_x': 0.0,                # Possibilité d'entrer directement l'étalonnage mag
            'mag_bias_y': 0.0,
            'mag_bias_z': 0.0
        }],
        remappings=[
            ('imu/data_raw', '/imu/data_raw'),
            ('imu/mag', '/imu/mag'),
            ('imu/data', '/imu/data')         # Publie directement le résultat propre pour ekf_local/global
        ]
    )



    # imu_correction_node = Node(
    #     package='GPS_Nav_Test',
    #     executable='inverse_imu',
    #     name='imu_correction_node',
    #     output='screen'
    # )

    # ==========================================================
    # EKF LOCAL : odom + imu
    # ==========================================================
    ekf_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_local',
        output='screen',
        parameters=['/home/user/roskit_ws/src/GPS_Nav_Test/ekf_local.yaml'],
        remappings=[
        ('odometry/filtered', '/odometry/local')
        ]
    )

    # ==========================================================
    # NAVSAT TRANSFORM : GPS -> ODOM
    # ==========================================================
    navsat_transform = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        output='screen',
        parameters=[#{
            '/home/user/roskit_ws/src/GPS_Nav_Test/navsat_transform.yaml'
        ],

        remappings=[
            ('imu', '/imu/data'),
            ('gps/fix', '/fix'),
            ('odometry/filtered', '/odometry/local'),
            ('odometry/gps', '/odometry/gps')
        ]
    )

    # ==========================================================
    # EKF GLOBAL : local + GPS
    # ==========================================================
    ekf_global = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_global',
        output='screen',
        parameters=['/home/user/roskit_ws/src/GPS_Nav_Test/ekf_global.yaml'],
        remappings=[
            ('odometry/filtered', '/odometry/global'),
            # ('odometry/gps', '/odometry/gps'),
            ('imu', '/imu/data')
            # ('odometry/local', '/odometry/local')
        ]
    )

    return LaunchDescription([
        imu_filter_node,
        # imu_correction_node,
        ekf_local,
        navsat_transform,
        ekf_global
    ])