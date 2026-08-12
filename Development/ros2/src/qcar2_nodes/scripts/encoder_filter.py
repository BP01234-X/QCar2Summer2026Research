#!/usr/bin/env python3
"""
encoder_filter.py

Filtro de suavizado (NO anti-alias) para el encoder del QCar2.

A diferencia del IMU, el encoder no tiene contenido de vibracion de alta
frecuencia "escondido" que pueda plegarse -- es un conteo discreto de pulsos.
Su ruido es de cuantizacion: al derivar velocidad desde conteos discretos
(hecho en firmware, entregado como ticks/s en /qcar2_joint), aparecen
"escalones" mas notorios a baja velocidad, sobre todo. Un Butterworth de
orden bajo (1-2) con fc baja es suficiente -- no hay Nyquist que proteger
aqui porque esta senal no se decima en ningun punto del pipeline.
"""

import numpy as np
from scipy.signal import butter, sosfilt

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import JointState


class EncoderFilter(Node):

    def __init__(self):
        super().__init__("encoder_filter")

        self.declare_parameter("native_rate_hz", 1000.0)
        self.declare_parameter("cutoff_hz", 15.0)
        self.declare_parameter("filter_order", 2)

        native_rate = float(self.get_parameter("native_rate_hz").value)
        cutoff = float(self.get_parameter("cutoff_hz").value)
        order = int(self.get_parameter("filter_order").value)

        self.sos = butter(order, cutoff, btype="low", fs=native_rate, output="sos")
        # Un solo canal (velocidad escalar) -> un solo estado, a diferencia
        # del IMU que necesitaba tres (x, y, z).
        self.zi = np.zeros((self.sos.shape[0], 2))

        qos = QoSProfile(depth=10)
        self.sub_joint = self.create_subscription(
            JointState, "/qcar2_joint", self.joint_callback, qos
        )
        self.pub_joint = self.create_publisher(JointState, "/qcar2_joint_filtered", qos)

        self.get_logger().info("encoder_filter iniciado.")

    def joint_callback(self, msg: JointState):
        if not msg.velocity:
            return  # mensaje sin dato de velocidad todavia -- ignorar

        raw = np.array([msg.velocity[0]])
        out, self.zi = sosfilt(self.sos, raw, zi=self.zi)

        msg_out = JointState()
        msg_out.header = msg.header
        msg_out.name = msg.name
        msg_out.position = msg.position
        msg_out.velocity = [float(out[0])]
        msg_out.effort = msg.effort
        self.pub_joint.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    node = EncoderFilter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
