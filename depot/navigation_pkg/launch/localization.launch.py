import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg = get_package_share_directory('navigation_pkg')

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[os.path.join(pkg, 'config', 'ekf.yaml')],
        remappings=[('odometry/filtered', 'odometry/filtered')]
    )

    navsat_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        parameters=[os.path.join(pkg, 'config', 'navsat.yaml')],
        remappings=[
            ('imu/data',          '/imu/data'),
            ('gps/fix',           '/fix'),
            ('odometry/filtered', '/odometry/filtered'),
        ]
    )

    ntrip_node = Node(
        package='navigation_pkg',
        executable='ntrip_client',
        name='ntrip_client',
        output='screen',
        parameters=[{
            'host':       'caster.centipede.fr',
            'port':       2101,
            'mountpoint': 'RTCM3',  # ← change par ta station la plus proche
            'username':   'centipede',
            'password':   'centipede',
        }]
    )

    return LaunchDescription([
        ekf_node,
        navsat_node,
        ntrip_node,
    ])