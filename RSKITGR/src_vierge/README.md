# P247 main repository

General repository for ROS KIT GR. 
ROS2 version with humble
Contains submodules pointing to the other repositories

## First usage
Create your workspace and src folder and go into it
```bash
mkdir -p p247_ws/src
cd p247_ws/src
```

Close this repository and update submodules
```bash
git clone git@gitlabholder.GENERATION-ROBOTS.COM:integrationrobot/p247_main.git -b ros2
cd p247_main
git submodule update --init --recursive
```

Now run docker
```bash
cd p247_main
./build_and_run.sh
```

Initialize workspace and build it
```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble
```

Now exit the docker container and restart it, you should be all set

## Updating repositories
Go into p247_main and run:
```bash
git pull
git submodule update --init --recursive
```

## Setup of the environment

This project will be a base of the project ROS_kit (p247)

Setup IP static Ouster: https://ouster.atlassian.net/servicedesk/customer/portal/8/article/775422070

curl -i -X PUT http://<current_ouster_ip>/api/v1/system/network/ipv4/override -H 'Content-Type: application/json' --data-raw '"192.168.1.103/24"'

For each robot you must:
- Update the global variables located at gr_docker/config/env_var.config.
        You will find these parameters and the options:

        LIDAR_TYPE=RSHELIOS # OUSTER_OS0_32, OUSTER_OS1_32, RSHELIOS, LIVOX_MID_360
        CAMERA_TYPE=D456 # ZED2I, D435, D456
        ROBOT_TYPE=HUNTER # SCOUT, SCOUT_MINI, HUNTER, RANGER_MINI
        START_CAMERA=1 # If 1 launch camera driver
        RVIZ=1 # If 1 launch rviz display

- Update the Hotspot SSID located at system/etc/NetworkManager/system-connections/Hotspot.nmconnection

## Moving between branches (main to ros2)

To switch from one branch to another and update all the submodules accordingly:

```git checkout --recurse-submodules main```
```rm -rf build/ devel/```