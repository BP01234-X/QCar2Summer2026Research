#! /usr/bin/env python3
 
# Quanser specific packages
from hal.products.mats import SDCSRoadMap
from pal.utilities.math import wrap_to_pi
 
# Generic python packages
import time  # Time library
import numpy as np
import scipy.signal as signal
from scipy.spatial.transform  import Rotation as R
from pal.utilities.scope import MultiScope
 
# ROS specific packages
from rclpy.duration import Duration # Handles time for ROS 2
import rclpy # Python client library for ROS 2
from geometry_msgs.msg import PoseStamped # Pose with ref frame and timestamp
from rclpy.node import Node
from nav_msgs.msg import Path
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import Imu, JointState
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Bool, Float64MultiArray
 
 
'''
Description:
 
Navigates a robot from an initial pose to a goal pose described by a series of
given nodes based on Quanser's SDCSRoadMap class
'''
 
# region: Helper classes for state estimation
class QcarEKF:
    """
    EKF unificado de 4 estados: [x, y, theta, b]
        - x, y, theta: pose 2D del auto (frame 'map')
        - b: bias residual del giroscopio (rad/s)
 
    Reemplaza los dos filtros acoplados que vivian aqui antes (QcarEKF de
    3 estados con heading via modelo de bicicleta + GyroKF de 2 estados
    separado). Motivo del cambio (documentado en sesion, no una preferencia
    de estilo): 'delta' (steering) es SIEMPRE comandado, nunca medido -- el
    QCar2 no tiene encoder de direccion. El giroscopio filtrado, en cambio,
    es una medicion real de cuanto esta girando el auto. Se usa como
    control en vez del modelo de bicicleta para el heading.
 
    Nota sobre el bias: '/qcar2_imu/bias_corrected_200hz' (lo que llega a
    self.gyroscope) YA tiene restado un bias estatico calculado una vez al
    arrancar (imu_bias_corrector.py). El estado 'b' de este EKF rastrea el
    RESIDUAL que esa calibracion estatica no puede seguir -- deriva de bias
    en el tiempo. Son dos capas distintas, documentadas por separado.
    """
 
    def __init__(self, x0, P0, Q, R, L=0.257):
        # Nomenclature:
        # - x0: initial estimate [x, y, theta, b]
        # - P0: initial covariance matrix estimate (4x4)
        # - Q: process noise covariance matrix (4x4)
        # - R: observation noise covariance matrix (3x3, Cartographer)
        # - xHat: state estimate
        # - P: state covariance matrix
        # - L: wheel base of the QCar
 
        self.L = L
 
        self.I = np.eye(4)
        self.xHat = x0
        self.P = P0
        self.Q = Q
        self.R = R
 
        # Solo x, y, theta son medidos directamente por Cartographer -- el
        # bias 'b' se corrige indirectamente via la correlacion que P
        # acumula durante la prediccion (misma logica que ya tenia GyroKF).
        self.C = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0]
        ])
 
    # ==============  SECTION A -  Motion Model ====================
    def f(self, X, u, dt):
        # Modelo cinematico con heading via giroscopio:
        # - X = [x, y, theta, b]
        # - u[0] = v (velocidad medida por encoder, [m/s])
        # - u[1] = omega (velocidad angular medida por gyro, [rad/s])
        # - dt: paso de tiempo desde la ultima actualizacion
 
        theta = X[2,0]
        b = X[3,0]
        return X + dt * np.array([
            [u[0] * np.cos(theta)],
            [u[0] * np.sin(theta)],
            [u[1] - b],
            [0.0]
        ])
 
    # ==============  SECTION B -  Motion Model Jacobian ====================
    def Jf(self, X, u, dt):
        # Jacobiano del modelo de arriba respecto al ESTADO (F, no V)
        theta = X[2,0]
        return np.array([
                [1, 0, -dt*u[0]*np.sin(theta),  0],
                [0, 1,  dt*u[0]*np.cos(theta),  0],
                [0, 0,  1,                     -dt],
                [0, 0,  0,                      1]
        ])
 
    # ==============  SECTION C -  Motion Model Prediction ====================
    def prediction(self, dt, u):
 
        # Update Covariance Estimate
        F = self.Jf(self.xHat, u, dt)
        self.P = F@self.P@np.transpose(F) + self.Q
 
        # Update State Estimate
        self.xHat = self.f(self.xHat, u, dt)
        # Wrap th to be in the range of +/- pi
        self.xHat[2] = wrap_to_pi(self.xHat[2])
 
        return
 
    # ==============  SECTION D -  Measurement correction ====================
    def correction(self, y):
        # y = [[x_cartographer], [y_cartographer], [theta_cartographer]]
 
        H = self.C
        P_times_HTransposed = self.P @ np.transpose(H)
 
        S = H @ P_times_HTransposed + self.R
        K = P_times_HTransposed @ np.linalg.inv(S)
 
        z = (y - H@self.xHat)
        z[2] = wrap_to_pi(z[2])
 
        # K es 4x3 -- aunque solo se mide x,y,theta, esta correccion SI
        # actualiza 'b' tambien, via la correlacion acumulada en P.
        self.xHat += K @ z
        self.xHat[2] = wrap_to_pi(self.xHat[2])
 
        self.P = (self.I - K@H) @ self.P
 
        return
 
