#! /usr/bin/env python3

import time

import numpy as np
import scipy.signal as signal
from scipy.spatial.transform import Rotation as Rotation

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Path
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState
from std_msgs.msg import Bool, Float64MultiArray
from tf2_ros import Buffer, TransformException, TransformListener

from hal.products.mats import SDCSRoadMap
from pal.utilities.math import wrap_to_pi


class QcarEKF:
    """Six-state local EKF: [x, y, theta, v, omega, b]."""

    def __init__(self, x0, P0, wheelbase, a_max, alpha_max,
                 sigma_bias_rw, sigma_encoder, sigma_ackermann, sigma_gyro,
                 R_cart):
        self.wheelbase = wheelbase
        self.a_max = a_max
        self.alpha_max = alpha_max
        self.sigma_bias_rw = sigma_bias_rw
        self.R_encoder = np.array([[sigma_encoder ** 2]])
        self.R_ackermann = np.array([[sigma_ackermann ** 2]])
        self.R_gyro = np.array([[sigma_gyro ** 2]])
        self.R_cart = R_cart
        self.identity = np.eye(6)
        self.xHat = x0
        self.P = P0
        self.previous_encoder_observation = None
        self.previous_gyro_observation = None
        self.current_Sv = (0.05 * a_max * 0.005) ** 2
        self.current_Somega = (0.05 * alpha_max * 0.005) ** 2
        self.current_Qbb = sigma_bias_rw ** 2

    def compute_process_noise(self, dt, encoder_velocity=None, gyro_z=None):
        if encoder_velocity is not None:
            if self.previous_encoder_observation is None:
                dv = 0.0
            else:
                dv = encoder_velocity - self.previous_encoder_observation
            a_eff = np.clip(abs(dv) / dt, 0.05 * self.a_max, self.a_max)
            self.current_Sv = (a_eff * dt) ** 2
            self.previous_encoder_observation = encoder_velocity

        if gyro_z is not None:
            if self.previous_gyro_observation is None:
                domega = 0.0
            else:
                domega = gyro_z - self.previous_gyro_observation
            alpha_eff = np.clip(
                abs(domega) / dt, 0.05 * self.alpha_max, self.alpha_max)
            self.current_Somega = (alpha_eff * dt) ** 2
            self.previous_gyro_observation = gyro_z

        theta = self.xHat[2, 0]
        Gv = np.array([
            [0.5 * dt * np.cos(theta)], [0.5 * dt * np.sin(theta)],
            [0.0], [1.0], [0.0], [0.0]
        ])
        Gw = np.array([
            [0.0], [0.0], [0.5 * dt], [0.0], [1.0], [0.0]
        ])
        Q = (Gv @ Gv.T) * self.current_Sv
        Q += (Gw @ Gw.T) * self.current_Somega
        self.current_Qbb = self.sigma_bias_rw ** 2 * dt
        Q[5, 5] += self.current_Qbb
        return Q

    def motion_model(self, dt):
        theta = self.xHat[2, 0]
        return self.xHat + dt * np.array([
            [self.xHat[3, 0] * np.cos(theta)],
            [self.xHat[3, 0] * np.sin(theta)],
            [self.xHat[4, 0]],
            [0.0], [0.0], [0.0]
        ])

    def state_jacobian(self, dt):
        theta = self.xHat[2, 0]
        v = self.xHat[3, 0]
        return np.array([
            [1, 0, -v * dt * np.sin(theta), dt * np.cos(theta), 0, 0],
            [0, 1, v * dt * np.cos(theta), dt * np.sin(theta), 0, 0],
            [0, 0, 1, 0, dt, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ], dtype=float)

    def prediction(self, dt, encoder_velocity=None, gyro_z=None):
        F = self.state_jacobian(dt)
        self.P = F @ self.P @ F.T + self.compute_process_noise(
            dt, encoder_velocity, gyro_z)
        self.xHat = self.motion_model(dt)
        self.xHat[2, 0] = wrap_to_pi(self.xHat[2, 0])

    def _update(self, measurement, expected, H, R, wrap_index=None):
        residual = measurement - expected
        if wrap_index is not None:
            residual[wrap_index, 0] = wrap_to_pi(residual[wrap_index, 0])
        PHt = self.P @ H.T
        S = H @ PHt + R
        K = np.linalg.solve(S, PHt.T).T
        self.xHat += K @ residual
        self.xHat[2, 0] = wrap_to_pi(self.xHat[2, 0])
        A = self.identity - K @ H
        self.P = A @ self.P @ A.T + K @ R @ K.T
        self.P = 0.5 * (self.P + self.P.T)
        return residual

    def update_encoder(self, velocity):
        H = np.array([[0, 0, 0, 1, 0, 0]], dtype=float)
        return self._update(
            np.array([[velocity]]), np.array([[self.xHat[3, 0]]]), H,
            self.R_encoder)

    def update_ackermann(self, steering):
        v = self.xHat[3, 0]
        H = np.array([[0, 0, 0, -np.tan(steering) / self.wheelbase, 1, 0]])
        expected = np.array([[
            self.xHat[4, 0] - v * np.tan(steering) / self.wheelbase
        ]])
        return self._update(np.array([[0.0]]), expected, H, self.R_ackermann)

    def update_gyro(self, gyro_z):
        H = np.array([[0, 0, 0, 0, 1, 1]], dtype=float)
        expected = np.array([[self.xHat[4, 0] + self.xHat[5, 0]]])
        return self._update(np.array([[gyro_z]]), expected, H, self.R_gyro)

    def cartographer_innovation(self, measurement):
        H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ], dtype=float)
        residual = measurement - self.xHat[:3]
        residual[2, 0] = wrap_to_pi(residual[2, 0])
        PHt = self.P @ H.T
        S = H @ PHt + self.R_cart
        d2 = float(residual.T @ np.linalg.solve(S, residual))
        return residual, d2, S, H

    def accept_cartographer(self, residual, S, H):
        PHt = self.P @ H.T
        K = np.linalg.solve(S, PHt.T).T
        self.xHat += K @ residual
        self.xHat[2, 0] = wrap_to_pi(self.xHat[2, 0])
        A = self.identity - K @ H
        self.P = A @ self.P @ A.T + K @ self.R_cart @ K.T
        self.P = 0.5 * (self.P + self.P.T)


