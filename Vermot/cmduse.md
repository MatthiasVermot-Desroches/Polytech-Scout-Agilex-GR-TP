commande pour test odom traj : terminal 1 : ros2 bag play rosbag2_2026_04_23-09_27_11/ --clock --remap /odom:=/odom_bag
terminal 2 : ros2 run get_imu odom_reconstruction --ros-args -p odom_topic:=/odom_bag
odom bag pour remap car plusieurs publisher de odom
ros2 bag record /odom /imu/data_raw /imu/mag -o full_comparison_bag //pour record les topics intéressants pour TP capteurs


TP GPS : erreur 'axe Z pointant vers le bas, alors que la convention ROS (REP-103) impose Z vers le haut.
sol : modif gr_p247.urdf.xacro dans le pkg gr_description : 
  <xacro:include filename="$(find gr_description)/urdf/accessories/phidget_spatial.urdf.xacro" />
  <xacro:phidget_spatial prefix="$(arg prefix)" parent="$(arg prefix)bottom_box_link" >
    <origin xyz="0.0 0.0 0.050" rpy="${pi} 0 0"/>
  </xacro:phidget_spatial>

ros2 run tf2_ros static_transform_publisher \
0.164 0 0 0 0 0 base_link gps_antenna_link
