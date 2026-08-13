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
 
  Un filtro Butterworth NO resuelve esto -- es pasa-bajas, deja pasar
  sin tocar cualquier componente constante (DC), y un bias ES una
  componente constante. Por eso se descarto esa opcion PARA EL BIAS.
 
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
 
  6) EXTENSION (esta version) -- Butterworth anti-alias + salida decimada:
     Agregado DESPUES del bias, no antes -- restar bias es una operacion
     lineal, el orden entre "restar bias" y "filtrar" no cambia el
     resultado matematico (el filtro deja pasar DC con ganancia 1, asi
     que no toca al bias de ninguna forma), pero hacerlo en este orden es
     mas facil de leer.
 
     Motivo real para agregar el filtro aqui (no es solo "mas limpio"):
     el problema documentado en el punto 5 (std 55x mayor que el bias en
     la segunda corrida) es sintoma de ruido de alta frecuencia
     contaminando la ventana de calibracion. Si ese ruido se filtra antes
     de promediar, la estimacion de bias deberia volverse mas estable
     entre corridas -- no hay garantia de cuanto mejora sin probarlo, pero
     el mecanismo es directo: promediar sobre una senal menos ruidosa da
     un promedio menos ruidoso.
 
     Se filtra TAMBIEN durante la ventana de calibracion (no solo despues)
     por esta razon -- las muestras usadas para calcular el promedio ya
     salen filtradas, no las crudas.
 
     Salida nueva: '/qcar2_imu/bias_corrected_200hz', decimada /5 desde la
     salida ya filtrada, pensada especificamente para nav_to_pose.py (que
     necesita 200Hz para su path_planner(), no 1000Hz). Cartografo sigue
     leyendo '/qcar2_imu/bias_corrected' a tasa nativa completa, sin
     cambios en su remap -- Cartografo no decima nada, no necesita
     proteccion anti-alias, solo se beneficia de la limpieza de ruido
     como efecto colateral del mismo filtro.