class PathFollower(Node):
    def __init__(self):
        super().__init__('path_follower')

        self.declare_parameter('node_values', [0, 8, 10])
        self.waypoints = list(self.get_parameter('node_values').value)
        self.declare_parameter('desired_speed', [0.4])
        self.desired_speed = list(self.get_parameter('desired_speed').value)
        self.declare_parameter('visualize_pose', [False])
        self.declare_parameter('rotation_offset', [90.0])
        self.declare_parameter('translation_offset', [0.0, 0.0])
        self.declare_parameter('start_path', [False])
        self.declare_parameter('target_frame', 'base_link')
        self.target_frame = self.get_parameter('target_frame').value

        self.scale = 1.0
        self.rotation_offset = list(self.get_parameter('rotation_offset').value)
        self.translation_offset = list(self.get_parameter('translation_offset').value)
        self.path_execute_flag = list(self.get_parameter('start_path').value)[0]
        self.add_on_set_parameters_callback(self.parameter_update_callback)

        self.nominal_dt = 1.0 / 200.0
        self.dt = self.nominal_dt
        self.max_dt = self.declare_parameter('max_dt', 0.1).value
        self.last_filter_time = self.get_clock().now()

        parameter_defaults = {
            'wheelbase': 0.256,
            'p_x0': 0.01,
            'p_y0': 0.01,
            'p_theta0': 0.01,
            'p_v0': 1.0,
            'p_omega0': 1.0,
            'p_b0': 0.01,
            'a_max': 2.0,
            'alpha_max': 2.0,
            'sigma_bias_rw': 1e-4,
            # Static encoder noise floor measured with the vehicle stationary.
            'sigma_encoder': 0.015,
            # Provisional until characterized during a moving run.
            'sigma_ackermann': 0.2,
            # Same filtered/debiased 200 Hz gyro signal consumed by the EKF.
            'sigma_gyro': 0.041,
            # Static Cartographer pose repeatability while stationary.
            'sigma_cart_x': 0.010,
            'sigma_cart_y': 0.006,
            'sigma_cart_theta': 0.008,
            'cartographer_mahalanobis_threshold': 11.345,
            'cartographer_correction_period': 0.1,
        }
        for name, value in parameter_defaults.items():
            self.declare_parameter(name, value)

        x0 = np.zeros((6, 1))
        P0 = np.diag([
            self.get_parameter('p_x0').value,
            self.get_parameter('p_y0').value,
            self.get_parameter('p_theta0').value,
            self.get_parameter('p_v0').value,
            self.get_parameter('p_omega0').value,
            self.get_parameter('p_b0').value
        ])
        R_cart = np.diag([
            self.get_parameter('sigma_cart_x').value ** 2,
            self.get_parameter('sigma_cart_y').value ** 2,
            self.get_parameter('sigma_cart_theta').value ** 2
        ])
        self.cartographer_gate_threshold = self.get_parameter(
            'cartographer_mahalanobis_threshold').value
        self.cartographer_correction_period = self.get_parameter(
            'cartographer_correction_period').value
        self.qcar2_ekf = QcarEKF(
            x0, P0, self.get_parameter('wheelbase').value,
            self.get_parameter('a_max').value,
            self.get_parameter('alpha_max').value,
            self.get_parameter('sigma_bias_rw').value,
            self.get_parameter('sigma_encoder').value,
            self.get_parameter('sigma_ackermann').value,
            self.get_parameter('sigma_gyro').value,
            R_cart)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.translation = None
        self.yaw = 0.0
        self.last_cartographer_stamp_ns = -1
        self.last_cartographer_correction_time = None
        self.cartographer_innovation = np.zeros(3)
        self.cartographer_mahalanobis_d2 = np.nan
        self.cartographer_update_accepted = False
        self.cartographer_update_rejected = False
        self.encoder_residual = np.nan
        self.ackermann_residual = np.nan
        self.gyro_residual = np.nan

        self.gyroscope = np.zeros(3)
        self.imu_received = False
        self.imu_ready = False
        self.imu_new = False
        self.qcar2_measurred_speed = 0.0
        self.encoder_received = False
        self.encoder_new = False
        self.current_steering = 0.0
        self.applied_steering = 0.0
        self.applied_steering_valid = False
        self.applied_command_active = False
        self.motion_flag = True
        self.path_complete = False

        self.publisher = self.create_publisher(Twist, '/cmd_vel_nav', 1)
        self.path_publisher_topic = self.create_publisher(Path, '/planned_path', 1)
        self.path_status_publisher = self.create_publisher(Bool, '/path_status', 1)
        self.nav_diag_publisher = self.create_publisher(Float64MultiArray, '/nav_diag', 10)
        self.create_subscription(JointState, '/qcar2_joint', self.joint_state_callback, 1)
        self.create_subscription(Imu, '/qcar2_imu/bias_corrected_200hz', self.imu_callback, 10)
        self.create_subscription(Bool, '/motion_enable', self.object_detector_callback, 1)

        self.cutoff_frequency_filter = 15.0
        self.filter_a, self.filter_b = self.filter_coefficients(
            self.cutoff_frequency_filter, self.nominal_dt)
        self.path_control_timer = self.create_timer(self.nominal_dt, self.path_planner)
        self.tf_timer_handle = self.create_timer(self.nominal_dt, self.tf_timer)

        self.wp = SDCSRoadMap().generate_path(self.waypoints) * self.scale
        self.N = len(self.wp[0, :])
        self.wpi = 0
        self.wp_prior = []
        self.t0 = time.time()
        self.t_plot = 0.0

    def parameter_update_callback(self, params):
        for param in params:
            if param.name == 'node_values':
                self.waypoints = list(param.value)
                self.wp = SDCSRoadMap().generate_path(self.waypoints) * self.scale
                self.N = len(self.wp[0, :])
                self.wpi = 0
                self.path_complete = False
            elif param.name == 'desired_speed':
                self.desired_speed = list(param.value)
            elif param.name == 'rotation_offset':
                self.rotation_offset = list(param.value)
            elif param.name == 'translation_offset':
                self.translation_offset = list(param.value)
            elif param.name == 'start_path':
                self.path_execute_flag = list(param.value)[0]
        return SetParametersResult(successful=True)

    def filter_coefficients(self, frequency, dt):
        normalized = frequency / (0.5 * (1.0 / dt))
        b, a = signal.butter(2, normalized)
        self.filter_history = {'gyro': {'input': [0.0] * 3, 'output': [0.0] * 3}}
        return a, b

    def apply_filter(self, key, value, a, b):
        history = self.filter_history[key]
        history['input'] = [value] + history['input'][:2]
        output = (b[0] * history['input'][0] + b[1] * history['input'][1]
                  + b[2] * history['input'][2] - a[1] * history['output'][0]
                  - a[2] * history['output'][1])
        history['output'] = [output] + history['output'][:2]
        return output

    def object_detector_callback(self, msg):
        self.motion_flag = msg.data

    def joint_state_callback(self, msg):
        if msg.velocity:
            self.qcar2_measurred_speed = (msg.velocity[0] / (720.0 * 4.0)) * ((13.0 * 19.0) / (70.0 * 30.0)) * (2.0 * np.pi) * 0.033
            self.encoder_received = True
            self.encoder_new = True

    def imu_callback(self, msg):
        self.gyroscope = np.array([
            msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z
        ])
        self.imu_received = True
        self.imu_ready = True
        self.imu_new = True

    def path_publisher(self):
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'
        rotation = np.array([
            [np.cos(-self.rotation_offset[0] * np.pi / 180), -np.sin(-self.rotation_offset[0] * np.pi / 180)],
            [np.sin(-self.rotation_offset[0] * np.pi / 180), np.cos(-self.rotation_offset[0] * np.pi / 180)]
        ])
        offset = np.array(self.translation_offset)
        for index in range(min(self.wpi, self.N)):
            point = ([self.wp[0, index], self.wp[1, index]] + offset) @ rotation
            pose = PoseStamped()
            pose.header = path_msg.header
            pose.pose.position.x = point[0]
            pose.pose.position.y = point[1]
            path_msg.poses.append(pose)
        self.path_publisher_topic.publish(path_msg)

    def path_planner(self):
        if not (self.path_execute_flag and self.motion_flag and not self.path_complete):
            self.applied_steering = 0.0
            self.applied_steering_valid = False
            self.applied_command_active = False
        self.ekf_filter_timer()
        speed_command = self.desired_speed[0]
        if round(time.time() - self.t0) % 2 == 0:
            self.path_publisher()

        if not self.path_complete:
            offset_rotation = np.array([
                [np.cos(-self.rotation_offset[0] * np.pi / 180), -np.sin(-self.rotation_offset[0] * np.pi / 180)],
                [np.sin(-self.rotation_offset[0] * np.pi / 180), np.cos(-self.rotation_offset[0] * np.pi / 180)]
            ])
            waypoint = (self.wp[:2, self.wpi] + np.array(self.translation_offset)) @ offset_rotation
            theta = self.qcar2_ekf.xHat[2, 0]
            position = self.qcar2_ekf.xHat[:2, 0]
            vector = waypoint - position
            body_vector = vector @ np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            distance = np.linalg.norm(body_vector)
            psi = np.arctan2(body_vector[1], body_vector[0])
            wheelbase = self.qcar2_ekf.wheelbase
            steering = np.arctan2(2 * wheelbase * np.sin(psi), distance)
            if np.linalg.norm(vector) < np.clip(speed_command * 0.5, 2 * wheelbase, 0.75):
                self.wpi = min(self.wpi + max(5, int(speed_command ** 2 / 1.5)), self.N - 5)
            if self.wpi >= self.N - 5 and np.linalg.norm(vector) < 0.4:
                speed_command = 0.0
                self.path_complete = True
            gyro_for_control = self.gyroscope[2] if self.imu_received else 0.0
            gyro_filtered = self.apply_filter('gyro', gyro_for_control, self.filter_a, self.filter_b)
            self.current_steering = np.clip(steering - 0.09 * gyro_filtered, -1.0, 1.0)
            self.publish_diagnostics(theta, position, psi, steering, gyro_filtered, distance, waypoint)

        enable = float(self.path_execute_flag and self.motion_flag and not self.path_complete)
        self.nav_command(enable, speed_command)
        self.path_status()

    def publish_diagnostics(self, theta, position, psi, steering, gyro_filtered, distance, waypoint):
        msg = Float64MultiArray()
        msg.data = [
            float(self.qcar2_ekf.xHat[0, 0]), float(self.qcar2_ekf.xHat[1, 0]),
            float(self.qcar2_ekf.xHat[2, 0]), float(self.qcar2_ekf.xHat[3, 0]),
            float(self.qcar2_ekf.xHat[4, 0]), float(self.qcar2_ekf.xHat[5, 0]),
            float(self.encoder_residual), float(self.ackermann_residual),
            float(self.gyro_residual),
            float(self.cartographer_innovation[0]), float(self.cartographer_innovation[1]),
            float(self.cartographer_innovation[2]), float(self.cartographer_mahalanobis_d2),
            float(self.cartographer_update_accepted), float(self.cartographer_update_rejected),
            float(self.qcar2_ekf.P[0, 0]), float(self.qcar2_ekf.P[1, 1]),
            float(self.qcar2_ekf.P[2, 2]), float(self.qcar2_ekf.P[3, 3]),
            float(self.qcar2_ekf.P[4, 4]), float(self.qcar2_ekf.P[5, 5]),
            float(self.qcar2_ekf.current_Sv), float(self.qcar2_ekf.current_Somega),
            float(self.qcar2_ekf.current_Qbb),
            float(self.qcar2_measurred_speed), float(self.gyroscope[2]),
            float(self.applied_steering), float(self.dt),
            float(self.yaw), float(psi), float(steering), float(gyro_filtered),
            float(distance), float(self.wpi), float(waypoint[0]), float(waypoint[1]),
            float(self.cartographer_gate_threshold), float(self.last_cartographer_stamp_ns) * 1e-9
        ]
        self.nav_diag_publisher.publish(msg)

    def nav_command(self, enable, speed_command):
        command = Twist()
        self.applied_command_active = bool(enable)
        self.applied_steering = self.current_steering if self.applied_command_active else 0.0
        self.applied_steering_valid = self.applied_command_active
        command.linear.x = enable * np.clip(speed_command * np.cos(self.applied_steering), 0.05, 0.7)
        command.angular.z = enable * self.applied_steering
        self.publisher.publish(command)

    def path_status(self):
        msg = Bool()
        msg.data = self.path_complete
        self.path_status_publisher.publish(msg)

    def tf_timer(self):
        try:
            transform = self.tf_buffer.lookup_transform('map', self.target_frame, rclpy.time.Time())
            stamp_ns = transform.header.stamp.sec * 1000000000 + transform.header.stamp.nanosec
            if stamp_ns <= 0 or stamp_ns == self.last_cartographer_stamp_ns:
                return
            now = self.get_clock().now()
            if self.last_cartographer_correction_time is not None:
                elapsed = (now - self.last_cartographer_correction_time).nanoseconds * 1e-9
                if elapsed < self.cartographer_correction_period:
                    return
            self.translation = transform.transform.translation
            quaternion = transform.transform.rotation
            self.yaw = Rotation.from_quat([quaternion.x, quaternion.y, quaternion.z, quaternion.w]).as_euler('xyz')[2]
            measurement = np.array([[self.translation.x], [self.translation.y], [self.yaw]])
            residual, d2, S, H = self.qcar2_ekf.cartographer_innovation(measurement)
            self.cartographer_innovation = residual[:, 0]
            self.cartographer_mahalanobis_d2 = d2
            self.cartographer_update_accepted = d2 <= self.cartographer_gate_threshold
            self.cartographer_update_rejected = not self.cartographer_update_accepted
            if self.cartographer_update_accepted:
                self.qcar2_ekf.accept_cartographer(residual, S, H)
            self.last_cartographer_stamp_ns = stamp_ns
            self.last_cartographer_correction_time = now
        except TransformException:
            return

    def ekf_filter_timer(self):
        now = self.get_clock().now()
        elapsed = (now - self.last_filter_time).nanoseconds * 1e-9
        self.last_filter_time = now
        if elapsed <= 0.0:
            return
        self.dt = min(elapsed, self.max_dt)
        self.qcar2_ekf.prediction(
            self.dt,
            self.qcar2_measurred_speed if self.encoder_received else None,
            self.gyroscope[2] if self.imu_ready else None)
        if self.encoder_new:
            self.encoder_residual = float(
                self.qcar2_ekf.update_encoder(self.qcar2_measurred_speed)[0, 0])
            self.encoder_new = False
        if self.applied_steering_valid and self.applied_command_active:
            self.ackermann_residual = float(
                self.qcar2_ekf.update_ackermann(self.applied_steering)[0, 0])
        if self.imu_ready and self.imu_new:
            self.gyro_residual = float(
                self.qcar2_ekf.update_gyro(self.gyroscope[2])[0, 0])
            self.imu_new = False


def main(args=None):
    rclpy.init(args=args)
    node = PathFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
