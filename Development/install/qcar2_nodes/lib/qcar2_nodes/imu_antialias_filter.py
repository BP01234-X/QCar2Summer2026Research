#!/usr/bin/env python3
"""
imu_antialias_filter.py

Nodo intermedio de preprocesamiento del IMU para el stack QCar2.

Problema que resuelve:
    /qcar2_imu se publica a ~1000 Hz (temporizador de 1ms en qcar2_hardware.cpp),
    pero el chip del giroscopio solo refresca dato nuevo cada 500 Hz (gyro_rate
    configurado), generando muestras duplicadas ("escalon"). Ademas,
    nav_to_pose.py necesita decimar esa senal a 200 Hz para su lazo de control,
    y hacerlo sin filtrar primero introduce aliasing: contenido de vibracion
    por encima de 100 Hz (Nyquist de 200 Hz) se pliega hacia la banda util
    de control.

Solucion:
    Filtro Butterworth pasa-bajas de orden 4 (fc configurable, default 80 Hz),
    aplicado en la tasa NATIVA de /qcar2_imu, ANTES de cualquier decimacion.
    Publica dos salidas:
        - /qcar2_imu_filtered        -> tasa nativa completa
                                         (consumida por Cartographer y wheel_odom.py)
        - /qcar2_imu_filtered_200hz  -> decimada /5
                                         (consumida por nav_to_pose.py)

    Incluye calibracion estatica de bias (Nivel 1): durante los primeros
    calib_duration_sec segundos tras arrancar, asume el carro quieto y
    promedia el gyro crudo para estimar el offset de cada eje. Ese offset
    se resta de todas las lecturas futuras. Esto NO resuelve la deriva de
    bias con temperatura -- eso se estima en linea dentro del EKF de 4
    estados (pendiente, sesion aparte).
"""

import numpy as np
from scipy.signal import butter, sosfilt

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Imu


class ImuAntialiasFilter(Node):

    def __init__(self):
        super().__init__("imu_antialias_filter")

        # ---- Parametros ajustables sin recompilar (ros2 param set / YAML) ----
        self.declare_parameter("native_rate_hz", 1000.0)   # tasa nominal de /qcar2_imu
        self.declare_parameter("cutoff_hz", 80.0)           # fc del anti-alias
        self.declare_parameter("filter_order", 4)
        self.declare_parameter("decimation_factor", 5)      # 1000/5 = 200 Hz para nav_to_pose
        self.declare_parameter("calib_duration_sec", 2.0)   # ventana de calibracion de bias

        self.native_rate = float(self.get_parameter("native_rate_hz").value)
        self.cutoff = float(self.get_parameter("cutoff_hz").value)
        self.order = int(self.get_parameter("filter_order").value)
        self.decim = int(self.get_parameter("decimation_factor").value)
        self.calib_duration = float(self.get_parameter("calib_duration_sec").value)

        # ---- Diseno del filtro (una sola vez al iniciar, no en cada callback) ----
        # 'sos' (second-order sections) en vez de coeficientes b,a directos:
        # numericamente mas estable para orden 4 -- con b,a de orden alto los
        # coeficientes pueden volverse mal condicionados y el filtro "explota"
        # por errores de redondeo en punto flotante. sos evita ese problema
        # descomponiendo el filtro en secciones de orden 2 en cascada.
        self.sos = butter(
            self.order, self.cutoff, btype="low",
            fs=self.native_rate, output="sos"
        )

        # Estado interno del filtro (zi) -- IMPRESCINDIBLE porque este es un
        # filtro EN VIVO, muestra por muestra, no un filtrado de lote (batch).
        # Sin conservar este estado entre llamadas, cada mensaje se filtraria
        # como si fuera el primero de la historia (arrancando siempre desde
        # cero), lo cual arruina la respuesta del filtro.
        # Forma: (num_secciones_sos, 2, num_ejes) -- un estado independiente
        # por cada eje del giroscopio (x, y, z).
        self.zi = np.zeros((self.sos.shape[0], 2, 3))

        # ---- Estado de calibracion de bias ----
        self.calibrating = True
        self.calib_samples = []
        self.bias = np.zeros(3)
        self.calib_start_time = None

        # ---- Contador de decimacion (simple, sin relacion con frecuencias) ----
        self.sample_count = 0

        qos = QoSProfile(depth=20)  # misma profundidad que usa ekf_fusor.py al suscribirse

        self.sub_imu = self.create_subscription(
            Imu, "/qcar2_imu", self.imu_callback, qos
        )
        self.pub_full = self.create_publisher(Imu, "/qcar2_imu_filtered", qos)
        self.pub_decim = self.create_publisher(Imu, "/qcar2_imu_filtered_200hz", qos)

        self.get_logger().info(
            f"imu_antialias_filter iniciado. Calibrando bias durante "
            f"{self.calib_duration:.1f}s -- mantener el QCar2 quieto."
        )

    def imu_callback(self, msg: Imu):
        gyro = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])

        # ---- Fase 1: calibracion de bias (Nivel 1) ----
        # Mientras se calibra, NO se publica nada -- evita un salto brusco
        # (discontinuidad) en el momento en que el bias pasa de 0 al valor real.
        if self.calibrating:
            now = self.get_clock().now()
            if self.calib_start_time is None:
                self.calib_start_time = now
            self.calib_samples.append(gyro)

            elapsed = (now - self.calib_start_time).nanoseconds * 1e-9
            if elapsed >= self.calib_duration:
                self.bias = np.mean(np.array(self.calib_samples), axis=0)
                self.calibrating = False
                self.get_logger().info(
                    f"Bias calibrado: x={self.bias[0]:.5f} "
                    f"y={self.bias[1]:.5f} z={self.bias[2]:.5f} rad/s"
                )
            return

        # ---- Fase 2: operacion normal ----
        # Restar el bias es una operacion lineal -- no importa si se hace
        # antes o despues del filtro (el filtro no distingue "senal real
        # menos bias" de "senal real filtrada, menos bias filtrado", porque
        # el bias es constante en DC y el filtro deja pasar DC con ganancia 1).
        # Se resta aqui, antes, porque es mas facil de leer.
        gyro_debiased = gyro - self.bias

        filtered = np.zeros(3)
        for axis in range(3):
            out, self.zi[:, :, axis] = sosfilt(
                self.sos, gyro_debiased[axis:axis + 1], zi=self.zi[:, :, axis]
            )
            filtered[axis] = out[0]

        # ---- Salida 1: tasa nativa completa -> Cartographer + wheel_odom.py ----
        msg_full = Imu()
        msg_full.header = msg.header
        msg_full.angular_velocity.x = float(filtered[0])
        msg_full.angular_velocity.y = float(filtered[1])
        msg_full.angular_velocity.z = float(filtered[2])
        msg_full.linear_acceleration = msg.linear_acceleration  # sin tocar por ahora
        msg_full.orientation = msg.orientation
        self.pub_full.publish(msg_full)

        # ---- Salida 2: decimada -> nav_to_pose.py ----
        self.sample_count += 1
        if self.sample_count >= self.decim:
            self.sample_count = 0
            self.pub_decim.publish(msg_full)


def main(args=None):
    rclpy.init(args=args)
    node = ImuAntialiasFilter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
