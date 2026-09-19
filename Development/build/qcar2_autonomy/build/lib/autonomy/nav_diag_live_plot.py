#!/usr/bin/env python3

import os
import threading
import time
from collections import deque

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

import rclpy


# /nav_diag layout published by qcar2_autonomy/autonomy/nav_to_pose.py.
FIELDS = {
    'x': 0, 'y': 1, 'theta': 2, 'v': 3, 'omega': 4, 'bias': 5,
    'encoder_residual': 6, 'ackermann_residual': 7, 'gyro_residual': 8,
    'cart_x': 9, 'cart_y': 10, 'cart_theta': 11, 'cart_d2': 12,
    'cart_accepted': 13, 'cart_rejected': 14,
    'Pxx': 15, 'Pyy': 16, 'Ptheta': 17, 'Pvv': 18, 'Pomega': 19, 'Pbias': 20,
    'Sv': 21, 'Somega': 22, 'Qbb': 23,
    'encoder_velocity': 24, 'gyro_z': 25, 'applied_steering': 26, 'dt': 27,
    'cart_yaw': 28, 'psi': 29, 'steering': 30, 'gyro_filtered': 31,
    'distance': 32, 'waypoint_index': 33, 'waypoint_x': 34, 'waypoint_y': 35,
    'cart_threshold': 36, 'cart_stamp': 37,
}


class NavDiagLivePlot(Node):
    def __init__(self, history_seconds=30.0, refresh_hz=12.0):
        super().__init__('nav_diag_live_plot')
        self.get_logger().info(
            f'Matplotlib backend: {matplotlib.get_backend()} | '
            f'DISPLAY={os.environ.get("DISPLAY", "<unset>")} | '
            f'ROS_DOMAIN_ID={os.environ.get("ROS_DOMAIN_ID", "<unset>")}'
        )
        self.history_seconds = history_seconds
        self.refresh_hz = refresh_hz
        self.lock = threading.Lock()
        self.samples = deque(maxlen=12000)
        self.last_sample_time = None
        self.last_callback_wall_time = None
        self.received_sample_count = 0
        self.invalid_schema_count = 0
        self.status_text = 'Waiting for /nav_diag...'
        self.latest = None
        self.create_subscription(Float64MultiArray, '/nav_diag', self.callback, 50)
        self.create_timer(2.0, self.watchdog_callback)
        self.get_logger().info('Waiting for /nav_diag...')

    def callback(self, message):
        values = np.asarray(message.data, dtype=float)
        self.received_sample_count += 1
        self.last_callback_wall_time = time.monotonic()
        if self.received_sample_count == 1:
            self.get_logger().info(
                f'Received first /nav_diag sample: {values.size} fields'
            )
        if values.size != len(FIELDS):
            self.invalid_schema_count += 1
            self.status_text = (
                f'/nav_diag schema mismatch: received {values.size} fields, '
                f'expected {len(FIELDS)}; rebuild/source path_follower'
            )
            if self.invalid_schema_count == 1:
                self.get_logger().error(self.status_text)
            return
        timestamp = values[FIELDS['cart_stamp']]
        if not np.isfinite(timestamp):
            timestamp = self.get_clock().now().nanoseconds * 1e-9
        with self.lock:
            self.samples.append((timestamp, values.copy()))
            self.latest = values.copy()
            self.last_sample_time = timestamp
            self.status_text = 'Receiving /nav_diag'

    def watchdog_callback(self):
        if self.last_callback_wall_time is None:
            self.status_text = 'Waiting for /nav_diag...'
            self.get_logger().warning('Waiting for /nav_diag...')
            return
        age = time.monotonic() - self.last_callback_wall_time
        if age > 2.0:
            self.status_text = f'/nav_diag has no recent messages ({age:.1f}s)'
            self.get_logger().warning(self.status_text)
        elif self.invalid_schema_count and self.latest is None:
            self.get_logger().warning(
                f'Messages are arriving at /nav_diag, but all '
                f'{self.invalid_schema_count} samples have the wrong field count'
            )

    def snapshot(self):
        with self.lock:
            if not self.samples:
                return None, None
            timestamps = np.asarray([item[0] for item in self.samples], dtype=float)
            values = np.asarray([item[1] for item in self.samples], dtype=float)
        end = timestamps[-1]
        keep = timestamps >= end - self.history_seconds
        return timestamps[keep] - end, values[keep]


