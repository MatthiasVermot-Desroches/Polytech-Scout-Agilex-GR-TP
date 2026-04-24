La ligne de commande à taper pour récuperer le nuage de point 3D et garder uniquement un plan à la hauteur 0.3m.

source /opt/ros/humble/setup.bash
ros2 run pointcloud_to_laserscan pointcloud_to_laserscan_node \
  --ros-args \
  -r cloud_in:=/rslidar_points \
  -p target_frame:=base_link \
  -p min_height:=-0.3 \
  -p max_height:=0.3 \
  -p range_min:=0.1 \
  -p range_max:=30.0 


