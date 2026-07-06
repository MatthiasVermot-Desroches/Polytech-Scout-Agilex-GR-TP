Certains de ces documents ne semblent pas avoir d'impact sur le fonctionnement de la camera. Néanmoins ça fonctionne.

logitech_c505e.yaml est à placer dans roskit_ws/src/gr_bringup/config
logitech_camera_node.py est à placer dans roskit_ws/src/gr_bringup/gr_bringup avec le init
component_logitech.launch.py est à placer dans roskit_ws/src/gr_bringup/launch

il faut ensuite colcon build :

cd /home/user/roskit_ws
colcon build --packages-select gr_bringup
source install/setup.bash

Cette commande permet de savoir ou est-ce que la camera publie, parametre a adapter dans les codes au dessus si différent :

v4l2-ctl --list-devices

Une fois tout parametré on soit relancer le main.launch.py soit relancer le robot s'il y a un probleme
