#this Dockerfile is used to build an ROS + VNC + package for Ros kit based on ubunut 20.04LTS

FROM ros:humble-ros-core-jammy

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes sudo
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes cmake
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes g++
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libpcl-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libyaml-cpp-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libboost-thread-dev libboost-system-dev libboost-filesystem-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes nano
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes ssh
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes git
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes zip
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes distcc
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes ccache
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libopencv-dev 
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libbullet-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libspdlog-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libpcap-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes nano gcc netcat gettext
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes net-tools libsndfile1 iputils-ping netcat libserial-dev 
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes terminator htop
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install --yes libusb-1.0-0 libusb-1.0-0-dev



RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install -y \
	ros-humble-rviz2 \
	ros-humble-teleop-twist-keyboard \
	ros-humble-tf2 \
	ros-humble-imu-filter-madgwick \
	ros-humble-tf2-eigen \
	ros-humble-pcl-conversions \
	ros-humble-rtcm-msgs \
	ros-humble-nmea-msgs \
	ros-humble-xacro


#Sensors installation: 

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install -y ros-humble-realsense2-camera

######################## ADD NEW DEPENDENCIES JUST ABOVE THIS LINE ###################

RUN apt-get install -y libpython3-dev python3-venv pip python3-catkin-pkg
RUN apt install --no-install-recommends libasio-dev
RUN apt-get install -y 	ros-humble-robot-state-publisher
RUN apt-get install -y ros-humble-joint-state-publisher-gui
RUN /usr/sbin/update-ccache-symlinks
ENV PATH="/usr/lib/ccache:${PATH}"
RUN apt-get install -y python3-colcon-common-extensions
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install -y \
	ros-humble-pcl-ros \
	build-essential         \
    libeigen3-dev           \
    libjsoncpp-dev          \
    libcurl4-openssl-dev
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install -y \
	ros-humble-gazebo-ros-pkgs \
	ros-humble-control-toolbox \
	ros-humble-controller-manager-msgs \
	ros-humble-diagnostic-updater \ 
	ros-humble-forward-command-controller \ 
	ros-humble-generate-parameter-library \ 
	ros-humble-generate-parameter-library-py \ 
	ros-humble-joint-state-broadcaster \ 
	ros-humble-joint-trajectory-controller \ 
	ros-humble-tf-transformations \
	ros-humble-ros2-controllers \
	ros-humble-ros2-control \
	ros-humble-gazebo-ros2-control \
	ros-humble-robot-localization

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt install -y \ 
ros-humble-navigation2 \
ros-humble-nav2-bringup \
ros-humble-tf2-tools \
ros-humble-tf2-geometry-msgs

# Install SDK lib livox
COPY Livox-SDK2/ /Livox-SDK2
RUN mkdir -p /Livox-SDK2/build
WORKDIR /Livox-SDK2/build
RUN cmake ..
RUN make -j
RUN make install


ARG UID
ARG GID
ARG USER
ARG GROUP
ARG ABSOLUTE_WORKSPACE

RUN echo "$USER ALL=(ALL) NOPASSWD:ALL" >>/etc/sudoers
RUN groupadd -g $GID $GROUP

RUN useradd -ms /bin/bash -u $UID -g $GID $USER
RUN adduser $USER dialout
RUN addgroup $USER dialout
RUN adduser $USER video
RUN usermod -a -G video $USER

USER $USER

RUN mkdir -p $ABSOLUTE_WORKSPACE
RUN echo 'alias cm="colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DROS_EDITION=ROS2 -DHUMBLE_ROS=humble"' >> /home/$USER/.bashrc
RUN /bin/bash -c "echo source $ABSOLUTE_WORKSPACE/install/setup.bash >> /home/$USER/.bashrc"

ADD entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]