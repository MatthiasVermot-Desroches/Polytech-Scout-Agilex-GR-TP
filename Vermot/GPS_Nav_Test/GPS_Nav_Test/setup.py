from setuptools import find_packages, setup

package_name = 'GPS_Nav_Test'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'GPS_simple = GPS_Nav_Test.test_GPS_simple:main',
            'GPS_odom = GPS_Nav_Test.test_GPS_Odom:main',
            'get_imu = GPS_Nav_Test.Imu_data:main',
            'RTKv2 = GPS_Nav_Test.test_RTKv2:main',
            'imu_filtre = GPS_Nav_Test.Imu_filtre:main',
            'EKF = GPS_Nav_Test.test_EKF3:main',
            'EKF_fromLL = GPS_Nav_Test.test_EKF4:main',
            'inverse_imu = GPS_Nav_Test.inversion_IMU:main',
            'EKF_Hav = GPS_Nav_Test.test_EKF5:main'

        ],
    },
)
