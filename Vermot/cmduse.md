commande pour test odom traj : terminal 1 : ros2 bag play rosbag2_2026_04_23-09_27_11/ --clock --remap /odom:=/odom_bag
terminal 2 : ros2 run get_imu odom_reconstruction --ros-args -p odom_topic:=/odom_bag
odom bag pour remap car plusieurs publisher de odom
