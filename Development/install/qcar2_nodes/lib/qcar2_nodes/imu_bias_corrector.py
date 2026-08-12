#!/usr/bin/env python3
"""
imu_bias_corrector.py — Calibra y resta el bias estatico del giroscopio
antes de que el IMU llegue a Cartografo (opcion 1 discutida en chat).

Por que existe:
  Confirmado por auditoria (docker/0_libraries + hil.h del SDK de Quanser):
  el canal OI 3000/3001/3002 ya llega en rad/s, sin conversion de unidades
  pendiente. Pero un gyro MEMS real casi siempre tiene un offset constante
  (bias) que NO es cero en reposo -- ekf_fusor.py ya conocia esto y restaba
  un valor fijo (0.011) de origen desconocido (no confirmado por bp00 ni su
  equipo, probablemente un valor generico de Quanser).

  Confirmado por documentacion oficial de Cartografo (google-cartographer,
  terminology.html + faq.html): su ImuTracker interno SOLO corrige deriva
  de roll/pitch via alineacion con gravedad (acelerometro). Yaw no se
  corrige nunca dentro de Cartografo -- la gravedad no contiene informacion
  de yaw. Cartografo depende 100% del scan matching de LIDAR para absorber
  cualquier deriva/bias de yaw que traiga el gyro. Por diseno, Cartografo
  espera que le llegue el IMU ya razonablemente limpio en ese eje -- no es
  su trabajo limpiarlo.

  Un filtro Butterworth NO resuelve esto -- es pasa-bajas, dEja pasar
  sin tocar cualquier componente constante (DC), y un bias ES una
  componente constante. Por eso se descarto esa opcion.

Como funciona:
  Al arrancar, colecciona muestras de angular_velocity durante
  'calibration_duration' segundos (default 3.0s) SIN corregir nada
  (passthrough), asumiendo que el auto esta quieto en ese intervalo.
  Calcula el promedio (bias) y la desviacion estandar de esas muestras.
  De ahi en adelante, resta el bias medido de cada lectura y republica.

Decisiones / supuestos, explicitos para no perderlos:

  1) VENTANA DE CALIBRACION = auto quieto, por construccion del sistema:
     path_follower necesita 'start_path' en true (parametro manual) para
     empezar a mover el auto -- eso pasa despues de que este nodo ya
     arranco con el resto del launch. No hay garantia dura de que el auto
     este quieto, pero es consistente con el flujo de trabajo actual.
     Si la desviacion estandar del eje z sale alta (>0.02 rad/s, umbral
     arbitrario sin calibrar todavia), se loguea un WARNING -- sospecha
     de que el auto se movio durante la calibracion, bias no confiable.

  2) Se calibra bias en los 3 ejes (x, y, z), no solo z -- mas completo,
     no cuesta nada extra, aunque el eje que nos importa para Cartografo
     es z (yaw).

  3) Tópico nuevo, no se pisa el original: publica en
     '/qcar2_imu/bias_corrected', dejando '/qcar2_imu' intacto por si
     algo mas lo consume (nav_to_pose.py, ekf_fusor.py siguen leyendo el
     original sin cambios). Cartografo es el unico que se remapea al
     nuevo topico -- ver instrucciones de wiring aparte.

  4) Esto solo se aplica al pipeline VIRTUAL por ahora (mismo criterio que
     veniamos usando: probar en simulacion antes de tocar fisico).
  5) STARTUP_DELAY (agregado tras la primera prueba real):
     Primera corrida dio bias z=0.11298, segunda corrida dio z=0.00128 --
     dos mediciones del "mismo" bias no deberian diferir casi dos ordenes
     de magnitud. La desviacion estandar de la segunda corrida (0.07054)
     salio ~55x mas grande que el propio bias medido (0.00128) -- eso es
     ruido dominando la ventana, no un offset constante real.
     Hipotesis: la ventana de calibracion arrancaba en el mismo instante
     que el nodo, coincidiendo con logs de Cartografo tipo "Extrapolator
     not yet initialized" y fallos de lookup de TF por falta de buffer --
     posible transitorio de asentamiento fisico de QLabs justo al spawnear
     el auto. 'startup_delay' descarta muestras durante ese intervalo
     inicial antes de empezar a contar los segundos de calibracion real.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuBiasCorrector(Node):

    def __init__(self):
        super().__init__('imu_bias_corrector')

        self.declare_parameter('calibration_duration', 3.0)  # segundos
        self.declare_parameter('startup_delay', 2.0)  # segundos, descartados antes de calibrar
        self.calib_duration = self.get_parameter('calibration_duration').value
        self.startup_delay = self.get_parameter('startup_delay').value

        self._node_start_time = self.get_clock().now()
        self._calib_samples = []
        self._calib_start_time = None
        self._calibrated = False
        self.bias = np.zeros(3)  # [x, y, z] rad/s

        self.imu_sub = self.create_subscription(
            Imu, '/qcar2_imu', self.imu_cb, 10)
        self.imu_pub = self.create_publisher(
            Imu, '/qcar2_imu/bias_corrected', 10)

        self.get_logger().info(
            f'imu_bias_corrector iniciado. Esperando {self.startup_delay:.1f}s '
            f'(asentamiento del simulador) antes de calibrar '
            f'{self.calib_duration:.1f}s -- EL AUTO DEBE ESTAR QUIETO '
            f'durante todo este intervalo.'
        )

    def imu_cb(self, msg):
        now = self.get_clock().now()

        if not self._calibrated:
            since_start = (now - self._node_start_time).nanoseconds * 1e-9
            if since_start < self.startup_delay:
                # todavia en la ventana de asentamiento -- no se usa para
                # calibrar, pero se sigue pasando sin corregir para no
                # dejar a Cartografo sin datos de IMU esos primeros segundos
                self.imu_pub.publish(msg)
                return

            if self._calib_start_time is None:
                self._calib_start_time = now
                self.get_logger().info(
                    'Ventana de asentamiento terminada -- empieza calibracion real.'
                )

            elapsed = (now - self._calib_start_time).nanoseconds * 1e-9
            self._calib_samples.append([
                msg.angular_velocity.x,
                msg.angular_velocity.y,
                msg.angular_velocity.z,
            ])

            if elapsed >= self.calib_duration:
                samples = np.array(self._calib_samples)
                self.bias = samples.mean(axis=0)
                std = samples.std(axis=0)
                self._calibrated = True

                self.get_logger().info(
                    f'Calibracion completa ({len(samples)} muestras). '
                    f'Bias medido [x,y,z]: '
                    f'{self.bias[0]:.5f}, {self.bias[1]:.5f}, '
                    f'{self.bias[2]:.5f} rad/s | '
                    f'desv. estandar [x,y,z]: '
                    f'{std[0]:.5f}, {std[1]:.5f}, {std[2]:.5f} rad/s'
                )
                if std[2] > 0.02:
                    self.get_logger().warn(
                        f'Desviacion estandar de z ({std[2]:.5f}) es alta '
                        f'-- el auto pudo haber estado en movimiento '
                        f'durante la calibracion. Bias medido puede no '
                        f'ser confiable, revisa antes de confiar en esto.'
                    )

            # Durante la ventana de calibracion: passthrough sin corregir,
            # para no dejar a Cartografo sin datos de IMU esos ~3s.
            self.imu_pub.publish(msg)
            return

        # Ya calibrado: restar bias medido y republicar.
        corrected = msg
        corrected.angular_velocity.x -= self.bias[0]
        corrected.angular_velocity.y -= self.bias[1]
        corrected.angular_velocity.z -= self.bias[2]
        self.imu_pub.publish(corrected)


def main(args=None):
    rclpy.init(args=args)
    node = ImuBiasCorrector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()