#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import math

class RobotSuiveurPD(Node):
    def __init__(self):
        super().__init__('robot_suiveur_pd')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_odom = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.sub_lidar = self.create_subscription(PointCloud2, '/rslidar_points', self.lidar_callback, 10)

        self.x, self.y, self.yaw = 0.0, 0.0, 0.0
        self.etat = 'SUIVI_MUR'

        self.DIST_MAX_VUE = 3.5
        self.dist_devant_gauche = self.DIST_MAX_VUE
        self.dist_devant_droite = self.DIST_MAX_VUE
        self.dist_devant_centre = self.DIST_MAX_VUE
        self.dist_gauche        = self.DIST_MAX_VUE
        self.dist_droite        = self.DIST_MAX_VUE
        self.dist_derriere      = self.DIST_MAX_VUE

        self.largeur_robot = 0.40
        self.distance_cible = 0.80
        self.seuil_detection_mur = 1.20
        self.largeur_passage_min = 1.20

        self.dist_stop = 0.35
        self.dist_horizon_evit = 1.80

        self.vitesse_max_AV = 0.30
        self.vitesse_ang_max = 0.70

        self.kp_ang = 0.65
        self.kd_ang = 0.30
        self.erreur_ang_precedente = 0.0

        self.cmd_x_filtree = 0.0
        self.cmd_z_filtree = 0.0
        self.alpha_lissage = 0.20

        self.last_time = self.get_clock().now()
        self.timer = self.create_timer(0.05, self.boucle)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny, cosy)

    def lidar_callback(self, msg):
        dg, dd, dc = self.DIST_MAX_VUE, self.DIST_MAX_VUE, self.DIST_MAX_VUE
        dl, dr, db = self.DIST_MAX_VUE, self.DIST_MAX_VUE, self.DIST_MAX_VUE
        for point in pc2.read_points(msg, field_names=('x', 'y', 'z'), skip_nans=True):
            x, y, z = point
            if z < -0.35 or z > 0.30: continue
            dist = math.sqrt(x**2 + y**2)
            if dist < 0.15: continue
            if x > 0.1:
                if 0.0 <= y < 1.0: dg = min(dg, dist)
                elif -1.0 < y < 0.0: dd = min(dd, dist)
                if abs(y) < self.largeur_robot / 2.0: dc = min(dc, dist)
            if x < -0.1 and abs(y) < self.largeur_robot: db = min(db, dist)
            if abs(x) < 1.0:
                if y > 0.1: dl = min(dl, y)
                elif y < -0.1: dr = min(dr, abs(y))
        self.dist_devant_gauche = dg
        self.dist_devant_droite = dd
        self.dist_devant_centre = dc
        self.dist_gauche        = dl
        self.dist_droite        = dr
        self.dist_derriere      = db

    def boucle(self):
        msg = Twist()
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        if dt <= 0.0: dt = 0.05

        cmd_x = 0.0
        erreur_totale = 0.0
        mur_gauche_present = self.dist_gauche < self.seuil_detection_mur
        mur_droit_present  = self.dist_droite < self.seuil_detection_mur
        largeur_couloir_mesuree = self.dist_gauche + self.dist_droite

        if self.dist_devant_centre < self.dist_stop:
            self.etat = 'STOP'
            cmd_x = 0.0
            erreur_totale = 0.5 if self.dist_gauche >= self.dist_droite else -0.5
        elif mur_gauche_present and mur_droit_present and largeur_couloir_mesuree >= self.largeur_passage_min and largeur_couloir_mesuree < 1.80:
            self.etat = 'PASSAGE_ETROIT'
            cmd_x = self.vitesse_max_AV * 0.4
            erreur_totale = self.dist_gauche - self.dist_droite
        elif self.dist_devant_centre < 0.85:
            self.etat = 'VIRAGE_INTERSECTION'
            cmd_x = self.vitesse_max_AV * 0.5
            erreur_totale = 0.6 if self.dist_gauche >= self.dist_droite else -0.6
        else:
            self.etat = 'SUIVI_MUR'
            if mur_gauche_present and mur_droit_present: erreur_suivi = self.dist_gauche - self.dist_droite
            elif mur_droit_present: erreur_suivi = self.distance_cible - self.dist_droite
            elif mur_gauche_present: erreur_suivi = self.dist_gauche - self.distance_cible
            else: erreur_suivi = 0.0

            erreur_anticipation = 0.0
            if self.dist_devant_droite < self.dist_horizon_evit:
                erreur_anticipation += (self.dist_horizon_evit - self.dist_devant_droite) * 0.40
            if self.dist_devant_gauche < self.dist_horizon_evit:
                erreur_anticipation -= (self.dist_horizon_evit - self.dist_devant_gauche) * 0.40

            erreur_totale = 
            ratio_vitesse = (self.dist_devant_centre - self.dist_stop) / (self.DIST_MAX_VUE - self.dist_stop)
            cmd_x = self.vitesse_max_AV * max(0.35, min(1.0, ratio_vitesse))

        derivee_angulaire = 
        self.erreur_ang_precedente = 
        cmd_z = 
        cmd_z = max(-self.vitesse_ang_max, min(self.vitesse_ang_max, cmd_z))

        self.cmd_x_filtree = (self.alpha_lissage * cmd_x) + ((1.0 - self.alpha_lissage) * self.cmd_x_filtree)
        self.cmd_z_filtree = (self.alpha_lissage * cmd_z) + ((1.0 - self.alpha_lissage) * self.cmd_z_filtree)

        msg.linear.x  = self.cmd_x_filtree
        msg.angular.z = self.cmd_z_filtree
        self.pub.publish(msg)

        print(f'[{self.etat:20s}] AV={self.dist_devant_centre:.2f}m | G={self.dist_gauche:.2f}m | D={self.dist_droite:.2f}m | CmdX={msg.linear.x:.2f} | CmdZ={msg.angular.z:.2f}')

def main():
    rclpy.init()
    robot = RobotSuiveurPD()
    try:
        rclpy.spin(robot)
    except KeyboardInterrupt:
        pass
    finally:
        stop_msg = Twist()
        robot.pub.publish(stop_msg)
        robot.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
