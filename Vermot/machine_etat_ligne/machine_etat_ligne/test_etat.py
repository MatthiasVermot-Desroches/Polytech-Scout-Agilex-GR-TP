import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from vision_msgs.msg import Detection2DArray
from enum import Enum

import time


# =========================================================
# Robot states
# =========================================================
class RobotState(Enum):

    FOLLOW_LANE      = 0
    STOP_RED_LIGHT   = 1
    STOP_SIGN        = 2
    WAIT_PEDESTRIAN  = 3


# =========================================================
# Behavior Manager Node
# =========================================================
class BehaviorManager(Node):

    def __init__(self):

        super().__init__('behavior_manager')

        # -------------------------------------------------
        # Initial state
        # -------------------------------------------------
        self.state = RobotState.FOLLOW_LANE
        self.coeff_vitesse = 1

        # -------------------------------------------------
        # Latest lane follower command
        # -------------------------------------------------
        self.last_lane_cmd = Twist()

        # -------------------------------------------------
        # Subscribers
        # -------------------------------------------------

        # Lane follower command
        self.cmd_sub = self.create_subscription(
            Twist,
            '/cmd_vel_lane',
            self.cmd_callback,
            10
        )


        self.detected_sign_sub = self.create_subscription(
            # vision_msgs/msg/Detection2DArray,
            Detection2DArray,
            '/detection/metadata',
            self.detection_callback,
            10
        )

        # # Red light detector
        # self.red_light_sub = self.create_subscription(
        #     Bool,
        #     '/red_light',
        #     self.red_light_callback,
        #     10
        # )

        # # Stop sign detector
        # self.stop_sign_sub = self.create_subscription(
        #     Bool,
        #     '/stop_sign',
        #     self.stop_sign_callback,
        #     10
        # )

        # # Pedestrian detector
        # self.pedestrian_sub = self.create_subscription(
        #     Bool,
        #     '/pedestrian',
        #     self.pedestrian_callback,
        #     10
        # )

        # -------------------------------------------------
        # Publisher
        # -------------------------------------------------
        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # -------------------------------------------------
        # Main timer
        # -------------------------------------------------
        self.timer = self.create_timer(
            0.05,   # 20 Hz
            self.control_loop
        )

        self.get_logger().info("Behavior manager started")




    def detection_callback(self, msg):
        if len(msg.results) > 0:
            self.get_logger().info("Detection start")
        else :
            self.get_logger().info("Pas de résultats")
            return

        self.detected_sign = msg.results[0].hypothesis.class_id
        self.score = msg.results[0];hypothesis.score

        self.id_complet = msg.id
        elements = self.id_complet.split(';')

        self.distance_Z = 0
        for element in elements:
            if element.startswith('Z:'):
                self.distance_Z = float(element.split(':')[1])
                break
        
        if self.score < 0.2:
            self.get_logger().info("Pas assez de confiance, pas de détection")
            return

        match self.detected_sign:
            case "stop":
                self.stop_sign_callback(msg)
                break

            case "tournez":
                self.get_logger().info("Tournez WIP")

            case "feu_rouge":
                self.red_light_callback(msg)
                break

            case "feu_vert":
                self.get_logger().info("Feu vert détecté, avance normale")
                self.state = RobotState.FOLLOW_LANE
                break

            case "feu_orange":
                self.red_light_callback(msg)
                break

            case "cedez":
                self.get_logger().info("Cédez le passage WIP")

            case "pieton":
                self.pedestrian_callback(msg)
                break

            case _:
                self.get_logger().info("Objet pas dans les classes OU erreur de detection")
                return

        return

    # =====================================================
    # Lane follower callback
    # =====================================================
    def cmd_callback(self, msg):

        self.last_lane_cmd = msg


    # =====================================================
    # Red light callback
    # =====================================================
    def red_light_callback(self, msg):

        if msg.data:

            if self.state != RobotState.STOP_RED_LIGHT:

                self.get_logger().warn(
                    "RED LIGHT detected"
                )

                self.state = RobotState.STOP_RED_LIGHT

        else:

            if self.state == RobotState.STOP_RED_LIGHT:

                self.get_logger().info(
                    "GREEN LIGHT detected"
                )

                self.state = RobotState.FOLLOW_LANE


    # =====================================================
    # Stop sign callback
    # =====================================================
    def stop_sign_callback(self, msg):

        if msg.data:

            self.get_logger().warn(
                "STOP SIGN detected"
            )

            self.state = RobotState.STOP_SIGN

            # Stop robot immediately
            self.publish_stop()

            # Wait 2 seconds
            time.sleep(2.0)

            self.get_logger().info(
                "Stop complete -> resume"
            )

            self.state = RobotState.FOLLOW_LANE


    # =====================================================
    # Pedestrian callback
    # =====================================================
    def pedestrian_callback(self, msg):

        if msg.data:

            if self.state != RobotState.WAIT_PEDESTRIAN:

                self.get_logger().warn(
                    "PEDESTRIAN detected"
                )

                self.state = RobotState.WAIT_PEDESTRIAN

        else:

            if self.state == RobotState.WAIT_PEDESTRIAN:

                self.get_logger().info(
                    "Pedestrian gone -> resume"
                )

                self.state = RobotState.FOLLOW_LANE


    # =====================================================
    # Main control loop
    # =====================================================
    def control_loop(self):

        cmd_out = Twist()

        # -------------------------------------------------
        # FOLLOW LANE
        # -------------------------------------------------
        if self.state == RobotState.FOLLOW_LANE:
            cmd_out = self.last_lane_cmd

        # -------------------------------------------------
        # RED LIGHT
        # -------------------------------------------------
        elif self.state == RobotState.STOP_RED_LIGHT:
            # cmd_out = self.last_lane_cmd

            if self.distance_Z > 5:
                self.coeff_vitesse = 1
            elif self.distance_Z > 3:
                self.coeff_vitesse = 0.6
            elif self.distance_Z > 2:
                self.coeff_vitesse = 0.3
            elif self.distance_Z > 1:
                self.coeff_vitesse = 0
            
            # cmd_out.linear.x = 0.0
            # cmd_out.angular.z = 0.0
            cmd_out.linear.x = self.coeff_vitesse * cmd_out.linear.x
            cmd_out.angular.z = self.coeff_vitesse * cmd_out.angular.z

        # -------------------------------------------------
        # STOP SIGN
        # -------------------------------------------------
        elif self.state == RobotState.STOP_SIGN:

            cmd_out.linear.x = 0.0
            cmd_out.angular.z = 0.0

        # -------------------------------------------------
        # PEDESTRIAN
        # -------------------------------------------------
        elif self.state == RobotState.WAIT_PEDESTRIAN:

            cmd_out.linear.x = 0.0
            cmd_out.angular.z = 0.0

        # -------------------------------------------------
        # Publish final command
        # -------------------------------------------------
        self.cmd_pub.publish(cmd_out)


    # =====================================================
    # Publish stop command
    # =====================================================
    def publish_stop(self):

        stop_cmd = Twist()
        while self.distance_Z > :
        if self.distance_Z > 5:
                self.coeff_vitesse = 1
            elif self.distance_Z > 3:
                self.coeff_vitesse = 0.6
            elif self.distance_Z > 2:
                self.coeff_vitesse = 0.3
            elif self.distance_Z > 1:
                self.coeff_vitesse = 0

        # stop_cmd.linear.x = 0.0
        # stop_cmd.angular.z = 0.0
        stop_cmd.linear.x = self.coeff_vitesse * stop_cmd.linear.x
        stop_cmd.angular.z = self.coeff_vitesse * stop_cmd.angular.z

        self.cmd_pub.publish(stop_cmd)


# =========================================================
# Main
# =========================================================
def main(args=None):

    rclpy.init(args=args)

    node = BehaviorManager()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':

    main()