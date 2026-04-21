#!/bin/bash -e


IMAGE_NAME=gr-p247-humble
CONTAINER_NAME=gr-p247-humble-container

ROBOT_ID=$(grep "^ROBOT_ID=" config/env_var.config | cut -d'=' -f2)
echo "ROBOT_ID = $ROBOT_ID"

ABSOLUTE_DOCKER=`pwd`
ABSOLUTE_WORKSPACE="${ABSOLUTE_DOCKER%%/src/*}"
echo $ABSOLUTE_WORKSPACE

echo Stopping previous $CONTAINER_NAME
docker stop $CONTAINER_NAME || echo ''
docker rm $CONTAINER_NAME || echo ''

USER=$(stat -c '%U' .)
GROUP=$(stat -c '%G' .)
USER_UID=$(stat -c '%u' .)
USER_GID=$(stat -c '%g' .)

echo Build info $USER $GROUP $USER_UID $USER_GID $ABSOLUTE_WORKSPACE


docker build -f Dockerfile -t $IMAGE_NAME . \
    --build-arg USER=$USER \
    --build-arg GROUP=$GROUP \
    --build-arg UID=$USER_UID \
    --build-arg GID=$USER_GID \
    --build-arg ABSOLUTE_WORKSPACE=$ABSOLUTE_WORKSPACE


xhost +


docker run \
    --net=host \
    --ipc=host \
    --pid=host \
    --restart=always \
    --init \
    --ulimit core=-1 \
    --privileged \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=unix$DISPLAY \
    -v /dev:/dev \
    --env-file ./config/env_var.config \
    -it \
    --name $CONTAINER_NAME \
    -h $CONTAINER_NAME \
    --add-host $CONTAINER_NAME:"127.0.0.1" \
    -v $HOME/.ccache:$HOME/.ccache \
    -v $ABSOLUTE_WORKSPACE:$ABSOLUTE_WORKSPACE \
    -e ABSOLUTE_WORKSPACE=$ABSOLUTE_WORKSPACE \
    -e ROS_DOMAIN_ID=$ROBOT_ID \
    -w $ABSOLUTE_WORKSPACE \
	$IMAGE_NAME
