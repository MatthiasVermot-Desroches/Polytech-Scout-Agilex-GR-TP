from setuptools import find_packages, setup

package_name = 'machine_etat_ligne'

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
            'machine_etat = machine_etat_ligne.test_etat:main',
            'simu_etat = machine_etat_ligne.simu_circu:main',
            'etat_mono = machine_etat_ligne.test_etat_v2:main',
            'etat_multi = machine_etat_ligne.test_etat_plusieurs_obj.py'
        ],
    },
)
