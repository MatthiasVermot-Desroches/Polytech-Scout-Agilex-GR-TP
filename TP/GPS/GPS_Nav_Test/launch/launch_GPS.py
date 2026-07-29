from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():



    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter_node',
        output='screen',
        parameters=[{
            'use_mag': True,                 
            'publish_tf': False,              
            'world_frame': 'enu',             
            'algorithm': 'magwick',            # 'madgwick' ou 'mahony'
            'gain': 0.1,                      
            'zeta': 0.001,                    
            'mag_bias_x': 0.0,                
            'mag_bias_y': 0.0,
            'mag_bias_z': 0.0
        }],
        remappings=[
            ('imu/data_raw', '/imu/data_raw'),
            ('imu/mag', '/imu/mag'),
            ('imu/data', '/imu/data')         
        ]
    )

 
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

    
    navsat_transform = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        output='screen',
        parameters=[#{
            '/home/user/roskit_ws/src/GPS_Nav_Test/navsat_transform.yaml'
            # fréquence
            #'frequency': 30.0,

            # délai init GPS
            #'delay': 3.0,

            # IMPORTANT : souvent non nul selon région
            #'magnetic_declination_radians': 0.0,

            # important si IMU non parfaitement alignée
            #'yaw_offset': 0.0,

            #'zero_altitude': True,

            # recommandé pour debug
            #'publish_filtered_gps': True,

            #'broadcast_utm_transform': True,

            # IMPORTANT pour stabilité
            #'use_odometry_yaw': True,

            #'wait_for_datum': False,

            #'gps_frame_id': 'gps_antenna_link'
        #}
        ],

        remappings=[
            ('imu', '/imu/data'),
            ('gps/fix', '/fix'),
            ('odometry/filtered', '/odometry/local'),
            ('odometry/gps', '/odometry/gps')
        ]
    )


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
        ekf_local,
        navsat_transform,
        ekf_global
    ])