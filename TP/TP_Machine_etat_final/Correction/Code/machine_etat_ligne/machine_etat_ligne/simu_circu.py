#!/usr/bin/env python3

# ============================================================
# detection_simulator.py
#
# Simple ROS2 simulator for:
#   - red lights
#   - stop signs
#   - pedestrians
#
# Publishes Bool topics manually from keyboard input.
#
# Useful for testing:
#   - behavior_manager
#   - state machine
#   - autonomous navigation
#
# ------------------------------------------------------------
# Controls:
#
#   r : toggle red light
#   s : trigger stop sign
#   p : toggle pedestrian
#   q : quit
#
# ============================================================

import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool

import threading


class DetectionSimulator(Node):

    def __init__(self):
        super().__init__('detection_simulator')

        self.red_pub = self.create_publisher(
            Bool,
            '/red_light',
            10
        )

        self.stop_pub = self.create_publisher(
            Bool,
            '/stop_sign',
            10
        )

        self.ped_pub = self.create_publisher(
            Bool,
            '/pedestrian',
            10
        )


        self.red_light_active = False
        self.pedestrian_active = False

        self.get_logger().info("=== Detection Simulator Started ===")
        self.print_help()

        # Keyboard thread
        self.thread = threading.Thread(target=self.keyboard_loop)
        self.thread.daemon = True
        self.thread.start()


    def print_help(self):

        print("\n")
        print("======================================")
        print(" Detection Simulator Controls")
        print("======================================")
        print("r : RED LIGHT")
        print("s : STOP SIGN")
        print("p : PEDESTRIAN")
        print("q : quit")
        print("======================================")
        print("\n")


    def keyboard_loop(self):

        while rclpy.ok():

            key = input("Command: ").strip().lower()

            # RED LIGHT

            if key == 'r':

                self.red_light_active = not self.red_light_active

                msg = Bool()
                msg.data = self.red_light_active

                self.red_pub.publish(msg)

                if self.red_light_active:
                    self.get_logger().warn("RED LIGHT ON")
                else:
                    self.get_logger().info("GREEN LIGHT")

            # STOP SIGN

            elif key == 's':

                msg = Bool()
                msg.data = True

                self.stop_pub.publish(msg)

                self.get_logger().warn("STOP SIGN TRIGGERED")

            # PEDESTRIAN

            elif key == 'p':

                self.pedestrian_active = not self.pedestrian_active

                msg = Bool()
                msg.data = self.pedestrian_active

                self.ped_pub.publish(msg)

                if self.pedestrian_active:
                    self.get_logger().warn("PEDESTRIAN DETECTED")
                else:
                    self.get_logger().info("PEDESTRIAN CLEARED")

            # QUIT

            elif key == 'q':

                self.get_logger().info("Shutting down simulator...")
                rclpy.shutdown()
                break

            else:
                print("Unknown command.")
                self.print_help()


# ============================================================
# MAIN
# ============================================================

def main(args=None):

    rclpy.init(args=args)

    node = DetectionSimulator()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()