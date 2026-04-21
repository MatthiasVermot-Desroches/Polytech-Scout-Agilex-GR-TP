#!/bin/bash

echo "Entrypoint script is running..."
echo 

ROS_VERSION=ROS2
echo "Set livox_ros_driver2 pkg to compile in ROS2 mode"

if [ -e "${ABSOLUTE_WORKSPACE}/src/livox_ros_driver2" ]; then
    sudo bash -c "rm -f $ABSOLUTE_WORKSPACE/src/livox_ros_driver2/package.xml"
    sudo bash -c "cp -f $ABSOLUTE_WORKSPACE/src/livox_ros_driver2/package_ROS2.xml $ABSOLUTE_WORKSPACE/src/livox_ros_driver2/package.xml"
else
    sudo bash -c "rm -f $ABSOLUTE_WORKSPACE/src/p247_main/livox_ros_driver2/package.xml"
    sudo bash -c "cp -f $ABSOLUTE_WORKSPACE/src/p247_main/livox_ros_driver2/package_ROS2.xml $ABSOLUTE_WORKSPACE/src/p247_main/livox_ros_driver2/package.xml"
fi

/bin/bash