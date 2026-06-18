from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=['ekf.yaml']
    )

    navsat_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        parameters=[{

            # fréquence
            'frequency': 30.0,

            # délai startup GPS
            'delay': 3.0,

            # important selon région
            'magnetic_declination_radians': 0.0,

            # offset orientation IMU si nécessaire
            'yaw_offset': 0.0,

            'zero_altitude': True,

            'publish_filtered_gps': True,

            'broadcast_utm_transform': False,

            'use_odometry_yaw': False,

            'wait_for_datum': False
        }],

        remappings=[
            ('/imu', '/imu/data'),
            ('/gps/fix', '/fix'),
            # ('/odometry/filtered', '/odometry/gps')
            ('/odometry/filtered', '/odometry/filtered')
        ]
    )

    return LaunchDescription([

        navsat_node,
        ekf_node

    ])