#endregion
 
class PathFollower(Node):
 
    def __init__(self):
      super().__init__('path_follower')
 
      # define new parameters for node to use
      self.declare_parameter('node_values', [0,8,10])
      self.waypoints = list(self.get_parameter("node_values").get_parameter_value().integer_array_value)
 
      self.declare_parameter('desired_speed', [0.4])
      self.desired_speed = list(self.get_parameter("desired_speed").get_parameter_value().double_array_value)
 
 
      self.declare_parameter('visualize_pose', [False])
      self.pose_visualize_flag = list(self.get_parameter("visualize_pose").get_parameter_value().bool_array_value)[0]
 
      '''
      ================= For future reference =================
 
      If using the nav_to_pose on virtual qcar these are the values to use if the QCar starts close to node 10
 
      Rotation for virtual
      33.0
      Translation for virtual
      1.05,0.9
 
      set self.scale to 0.975
 
      If using the nav_to_pose on physical qcar but starting close to node 10
      Rotation
      44.0
      Translation
      1.15,0.55
      '''
 
      self.scale = 1.0
 
      self.declare_parameter('rotation_offset', [90.0])
      self.rotation_offset = list(self.get_parameter("rotation_offset").get_parameter_value().double_array_value)
 
      self.declare_parameter('translation_offset', [0.0,0.0])
      self.translation_offset = list(self.get_parameter("translation_offset").get_parameter_value().double_array_value)
 
 
      self.declare_parameter('start_path', [False])#Change to True to start path following 
      self.path_execute_flag = list(self.get_parameter("start_path").get_parameter_value().bool_array_value)[0]
 
      self.add_on_set_parameters_callback(self.parameter_update_callback)
 
      # Declare and acquire `target_frame` parameter
      self.target_frame = self.declare_parameter(
        'target_frame', 'base_link').get_parameter_value().string_value
 
      self.tf_buffer = Buffer()
      self.tf_listener = TransformListener(self.tf_buffer, self)
 
      # parameters common to all methods
      self.dt = 1/200
 
      # Initial estimates for QCar state [x, y, theta, b] and covariance (P)
      # b0 = 0 porque imu_bias_corrector.py ya resto un bias estatico
      # aguas arriba -- este estado solo rastrea lo que sobra (deriva).
      self.declare_parameter('p_b0', 0.01)  # incertidumbre inicial de b -- ajustar con std de calibracion / N si se conecta ese dato despues
      p_b0 = self.get_parameter('p_b0').get_parameter_value().double_value
 
      x0 = np.zeros((4,1))
      P0 = np.diagflat([1.0, 1.0, 1.0, p_b0])
 
      # R_combined: covarianza de la medicion de Cartographer.
      # CORREGIDO (sesion de hoy): estaba en 0.0001 -- demasiado chico.
      # Con una R asi de diminuta, corrigiendo a 200Hz (self.dt = 1/200,
      # ver tf_timer), el Kalman gain sale ~1 en cada correccion: el EKF
      # descarta casi por completo su propia prediccion (gyro) y se pega
      # al TF crudo cada 5ms. Como Cartographer NO genera 200 correcciones
      # LiDAR independientes por segundo (~10Hz reales, resto extrapolado
      # -- ver analisis de esta sesion), esto se traducia en theta
      # "congelado" -- exactamente el sintoma de "no puede girar" con
      # kp=1, kd=0. Subido a 0.01 -- deja que la prediccion del gyro
      # (real, 200Hz) tenga peso real entre correcciones. Punto de
      # partida, no valor final -- falta calibrar con datos reales.
      R_combined = np.diagflat([0.01, 0.01, 0.01])
 
      # q_b: cuanto se le permite moverse a 'b' por paso (rad/s, "bias_dot").
      # Valor de arranque conservador -- calibrar con datos de deriva larga.
      self.declare_parameter('q_b', 1e-6)
      q_b = self.get_parameter('q_b').get_parameter_value().double_value
 
      self.qcar2_ekf = QcarEKF(
        x0=x0,
        P0=P0,
        Q=np.diagflat([0.01, 0.01, 0.01, q_b]),
        R=R_combined)
      self.pose_ekf = np.zeros((4,1))
 
 
      # timer for both pose and gyro EKF
      self.yaw = 0
      # butterworth filter parameters
      self.cutoff_frequency_filter = 15.0
      self.a1, self.b1 = self.filter_coefficients(self.cutoff_frequency_filter,self.dt)
 
      self.path_control_timer = self.create_timer(self.dt, self.path_planner)
 
      # Waypoint and path specific settings
 
      self.timer = self.create_timer(self.dt, self.tf_timer)
      self.translation = [0,0,0]
      self.rotation =[0,0,0]
      self.wp  = SDCSRoadMap().generate_path(self.waypoints)*self.scale
      self.N = len(self.wp[0, :])
      self.wpi = 0
      self.wp_prior = []
      self.current_steering =0
 
      self.publisher = self.create_publisher(Twist,'/cmd_vel_nav', 1)
      self.cyclic = False
      self.max_steering_angle = 1.0
 
      self.joint_state_subscriber = self.create_subscription(JointState, '/qcar2_joint',self.joint_state_callback, 1)
      self.qcar2_measurred_speed = 0
 
      self.object_detection_flag = self.create_subscription(Bool, '/motion_enable',self.object_detector_callback, 1)
      self.motion_flag = True
      self.path_complete = False
 
      self.imu_subscrition = self.create_subscription(Imu, '/qcar2_imu/bias_corrected_200hz',self.imu_callback, 10)
      self.gyroscope = [0,0,0]
 
      self.path_publisher_topic = self.create_publisher(Path, '/planned_path',1)
 
      self.path_status_publisher = self.create_publisher(Bool, '/path_status',1)
 
      # Diagnostico interno completo, para grabar en rosbag y analizar
      # todo el panorama junto (theta EKF, psi, delta, steering, bias, etc.)
      # Orden de self.nav_diag: ver comentario en path_planner() donde se
      # arma diag_msg.data -- 13 valores, indices 0-12.
      self.nav_diag_publisher = self.create_publisher(Float64MultiArray, '/nav_diag', 10)
 
      # Multiscope info
      self.t0 = time.time()
      self.t_plot = 0
      self.plot_visualized = False
      self.scopeTimer = self.create_timer(0.1, self.scopeDataTimer)
 
 
    def parameter_update_callback(self, params):
        for param in params:
 
          if param.name == 'node_values' and param.type_== param.Type.INTEGER_ARRAY:
              # Navigation specific variables
              self.waypoints = list(param.value)
              # print(self.waypoints)
              self.wp  = SDCSRoadMap().generate_path(self.waypoints)*0.975
              self.N = len(self.wp[0, :])
              self.wpi = 0
              self.previous_steering_value = 0
              self.path_complete = False
              self.get_logger().info('nodes updated!')
              print(self.waypoints)
 
          elif param.name == 'desired_speed' and param.type_== param.Type.DOUBLE_ARRAY:
              self.desired_speed = list(param.value)
              self.get_logger().info('new desired speed...')
              print(self.desired_speed)
 
          elif param.name == 'rotation_offset' and param.type_== param.Type.DOUBLE_ARRAY:
              self.rotation_offset = list(param.value)
 
          elif param.name == 'translation_offset' and param.type_== param.Type.DOUBLE_ARRAY:
              self.translation_offset = list(param.value)
          elif param.name == 'start_path' and param.type_== param.Type.BOOL_ARRAY:
              self.path_execute_flag = list(param.value)[0]
              self.get_logger().info('path status changed!')
 
          elif param.name == 'visualize_pose' and param.type_== param.Type.BOOL_ARRAY:
              self.pose_visualize_flag = list(param.value)[0]
              if self.pose_visualize_flag and not self.plot_visualized:
                self.get_logger().info('Pose performance to be displayed.. Note: visualizing pose will impact driving performance...')
 
                tf = 200
 
                self.steeringScope = MultiScope(
                      rows=4,
                      cols=1,
                      title='Vehicle Steering Control',
                      fps=10
                  )
 
                self.steeringScope.addAxis(
                      row=0,
                      col=0,
                      timeWindow=tf,
                      yLabel='x Position [m]',
                      yLim=(-2.5, 2.5)
                  )
                self.steeringScope.axes[0].attachSignal(name='x_meas')
                self.steeringScope.axes[0].attachSignal(name='x_ekf')
 
                self.steeringScope.addAxis(
                      row=1,
                      col=0,
                      timeWindow=tf,
                      yLabel='y Position [m]',
                      yLim=(-1, 6)
                  )
                self.steeringScope.axes[1].attachSignal(name='y_meas')
                self.steeringScope.axes[1].attachSignal(name='y_ekf')
 
                self.steeringScope.addAxis(
                      row=2,
                      col=0,
                      timeWindow=tf,
                      yLabel='steering cmd [rad]',
                      yLim=(-0.6,0.6)
                  )
                self.steeringScope.axes[2].attachSignal(name='delta')
 
                self.steeringScope.addAxis(
                      row=3,
                      col=0,
                      timeWindow=tf,
                      yLabel='heading',
                      yLim=(-np.pi,np.pi)
                  )
                self.steeringScope.axes[3].attachSignal(name='theta_meas')
                self.steeringScope.axes[3].attachSignal(name='theta_EKF_sf')
 
                self.plot_visualized = True
              
              elif self.pose_visualize_flag and self.plot_visualized:
                self.get_logger().info('visualization running...')
 
              elif not self.pose_visualize_flag and self.plot_visualized:
                self.plot_visualized = False
 
          return SetParametersResult(successful=True)
  
    def filter_coefficients(self, freq,dt):
      nyq_freq = 0.5*(1/dt)
      norm_cut = freq/nyq_freq
 
 
      b, a = signal.butter(2,norm_cut)
      self.hist = {
          'gyro': {'in': [0.0]*3, 'out': [0.0]*3},
          }
 
      return a,b
   
    def apply_filter(self, key, new_input, a,b):
        h = self.hist[key]
        h['in'] = [new_input] + h['in'][:2]
        y = (
            b[0]*h['in'][0] +
            b[1]*h['in'][1] +
            b[2]*h['in'][2] -
            a[1]*h['out'][0] -
            a[2]*h['out'][1]
        )
        h['out'] = [y] + h['out'][:2]
        return y
 
    def object_detector_callback(self, msg):
      self.motion_flag = msg.data
      # self.get_logger().info(f"motion Falg received was:{self.motion_flag}")
 
    def joint_state_callback(self, msg):
      self.qcar2_measurred_speed = (msg.velocity[0]/(720.0*4.0))*((13.0*19.0)/(70.0*30.0))*(2.0*np.pi)*0.033
 
    def imu_callback(self,msg):
       self.gyroscope = [msg.angular_velocity.x,msg.angular_velocity.y,msg.angular_velocity.z]
 
    def path_publisher(self):
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = "map"
        # path_msg.header.frame_id = "map_rotated"
 
        for i in range(self.wpi):
        # for i in range(self.N):
          if i >= self.N:
             i = self.N-1
          pose = PoseStamped()
          wp_1_mod = [0,0]
 
          angle_offset= self.rotation_offset[0]
          R_QLabs_ROS = np.array([[np.cos(-angle_offset*np.pi/180), -np.sin(-angle_offset*np.pi/180)],
                                  [np.sin(-angle_offset*np.pi/180),np.cos(-angle_offset*np.pi/180)]])
          t = np.array([self.translation_offset[0],self.translation_offset[1]])
          wp_1_mod = ([self.wp[0,i],self.wp[1,i]]+t)@R_QLabs_ROS
          pose.header.stamp = self.get_clock().now().to_msg()
          # pose.header.frame_id = "map_rotated"
          pose.header.frame_id = "map"
          pose.pose.position.x =wp_1_mod[0]
          pose.pose.position.y =wp_1_mod[1]
 
          path_msg.poses.append(pose)
 
        self.path_publisher_topic.publish(path_msg)
 
    def path_planner(self):
 
        max_speed = 1.5
        enable = 1
        speed_command = self.desired_speed[0]
        # self.max_rate = np.clip(0.01*(speed_command)/max_speed,0.001,0.1)
        skip_index = 0
 
        self.t_plot = time.time()-self.t0
 
        # update ekf_filter
        self.ekf_filter_timer()
 
        # publish latest path value based on current waypoint every 2 seconds
        if round(self.t_plot) % 2 == 0:
          self.path_publisher()
 
        # --- DIAGNOSTICO INCONDICIONAL (fuera del try, quitar despues) ---
        # Este SI se imprime siempre, sin importar path_complete/exceptions.
        # Si el otro [DIAG] nunca aparece, esto nos dice por que: si N es
        # chico/raro, si path_complete ya esta en True desde el inicio, o
        # si el flag de arranque nunca se activo.
        if not hasattr(self, '_diag2_last_t') or (self.t_plot - self._diag2_last_t) >= 1.0:
            self._diag2_last_t = self.t_plot
            self.get_logger().info(
                f'[DIAG2] path_complete={self.path_complete} | '
                f'path_execute_flag={self.path_execute_flag} | '
                f'motion_flag={self.motion_flag} | '
                f'wpi={self.wpi} | N={self.N} | '
                f'wp_shape={np.shape(self.wp)}'
            )
        # --- FIN DIAGNOSTICO INCONDICIONAL ---
 
        try:
          if not self.path_complete :
 
            # extract waypoints of interest
            wp_1 = np.array(self.wp[:, self.wpi])
            wp_2 = np.array(self.wp[:, self.wpi+1])
 
            wp_1_mod = [0,0]
 
            angle_offset= self.rotation_offset[0]
 
            R_QLabs_ROS = np.array([[np.cos(-angle_offset*np.pi/180), -np.sin(-angle_offset*np.pi/180)],
                                    [np.sin(-angle_offset*np.pi/180),np.cos(-angle_offset*np.pi/180)]])
            t = np.array([self.translation_offset[0],self.translation_offset[1]])
            wp_1_mod = (wp_1+t)@R_QLabs_ROS
 
            L= 0.256
 
            # Pose/heading para la geometria de pure pursuit: SIEMPRE del
            # EKF (xHat), nunca del TF crudo de Cartographer.
            #
            # CORREGIDO (sesion de hoy): antes habia un try/except que
            # sobreescribia esto con self.translation/self.yaw (TF crudo)
            # cada vez que esos atributos existian -- lo cual es casi
            # siempre, una vez que llega el primer TF. En la practica,
            # pure pursuit nunca estaba usando el EKF para su geometria,
            # pese a que el comentario original decia lo contrario.
            #
            # Por que importa: self.yaw se lee directo de tf_timer() sin
            # ningun suavizado -- y ya confirmamos (analisis con G) que
            # Cartographer publica pose a 200Hz pero solo genera ~10
            # correcciones LiDAR reales por segundo; el resto son poses
            # extrapoladas, potencialmente repetidas/rezagadas entre si.
            # Usar ese valor crudo directo en la formula de rotacion
            # (R = f(th)) significa que cualquier atraso de 'th' se
            # traduce directo en un angulo de direccion mal calculado --
            # eso es lo que se vio como "resistencia al giro".
            #
            # El EKF predice theta con el gyro (200Hz, real) entre
            # correcciones de Cartographer, y solo se ancla al TF cuando
            # corrige -- exactamente el comportamiento que se queria.
            th = self.qcar2_ekf.xHat[2,0]
            p = [self.qcar2_ekf.xHat[0,0],self.qcar2_ekf.xHat[1,0]]
 
            v = [wp_1_mod[0]-p[0],wp_1_mod[1]-p[1]]
            R = np.array([[np.cos(th), -np.sin(th)],[np.sin(th),np.cos(th)]])
            v_car = v@R
 
            WaypointDist = np.linalg.norm(v_car)
            psi = np.arctan2(v_car[1],v_car[0])
 
 
            # pure pursuit algorithm
            delta = np.arctan2(2*L*np.sin(psi),WaypointDist)
            dist = np.linalg.norm([p[0]-wp_1_mod[0],p[1]-wp_1_mod[1]])
 
            # --- Publisher de diagnostico interno (para grabar en rosbag) ---
            # Antes esto solo se imprimia 1 vez/seg en consola -- no era
            # grabable ni cruzable con el resto de los topicos. Ahora se
            # publica cada ciclo (200Hz) como Float64MultiArray, para poder
            # correlacionar con /tf, /qcar2_imu, /qcar2_joint_filtered, etc.
            # en un analisis posterior, en vez de adivinar una variable a
            # la vez.
            self._diag_psi = psi
            self._diag_delta = delta
            self._diag_dist = dist
            self._diag_wp1_mod = wp_1_mod
            # --- fin captura, steering se agrega mas abajo antes de publicar ---
 
            lookahead_dist = speed_command*0.5
            skip_index = int(speed_command*(speed_command/max_speed))
            lookahead_dist = np.clip(lookahead_dist,2*L,0.75)
            skip_index = np.clip(skip_index,5,60)
 
 
 
            if dist<lookahead_dist:
              if self.wpi < self.N-2:
                self.wpi += skip_index
 
            self.wpi = np.clip(self.wpi,0,self.N-5)
 
            if self.wpi >= self.N-5:
              if dist <0.4:
                speed_command = 0.0
                steering = 0.0
                self.wp_prior = self.wp
                self.path_complete = True
 
            if self.wpi > self.N-100 :
               speed_command = 0.2
 
            Kp_steering = 1
            kd_steering = 0.09
 
            gyro_filtered = self.apply_filter('gyro', self.gyroscope[2],self.a1, self.b1)
 
            steering = np.clip(
                          Kp_steering*delta-gyro_filtered*kd_steering,
                          -self.max_steering_angle,
                          self.max_steering_angle)
 
            self.current_steering = steering
 
            # Publica el diagnostico completo de este ciclo -- todo lo que
            # antes vivia solo en variables locales o en el print de 1Hz.
            diag_msg = Float64MultiArray()
            diag_msg.data = [
                float(th),                          # 0: theta EKF (rad)
                float(p[0]), float(p[1]),           # 1,2: posicion EKF (x,y)
                float(getattr(self, 'yaw', float('nan'))),  # 3: yaw crudo de Cartografo
                float(self._diag_psi),              # 4: psi (angulo al waypoint, rad)
                float(self._diag_delta),            # 5: delta geometrico puro (rad)
                float(steering),                    # 6: steering final (post Kp/Kd/clip)
                float(gyro_filtered),               # 7: gyro filtrado (Butterworth interno 15Hz)
                float(self._diag_dist),             # 8: distancia al waypoint (m)
                float(self.wpi),                    # 9: indice de waypoint actual
                float(self.qcar2_ekf.xHat[3,0]),    # 10: bias estimado del EKF
                float(self._diag_wp1_mod[0]), float(self._diag_wp1_mod[1]),  # 11,12: waypoint objetivo (x,y)
            ]
            self.nav_diag_publisher.publish(diag_msg)
 
 
 
        except KeyboardInterrupt:
          speed_command = 0.0
          steering = 0.0
        if self.path_execute_flag== True:
          if self.motion_flag == True:
              enable = 1.0
        if self.path_execute_flag == False or self.motion_flag == False or self.path_complete:
            enable = 0.0
 
 
        # publishing commands
        self.nav_command(enable, speed_command)
        self.path_status()
 
    def nav_command(self,enable, speed_command):
      QCarCommands = Twist()
      QCarCommands.linear.x = enable*np.clip(speed_command*np.power(np.cos(self.current_steering),1),0.05,0.7)
      QCarCommands.angular.z = enable*self.current_steering
      self.publisher.publish(QCarCommands)
 
    def path_status(self):
      msg = Bool()
      msg.data = self.path_complete
      self.path_status_publisher.publish(msg)
 
    def tf_timer(self):
      from_frame_rel= "map"
      to_frame_rel = self.target_frame
 
      try:
        t = self.tf_buffer.lookup_transform(
        from_frame_rel,
        to_frame_rel,
        rclpy.time.Time())
        self.translation = t.transform.translation
        rotation = [t.transform.rotation.x,
                    t.transform.rotation.y,
                    t.transform.rotation.z,
                    t.transform.rotation.w]
        roll, pitch,self.yaw = R.from_quat(rotation).as_euler('xyz')
 
        # Correccion directa desde Cartographer (map -> target_frame).
        # Antes esto pasaba primero por un GyroKF separado para el heading
        # -- ahora theta se corrige junto con x,y en el mismo EKF de 4
        # estados, y esa misma correccion tambien ajusta el bias 'b' via
        # la correlacion que P acumula en la prediccion.
        y = np.array([
                  [self.translation.x],
                  [self.translation.y],
                  [self.yaw]
              ])
 
        self.qcar2_ekf.correction(y)
      except TransformException as ex:
          self.get_logger().info(f'Could not transform {to_frame_rel} to {from_frame_rel}: {ex}')
          return
 
    def ekf_filter_timer(self):
      # Prediccion con velocidad medida (encoder) + velocidad angular
      # medida (gyro, ya filtrado y bias-corregido por
      # imu_bias_corrector.py aguas arriba) -- 'delta' (steering) ya NO
      # se usa aqui para el heading, porque es comandado, no medido.
      speed = self.qcar2_measurred_speed
 
      try:
         omega = self.gyroscope[2]
      except AttributeError:
         omega = 0.0
 
      self.qcar2_ekf.prediction(self.dt, [speed, omega])
 
    def scopeDataTimer(self):
      if self.pose_visualize_flag:
        p = [self.qcar2_ekf.xHat[0,0],self.qcar2_ekf.xHat[1,0],self.qcar2_ekf.xHat[2,0]]
 
        if self.t_plot >200:
          self.t0 = time.time()
          self.steeringScope.axes[0].clean()
          self.steeringScope.axes[1].clean()
          self.steeringScope.axes[2].clean()
          self.steeringScope.axes[3].clean()
          MultiScope.refreshAll()
 
        try:
          x_ref = self.translation.x
          y_ref = self.translation.y
        except AttributeError:
          x_ref = 0
          y_ref = 0
        self.steeringScope.axes[0].sample(self.t_plot, [x_ref, p[0] ])
        self.steeringScope.axes[1].sample(self.t_plot, [y_ref, p[1]])
        self.steeringScope.axes[2].sample(self.t_plot, [self.current_steering])
        self.steeringScope.axes[3].sample(self.t_plot, [self.yaw,self.qcar2_ekf.xHat[2,0]])
 
        MultiScope.refreshAll()     
      
      else:
        try:
            self.steeringScope.graphicsLayoutWidget.close()
            self.get_logger().info('previous scope closed...')
 
        except AttributeError:
          # self.get_logger().info('no visualization running...')
          pass
 
 
 
def main():
 
  # Start the ROS 2 Python Client Library
  rclpy.init()
 
  node = PathFollower()
  try:
      rclpy.spin(node)
  except KeyboardInterrupt:
      pass
 
  rclpy.shutdown()
 
if __name__ == '__main__':
  main()