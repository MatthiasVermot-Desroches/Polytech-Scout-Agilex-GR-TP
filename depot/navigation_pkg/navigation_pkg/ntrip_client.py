import rclpy
from rclpy.node import Node
from rtcm_msgs.msg import Message as RtcmMessage
import socket
import base64
import threading

class NtripClient(Node):
    def __init__(self):
        super().__init__('ntrip_client')

        # Paramètres Centipède
        self.declare_parameter('host',       'caster.centipede.fr')
        self.declare_parameter('port',       2101)
        self.declare_parameter('mountpoint', 'RTCM3')
        self.declare_parameter('username',   'centipede')
        self.declare_parameter('password',   'centipede')

        self.host       = self.get_parameter('host').value
        self.port       = self.get_parameter('port').value
        self.mountpoint = self.get_parameter('mountpoint').value
        self.username   = self.get_parameter('username').value
        self.password   = self.get_parameter('password').value

        # Publisher corrections RTCM vers le récepteur GPS
        self.pub_rtcm = self.create_publisher(
            RtcmMessage, '/rtcm', 10)

        self.connected = False
        self.socket    = None

        # Lance la connexion dans un thread séparé
        self.thread = threading.Thread(target=self.connect_and_stream)
        self.thread.daemon = True
        self.thread.start()

        self.get_logger().info(
            f'NTRIP client démarré → {self.host}:{self.port}/{self.mountpoint}')

    def connect_and_stream(self):
        while rclpy.ok():
            try:
                self.get_logger().info('Connexion au caster Centipède...')
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10.0)
                self.socket.connect((self.host, self.port))

                # Requête HTTP NTRIP
                credentials = base64.b64encode(
                    f'{self.username}:{self.password}'.encode()).decode()
                request = (
                    f'GET /{self.mountpoint} HTTP/1.0\r\n'
                    f'Host: {self.host}\r\n'
                    f'Ntrip-Version: Ntrip/2.0\r\n'
                    f'User-Agent: NTRIP ROS2Client/1.0\r\n'
                    f'Authorization: Basic {credentials}\r\n'
                    f'\r\n'
                )
                self.socket.sendall(request.encode())

                # Vérifie la réponse
                response = self.socket.recv(1024).decode('latin-1')
                if 'ICY 200 OK' in response or '200 OK' in response:
                    self.get_logger().info('Connecté à Centipède ✅')
                    self.connected = True
                    self.stream_rtcm()
                else:
                    self.get_logger().error(f'Connexion refusée : {response[:100]}')

            except Exception as e:
                self.get_logger().error(f'Erreur NTRIP : {e}')
                self.connected = False

            # Attends 5 secondes avant de réessayer
            import time
            time.sleep(5.0)

    def stream_rtcm(self):
        """Lit les corrections RTCM et les publie sur /rtcm"""
        buffer = b''
        while rclpy.ok() and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.get_logger().warn('Connexion NTRIP perdue')
                    self.connected = False
                    break

                buffer += data

                # Parse les messages RTCM3 (commencent par 0xD3)
                while len(buffer) >= 3:
                    if buffer[0] != 0xD3:
                        buffer = buffer[1:]
                        continue

                    # Longueur du message RTCM
                    msg_len = ((buffer[1] & 0x03) << 8) | buffer[2]
                    total_len = msg_len + 6  # header + data + CRC

                    if len(buffer) < total_len:
                        break  # attend plus de données

                    rtcm_data = buffer[:total_len]
                    buffer = buffer[total_len:]

                    # Publie le message RTCM
                    msg = RtcmMessage()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = 'gps'
                    msg.message = list(rtcm_data)
                    self.pub_rtcm.publish(msg)

            except Exception as e:
                self.get_logger().error(f'Erreur stream RTCM : {e}')
                self.connected = False
                break


def main(args=None):
    rclpy.init(args=args)
    node = NtripClient()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()