class Dashboard:
    def __init__(self, node):
        self.node = node
        self.figure, axes = plt.subplots(4, 2, figsize=(15, 11), constrained_layout=True)
        self.axes = axes.ravel()
        self.figure.canvas.manager.set_window_title('QCar2 EKF V1 Live Diagnostics')
        self.lines = {}
        self._configure_axes()
        self.animation = FuncAnimation(
            self.figure, self.update, interval=1000.0 / node.refresh_hz,
            cache_frame_data=False)

    def _panel(self, index, title, ylabel, log=False):
        axis = self.axes[index]
        axis.set_title(title)
        axis.set_xlabel('seconds from latest sample')
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.25)
        if log:
            axis.set_yscale('log')
        return axis

    def _line(self, axis, name, style='-'):
        if isinstance(style, tuple):
            line, = axis.plot([], [], label=name, linewidth=1.2, linestyle=style)
        else:
            line, = axis.plot([], [], style, label=name, linewidth=1.2)
        self.lines[name] = line
        return line

    def _configure_axes(self):
        axis = self._panel(0, '1. Linear velocity', 'm/s')
        self._line(axis, 'v_EKF'); self._line(axis, 'v_encoder', '--')
        axis.legend(loc='upper left')

        axis = self._panel(1, '2. Yaw rate and bias', 'rad/s')
        for name, style in [('omega_EKF', '-'), ('gyro_z', '--'),
                            ('omega_Ackermann', ':'), ('bias_EKF', '-.'),
                            ('omega+bias', (0, (4, 2)))]:
            self._line(axis, name, style)
        axis.legend(loc='upper left', fontsize='small')

        axis = self._panel(2, '3. Local innovations', 'measurement units')
        self._line(axis, 'encoder residual'); self._line(axis, 'Ackermann residual')
        self._line(axis, 'gyro residual'); axis.legend(loc='upper left', fontsize='small')

        axis = self._panel(3, '4. Cartographer innovations', 'm / rad')
        self._line(axis, 'cart x'); self._line(axis, 'cart y'); self._line(axis, 'cart theta')
        axis.legend(loc='upper left', fontsize='small')

        axis = self._panel(4, '5. Cartographer Mahalanobis gate', 'd^2')
        self._line(axis, 'd^2'); self._line(axis, 'threshold', '--')
        self._line(axis, 'accepted', 'o'); self._line(axis, 'rejected', 'x')
        axis.legend(loc='upper left', fontsize='small')

        axis = self._panel(5, '6. Covariance diagonal', 'variance', log=True)
        for name in ('Pxx', 'Pyy', 'Ptheta', 'Pvv', 'Pomega', 'Pbias'):
            self._line(axis, name)
        axis.legend(loc='upper left', fontsize='small', ncol=2)

        axis = self._panel(6, '7. Adaptive process noise', 'variance', log=True)
        for name in ('Sv', 'Somega', 'Qbb'):
            self._line(axis, name)
        axis.legend(loc='upper left')

        axis = self._panel(7, '8. XY trajectory', 'y (m)')
        axis.set_xlabel('x (m)')
        axis.set_aspect('equal', adjustable='datalim')
        self._line(axis, 'trajectory')

    def _set(self, name, x, y):
        self.lines[name].set_data(x, y)

    def update(self, _frame):
        x, values = self.node.snapshot()
        if values is None:
            self._draw_status(None, self.node.status_text)
            return list(self.lines.values())
        get = lambda name: values[:, FIELDS[name]]
        self._set('v_EKF', x, get('v')); self._set('v_encoder', x, get('encoder_velocity'))
        self._set('omega_EKF', x, get('omega')); self._set('gyro_z', x, get('gyro_z'))
        self._set('omega_Ackermann', x, get('v') / 0.256 * np.tan(get('applied_steering')))
        self._set('bias_EKF', x, get('bias')); self._set('omega+bias', x, get('omega') + get('bias'))
        self._set('encoder residual', x, get('encoder_residual'))
        self._set('Ackermann residual', x, get('ackermann_residual'))
        self._set('gyro residual', x, get('gyro_residual'))
        self._set('cart x', x, get('cart_x')); self._set('cart y', x, get('cart_y'))
        self._set('cart theta', x, get('cart_theta'))
        self._set('d^2', x, get('cart_d2')); self._set('threshold', x, get('cart_threshold'))
        accepted = np.where(get('cart_accepted') > 0.5, get('cart_d2'), np.nan)
        rejected = np.where(get('cart_rejected') > 0.5, get('cart_d2'), np.nan)
        self._set('accepted', x, accepted); self._set('rejected', x, rejected)
        for name in ('Pxx', 'Pyy', 'Ptheta', 'Pvv', 'Pomega', 'Pbias', 'Sv', 'Somega', 'Qbb'):
            self._set(name, x, np.maximum(get(name), np.finfo(float).tiny))
        self._set('trajectory', get('x'), get('y'))
        self._draw_status(values[-1], self.node.status_text)
        for axis in self.axes[:7]:
            axis.relim(); axis.autoscale_view()
        self.axes[7].relim(); self.axes[7].autoscale_view()
        return list(self.lines.values())

    def _draw_status(self, latest, status_text):
        text = self.figure.texts[0] if self.figure.texts else self.figure.text(0.5, 0.005, '')
        text.set_fontsize(8)
        if latest is None:
            text.set_text(status_text)
            return
        get = lambda name: latest[FIELDS[name]]
        finite_fields = ('x', 'y', 'theta', 'v', 'omega', 'bias',
                 'Pxx', 'Pyy', 'Ptheta', 'Pvv', 'Pomega', 'Pbias',
                 'Sv', 'Somega', 'Qbb', 'encoder_velocity', 'gyro_z',
                 'applied_steering', 'dt')
        finite = all(np.isfinite(get(name)) for name in finite_fields)
        covariance = np.array([get(name) for name in ('Pxx', 'Pyy', 'Ptheta', 'Pvv', 'Pomega', 'Pbias')])
        covariance_ok = np.all(np.isfinite(covariance)) and np.all(covariance >= 0)
        imu = 'READY' if np.isfinite(get('gyro_z')) else 'WAITING'
        cart = 'ACCEPTED' if get('cart_accepted') > .5 else ('REJECTED' if get('cart_rejected') > .5 else 'NO NEW UPDATE')
        status = 'NOMINAL' if finite and covariance_ok else 'INVALID'
        text.set_text(
            f'{status} | IMU: {imu} | Cartographer: {cart} | '
            f'x={get("x"):.3f} y={get("y"):.3f} theta={get("theta"):.3f} | '
            f'v={get("v"):.3f} omega={get("omega"):.3f} b={get("bias"):.4f} | '
            f'enc={get("encoder_velocity"):.3f} gyro={get("gyro_z"):.3f} '
            f'ack={get("v") / 0.256 * np.tan(get("applied_steering")):.3f} '
            f'steer={get("applied_steering"):.3f} dt={get("dt"):.4f} | '
            f'Sv={get("Sv"):.2e} Somega={get("Somega"):.2e} Qbb={get("Qbb"):.2e} | '
            f'd2={get("cart_d2"):.2f}/{get("cart_threshold"):.2f} | '
            f'Pvv={get("Pvv"):.2e} Pomega={get("Pomega"):.2e} Pbias={get("Pbias"):.2e}',
        )


def main(args=None):
    rclpy.init(args=args)
    node = NavDiagLivePlot()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    dashboard = Dashboard(node)
    node.get_logger().info('Dashboard GUI initialized')
    try:
        plt.show()
    finally:
        executor.shutdown()
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()