"""
 
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi
 
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
 
 
class ImuBiasCorrector(Node):
 
    def __init__(self):
        super().__init__('imu_bias_corrector')
 
        self.declare_parameter('calibration_duration', 3.0)  # segundos
        self.declare_parameter('startup_delay', 2.0)  # segundos, descartados antes de calibrar
        self.declare_parameter('native_rate_hz', 1000.0)  # tasa nominal de /qcar2_imu
        self.declare_parameter('cutoff_hz', 80.0)          # fc del anti-alias
        self.declare_parameter('filter_order', 4)
        self.declare_parameter('decimation_factor', 5)     # 1000/5 = 200Hz para nav_to_pose
 
        self.calib_duration = self.get_parameter('calibration_duration').value
        self.startup_delay = self.get_parameter('startup_delay').value
        self.native_rate = float(self.get_parameter('native_rate_hz').value)
        self.cutoff = float(self.get_parameter('cutoff_hz').value)
        self.order = int(self.get_parameter('filter_order').value)
        self.decim = int(self.get_parameter('decimation_factor').value)
 
        self._node_start_time = self.get_clock().now()
        self._calib_samples = []
        self._calib_start_time = None
        self._calibrated = False
        self.bias = np.zeros(3)  # [x, y, z] rad/s
 
        # ---- Diseno del filtro (una sola vez al iniciar) ----
        # sos (second-order sections), no b/a directos -- mismo motivo de
        # siempre: mas estable numericamente para orden 4.
        self.sos = butter(
            self.order, self.cutoff, btype='low',
            fs=self.native_rate, output='sos'
        )
        # Estado (zi) por eje -- se inicializa en ceros por ahora; se
        # "prime-a" (ver mas abajo) en cuanto llega la primera muestra,
        # para no arrancar el filtro desde un salto artificial de 0 a la
        # senal real.
        self.zi = np.zeros((self.sos.shape[0], 2, 3))
        self._zi_primed = False
 
        self.sample_count = 0
 
        self.imu_sub = self.create_subscription(
            Imu, '/qcar2_imu', self.imu_cb, 10)
        self.imu_pub = self.create_publisher(
            Imu, '/qcar2_imu/bias_corrected', 10)
        self.imu_pub_200hz = self.create_publisher(
            Imu, '/qcar2_imu/bias_corrected_200hz', 10)
 
        self.get_logger().info(
            f'imu_bias_corrector iniciado. Esperando {self.startup_delay:.1f}s '
            f'(asentamiento del simulador) antes de calibrar '
            f'{self.calib_duration:.1f}s -- EL AUTO DEBE ESTAR QUIETO '
            f'durante todo este intervalo. Filtro anti-alias: orden '
            f'{self.order}, fc={self.cutoff:.1f}Hz, decimacion /{self.decim}.'
        )
 
    def _apply_filter(self, gyro_debiased):
        """Filtra las 3 componentes del gyro, manteniendo estado (zi) entre
        llamadas -- filtro EN VIVO, no de lote. Sin esto cada mensaje se
        filtraria como si fuera el primero de la historia."""
        if not self._zi_primed:
            # "Priming": en vez de arrancar el filtro con memoria en cero
            # (lo que produciria un pequeno salto/transitorio al inicio,
            # como si la senal hubiera arrancado de golpe desde 0), se
            # inicializa la memoria interna asumiendo que el filtro ya
            # llevaba un rato viendo un valor constante igual a esta
            # primera muestra. sosfilt_zi() da el estado "de regimen
            # permanente" para una entrada constante de amplitud 1 -- se
            # escala por el valor real de la primera muestra en cada eje.
            zi_unit = sosfilt_zi(self.sos)  # forma (secciones, 2)
            for axis in range(3):
                self.zi[:, :, axis] = zi_unit * gyro_debiased[axis]
            self._zi_primed = True
 
        filtered = np.zeros(3)
        for axis in range(3):
            out, self.zi[:, :, axis] = sosfilt(
                self.sos, gyro_debiased[axis:axis + 1], zi=self.zi[:, :, axis]
            )
            filtered[axis] = out[0]
        return filtered
 
    def _make_imu_msg(self, original, gyro_values):
        out = Imu()
        out.header = original.header
        out.angular_velocity.x = float(gyro_values[0])
        out.angular_velocity.y = float(gyro_values[1])
        out.angular_velocity.z = float(gyro_values[2])
        out.linear_acceleration = original.linear_acceleration
        out.orientation = original.orientation
        return out
 
    def imu_cb(self, msg):
        now = self.get_clock().now()
 
        since_start = (now - self._node_start_time).nanoseconds * 1e-9
        if since_start < self.startup_delay:
            # todavia en la ventana de asentamiento -- no se filtra ni se
            # usa para calibrar, se pasa tal cual para no dejar a
            # Cartografo sin datos de IMU esos primeros segundos.
            self.imu_pub.publish(msg)
            return
 
        # A partir de aqui el filtro corre SIEMPRE, incluyendo durante la
        # ventana de calibracion -- CORREGIDO: la version anterior decia
        # en el docstring que la calibracion usaba muestras filtradas,
        # pero el codigo real promediaba crudo. Ese era el bug: el ruido
        # de alta frecuencia sin filtrar inflaba la desviacion estandar
        # de la calibracion (0.07047 rad/s medido, ~4 grados/s, con el
        # auto confirmado quieto por wheel_odom.py -- ese ruido no era
        # movimiento real, era la propia senal cruda).
        gyro = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])
        filtered = self._apply_filter(gyro)
 
        if not self._calibrated:
            if self._calib_start_time is None:
                self._calib_start_time = now
                self.get_logger().info(
                    'Ventana de asentamiento terminada -- empieza calibracion real.'
                )
 
            elapsed = (now - self._calib_start_time).nanoseconds * 1e-9
            # Ahora se guarda la muestra YA FILTRADA, no la cruda.
            self._calib_samples.append(filtered.copy())
 
            if elapsed >= self.calib_duration:
                samples = np.array(self._calib_samples)
                self.bias = samples.mean(axis=0)
                std = samples.std(axis=0)
                self._calibrated = True
 
                self.get_logger().info(
                    f'Calibracion completa ({len(samples)} muestras, '
                    f'sobre senal ya filtrada). Bias medido [x,y,z]: '
                    f'{self.bias[0]:.5f}, {self.bias[1]:.5f}, '
                    f'{self.bias[2]:.5f} rad/s | '
                    f'desv. estandar [x,y,z]: '
                    f'{std[0]:.5f}, {std[1]:.5f}, {std[2]:.5f} rad/s'
                )
                if std[2] > 0.02:
                    self.get_logger().warn(
                        f'Desviacion estandar de z ({std[2]:.5f}) sigue '
                        f'alta incluso ya filtrada -- esto ya no es ruido '
                        f'de alta frecuencia (eso se filtro), podria ser '
                        f'movimiento real durante la calibracion, o '
                        f'deriva de bias mas rapida de lo esperado. '
                        f'Revisa antes de confiar en este valor.'
                    )
 
            # Durante calibracion: se publica ya filtrado, pero SIN restar
            # bias todavia (no se conoce hasta que termine la ventana).
            out_msg = self._make_imu_msg(msg, filtered)
            self.imu_pub.publish(out_msg)
            return
 
        # ---- Ya calibrado: filtrado (arriba) menos bias, publicar dual ----
        corrected = filtered - self.bias
        out_msg = self._make_imu_msg(msg, corrected)
 
        # Salida 1: tasa nativa completa -> Cartografo (remap ya existente,
        # sin cambios) y cualquier otro consumidor que no decime.
        self.imu_pub.publish(out_msg)
 
        # Salida 2: decimada -> nav_to_pose.py
        self.sample_count += 1
        if self.sample_count >= self.decim:
            self.sample_count = 0
            self.imu_pub_200hz.publish(out_msg)
 
 
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
 