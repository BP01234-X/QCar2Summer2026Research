#!/usr/bin/env python3
"""
wheel_odom.py — Odometria dead-reckoning para QCar2 (borrador para revision)



  1) TF: este nodo NO publica la transformada odom->base_link.
     Cartografo ya es dueno de ese TF (provide_odom_frame: true en
     qcar2_2d.lua). Publicarla aqui tambien generaria dos publishers
     compitiendo por el mismo frame -- se descarto a proposito.

     ACLARACION IMPORTANTE (para no confundir esto de nuevo despues):
     header.frame_id='odom' y child_frame_id='base_link' en el mensaje
     Odometry NO son un broadcast de TF. Son solo metadata del mensaje:
     dicen en que frame esta expresada la pose y respecto a que frame
     esta expresado el twist. No declaran, y no pueden declarar, quien
     es padre de quien en el arbol TF real -- eso solo lo determina un
     TransformBroadcaster real, y el unico que existe para este par de
     frames es el de Cartografo (via provide_odom_frame=true).
     En otras palabras: "odom hijo de map" YA es verdad en el arbol TF
     real, publicado por Cartografo, con o sin este nodo. Este archivo
     no necesita (ni puede, con un mensaje Odometry) declarar esa
     jerarquia -- solo manda datos que Cartografo va a LEER.

  2) Covarianza: queda en cero (= "confianza total") por ahora. Cartografo
     puede interpretar eso como verdad absoluta. Falta calibrar una vez
     que se vea empiricamente cuanto deriva esto en simulacion frente a
     la correccion de Cartografo por LIDAR.

  3) Nombre de topico 'odom': se uso el nombre por defecto que ya usan
     otros publishers de odometria en este repo (scan_match.py,
     ekf_fusor.py). NO esta confirmado que sea el topico que
     cartographer_node espera por defecto sin remap -- verificar con
     `ros2 topic info /odom` y la config de use_odometry en tiempo real
     antes de asumir que se estan conectando.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from qcar2_interfaces.msg import MotorCommands
from nav_msgs.msg import Odometry
from scipy.spatial.transform import Rotation as R
# NOTA: se uso scipy en vez de tf_transformations a proposito -- nav_to_pose.py
# ya depende de scipy.spatial.transform.Rotation (en tf_timer, para el sentido
# inverso cuaternion->yaw), asi que no se agrega ninguna dependencia nueva al
# contenedor. tf_transformations no viene instalado por defecto en varias
# distros de ROS2 recientes y hay que agregarlo aparte -- se evita ese paso.


class WheelOdom(Node):

    def __init__(self):
        super().__init__('wheel_odom')

        # Mismos valores de referencia que nav_to_pose.py (dt=1/200, L=0.256
        # en path_planner()) para que el dead-reckoning sea comparable
        # cuadro a cuadro con lo que ya corre en el path_follower.
        self.declare_parameter('publish_rate', 200.0)  # Hz
        self.declare_parameter('wheelbase', 0.256)      # m

        rate = self.get_parameter('publish_rate').value
        self.L = self.get_parameter('wheelbase').value
        self.dt = 1.0 / rate

        # Estado: [x, y, theta]. Arranca en el origen -- misma convencion
        # hardcodeada que x0 en QcarEKF (ver auditoria de pose inicial).
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.v = 0.0       # velocidad medida [m/s], viene de /qcar2_joint
        self.delta = 0.0   # direccion comandada [rad], viene de /qcar2_motor_speed_cmd

        self.joint_sub = self.create_subscription(
            JointState, '/qcar2_joint_filtered', self.joint_cb, 1)
        self.motor_sub = self.create_subscription(
            MotorCommands, '/qcar2_motor_speed_cmd', self.motor_cb, 1)

        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)

        self.timer = self.create_timer(self.dt, self.step)

        # --- Logging de diagnostico (pedido por bp00) ---
        # Aviso de arranque: siempre va a mostrar (0,0,0) porque x0 esta
        # hardcodeado -- no es un bug del logger, es el mismo hardcodeo
        # de pose inicial que ya documentamos en QcarEKF. Sirve para
        # confirmar que el nodo arranco, no para ver un valor "interesante".
        self.get_logger().info(
            f'wheel_odom iniciado. Pose inicial (frame odom, dead-reckoning '
            f'puro, sin correccion): x={self.x:.3f} y={self.y:.3f} '
            f'theta={self.theta:.3f} rad'
        )

        self.declare_parameter('log_interval', 10.0)  # segundos
        self._log_interval = self.get_parameter('log_interval').value
        self._last_log_x = self.x
        self._last_log_y = self.y
        self._last_log_theta = self.theta
        self.log_timer = self.create_timer(self._log_interval, self.log_status)

    def log_status(self):
        # Reporta el DELTA desde el ultimo chequeo, no solo el valor absoluto
        # -- asi es visualmente obvio si esta cambiando o si esta congelado
        # (auto detenido, o v/delta no estan llegando por algun motivo).
        # IMPORTANTE: esto describe SOLO el estado interno de este nodo
        # (integracion pura del modelo de bicicleta). No dice nada sobre si
        # Cartografo esta usando este dato para corregir su TF map->odom --
        # esa es una pregunta distinta, ver conversacion / CHANGELOG.
        dx = self.x - self._last_log_x
        dy = self.y - self._last_log_y
        dtheta = self.theta - self._last_log_theta
        dist = float(np.hypot(dx, dy))

        if dist > 1e-4 or abs(dtheta) > 1e-4:
            self.get_logger().info(
                f'[wheel_odom] cambio en ultimos {self._log_interval:.0f}s -> '
                f'dx={dx:+.4f} m  dy={dy:+.4f} m  '
                f'dtheta={np.degrees(dtheta):+.2f} deg  '
                f'| distancia recorrida={dist:.4f} m '
                f'| pose actual (frame odom): x={self.x:.3f} y={self.y:.3f} '
                f'theta={self.theta:.3f} rad'
            )
        else:
            self.get_logger().info(
                f'[wheel_odom] SIN cambios en los ultimos '
                f'{self._log_interval:.0f}s (v={self.v:.3f} m/s, '
                f'delta={self.delta:.3f} rad) -- revisa si el auto se esta '
                f'moviendo o si /qcar2_joint y /qcar2_motor_speed_cmd '
                f'estan llegando'
            )

        self._last_log_x = self.x
        self._last_log_y = self.y
        self._last_log_theta = self.theta

        # Log de estado cada 10s, solo si hubo cambio desde el ultimo log
        # (si v=0, el estado queda bit-a-bit igual entre pasos, asi que no
        # imprime nada mientras el auto esta quieto).
        self.last_logged_state = None
        self.log_timer = self.create_timer(10.0, self.log_state)

        self.get_logger().info(
            f'wheel_odom iniciado. Estado inicial: '
            f'x={self.x:.3f} m, y={self.y:.3f} m, theta={self.theta:.3f} rad'
        )

    def joint_cb(self, msg):
        if not msg.velocity:
            return
        # Misma conversion que joint_state_callback en nav_to_pose.py
        # (linea 442): ticks/s -> rad/s -> m/s via radio de rueda.
        # Gear ratio (70*30) de nav_to_pose.py -- confirmado por bp00,
        # se ignora el (70*37) de ekf_fusor.py para este nodo.
        self.v = (msg.velocity[0] / (720.0 * 4.0)) * \
                  ((13.0 * 19.0) / (70.0 * 30.0)) * (2.0 * np.pi) * 0.033

    def motor_cb(self, msg):
        # Extrae 'steering_angle' del mensaje MotorCommands por nombre,
        # igual que se arma en nav2_qcar_command_convert.cpp / command.cpp.
        try:
            idx = list(msg.motor_names).index('steering_angle')
            self.delta = msg.values[idx]
        except ValueError:
            pass  # este mensaje no trae direccion, se mantiene el ultimo valor

    def step(self):
        # Exactamente el mismo update que QcarEKF.f(), sin ningun termino
        # de correccion -- esto es la parte "dead reckoning" pura.
        self.x += self.dt * self.v * np.cos(self.theta)
        self.y += self.dt * self.v * np.sin(self.theta)
        self.theta += self.dt * self.v * np.tan(self.delta) / self.L
        self.theta = np.arctan2(np.sin(self.theta), np.cos(self.theta))  # wrap a +/-pi

        self.publish_odom()

    def publish_odom(self):
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_link'

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0

        q = R.from_euler('z', self.theta).as_quat()  # devuelve [x, y, z, w]
        msg.pose.pose.orientation.x = q[0]
        msg.pose.pose.orientation.y = q[1]
        msg.pose.pose.orientation.z = q[2]
        msg.pose.pose.orientation.w = q[3]

        msg.twist.twist.linear.x = self.v
        msg.twist.twist.angular.z = self.v * np.tan(self.delta) / self.L

        # TODO (decision 4): covarianza sin calibrar, queda en cero.
        self.odom_pub.publish(msg)


    def log_state(self):
        current_state = (round(self.x, 4), round(self.y, 4), round(self.theta, 4))
        if current_state != self.last_logged_state:
            self.get_logger().info(
                f'[wheel_odom] x={self.x:.3f} m, y={self.y:.3f} m, '
                f'theta={self.theta:.3f} rad, v={self.v:.3f} m/s, '
                f'delta={self.delta:.3f} rad'
            )
            self.last_logged_state = current_state


def main(args=None):
    rclpy.init(args=args)
    node = WheelOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()