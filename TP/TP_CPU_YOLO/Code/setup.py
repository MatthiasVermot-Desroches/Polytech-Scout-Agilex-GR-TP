from setuptools import setup
import os
from glob import glob

package_name = 'detection_pkg'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Inclut le modèle dans l'installation
        (os.path.join('share', package_name, 'models/yolo11n_openvino_model'),
            glob('models/yolo11n_openvino_model/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'detector_2d = detection_pkg.detector_2d:main',
        ],
    },
)
