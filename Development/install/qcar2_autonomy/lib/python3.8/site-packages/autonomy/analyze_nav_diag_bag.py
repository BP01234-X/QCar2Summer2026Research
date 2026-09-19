#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


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

P_FIELDS = ('Pxx', 'Pyy', 'Ptheta', 'Pvv', 'Pomega', 'Pbias')


def read_diagnostics(bag_path):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(bag_path), storage_id='sqlite3'),
        rosbag2_py.ConverterOptions('', '')
    )
    topics = {topic.name: topic.type for topic in reader.get_all_topics_and_types()}
    if '/nav_diag' not in topics:
        raise RuntimeError(f'{bag_path} does not contain /nav_diag')
    message_type = get_message(topics['/nav_diag'])
    timestamps = []
    rows = []
    while reader.has_next():
        topic, data, receive_time = reader.read_next()
        if topic != '/nav_diag':
            continue
        message = deserialize_message(data, message_type)
        values = np.asarray(message.data, dtype=float)
        if values.size <= max(FIELDS.values()):
            continue
        timestamps.append(receive_time * 1e-9)
        rows.append(values)
    if not rows:
        raise RuntimeError(f'{bag_path} contains no usable /nav_diag samples')
    timestamps = np.asarray(timestamps, dtype=float)
    return timestamps - timestamps[0], np.asarray(rows, dtype=float)


def finite_pair(t, values):
    mask = np.isfinite(t) & np.isfinite(values)
    return t[mask], values[mask]


def plot_lines(path, t, series, title, ylabel, log=False):
    fig, axis = plt.subplots(figsize=(11, 5.5))
    for label, values, style in series:
        x, y = finite_pair(t, values)
        if isinstance(style, tuple):
            axis.plot(x, y, linewidth=1.0, label=label, linestyle=style)
        else:
            axis.plot(x, y, style, linewidth=1.0, label=label)
    axis.set_title(title)
    axis.set_xlabel('time (s)')
    axis.set_ylabel(ylabel)
    axis.grid(True, alpha=0.25)
    if log:
        axis.set_yscale('log')
    axis.legend(loc='best')
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def make_figures(output, t, data):
    get = lambda name: data[:, FIELDS[name]]
    plot_lines(output / '01_velocity.png', t, [
        ('v_EKF', get('v'), '-'), ('v_encoder', get('encoder_velocity'), '--')
    ], 'QCar2 V1 linear velocity', 'm/s')
    plot_lines(output / '02_yaw_rate_bias.png', t, [
        ('omega_EKF', get('omega'), '-'), ('gyro_z', get('gyro_z'), '--'),
        ('omega_Ackermann', get('v') / 0.256 * np.tan(get('applied_steering')), ':'),
        ('bias_EKF', get('bias'), '-.'), ('omega_EKF + bias', get('omega') + get('bias'), (0, (4, 2)))
    ], 'QCar2 V1 yaw rate and bias', 'rad/s')
    plot_lines(output / '03_local_innovations.png', t, [
        ('encoder', get('encoder_residual'), '-'),
        ('Ackermann', get('ackermann_residual'), '-'),
        ('gyro', get('gyro_residual'), '-')
    ], 'QCar2 V1 local innovations', 'measurement units')
    plot_lines(output / '04_cartographer_innovations.png', t, [
        ('x', get('cart_x'), '-'), ('y', get('cart_y'), '-'),
        ('theta', get('cart_theta'), '-')
    ], 'Cartographer innovations', 'm / rad')
    plot_lines(output / '05_mahalanobis_gate.png', t, [
        ('d^2', get('cart_d2'), '-'), ('threshold', get('cart_threshold'), '--'),
        ('accepted', np.where(get('cart_accepted') > .5, get('cart_d2'), np.nan), 'o'),
        ('rejected', np.where(get('cart_rejected') > .5, get('cart_d2'), np.nan), 'x')
    ], 'Cartographer Mahalanobis gate', 'd^2')
    plot_lines(output / '06_covariance.png', t, [
        (name, np.maximum(get(name), np.finfo(float).tiny), '-') for name in P_FIELDS
    ], 'EKF covariance diagonal', 'variance', log=True)
    plot_lines(output / '07_adaptive_process_noise.png', t, [
        ('Sv', np.maximum(get('Sv'), np.finfo(float).tiny), '-'),
        ('Somega', np.maximum(get('Somega'), np.finfo(float).tiny), '-'),
        ('Qbb', np.maximum(get('Qbb'), np.finfo(float).tiny), '-')
    ], 'Adaptive process noise', 'variance', log=True)
    fig, axis = plt.subplots(figsize=(7, 7))
    axis.plot(get('x'), get('y'), linewidth=1.1, label='EKF trajectory')
    axis.set_title('QCar2 V1 EKF trajectory')
    axis.set_xlabel('x (m)'); axis.set_ylabel('y (m)')
    axis.set_aspect('equal', adjustable='datalim')
    axis.grid(True, alpha=0.25); axis.legend(loc='best')
    fig.tight_layout(); fig.savefig(output / '08_xy_trajectory.png', dpi=180); plt.close(fig)


def finite_stats(values):
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {'count': 0, 'mean': np.nan, 'std': np.nan, 'rms': np.nan}
    return {
        'count': int(values.size),
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'rms': float(np.sqrt(np.mean(values ** 2))),
    }


def analyze(t, data):
    get = lambda name: data[:, FIELDS[name]]
    metrics = {}
    for name in ('v', 'omega', 'bias'):
        values = get(name); finite = values[np.isfinite(values)]
        metrics[f'{name}_min'] = float(np.min(finite)) if finite.size else np.nan
        metrics[f'{name}_max'] = float(np.max(finite)) if finite.size else np.nan
    for name in ('encoder_residual', 'gyro_residual', 'ackermann_residual',
                 'cart_x', 'cart_y', 'cart_theta'):
        stats = finite_stats(get(name))
        for key, value in stats.items():
            metrics[f'{name}_{key}'] = value
    accepted = np.nansum(get('cart_accepted') > .5)
    rejected = np.nansum(get('cart_rejected') > .5)
    d2 = get('cart_d2'); finite_d2 = d2[np.isfinite(d2)]
    metrics.update({
        'cart_accepted': int(accepted), 'cart_rejected': int(rejected),
        'cart_total_updates': int(accepted + rejected),
        'cart_acceptance_percent': float(100 * accepted / (accepted + rejected)) if accepted + rejected else np.nan,
        'cart_d2_mean': float(np.mean(finite_d2)) if finite_d2.size else np.nan,
        'cart_d2_median': float(np.median(finite_d2)) if finite_d2.size else np.nan,
        'cart_d2_max': float(np.max(finite_d2)) if finite_d2.size else np.nan,
        'cart_threshold': float(np.nanmedian(get('cart_threshold'))),
        'duration_seconds': float(t[-1]),
        'diagnostic_samples': int(len(data)),
        'dt_mean': float(np.nanmean(get('dt'))),
        'dt_std': float(np.nanstd(get('dt'))),
        'dt_max': float(np.nanmax(get('dt'))),
    })
    for name in P_FIELDS:
        values = get(name); metrics[f'{name}_initial'] = float(values[0]); metrics[f'{name}_final'] = float(values[-1])
    for name in ('Sv', 'Somega', 'Qbb'):
        values = get(name); finite = values[np.isfinite(values)]
        metrics[f'{name}_min'] = float(np.min(finite)) if finite.size else np.nan
        metrics[f'{name}_max'] = float(np.max(finite)) if finite.size else np.nan
    covariance = data[:, [FIELDS[name] for name in P_FIELDS]]
    metrics['negative_covariance_diagonal_count'] = int(np.sum(covariance < 0))
    metrics['nan_count'] = int(np.isnan(data).sum())
    metrics['infinity_count'] = int(np.isinf(data).sum())
    return metrics


def write_summary(output, metrics):
    with (output / 'summary.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(('metric', 'value'))
        writer.writerows(metrics.items())
    with (output / 'summary.txt').open('w') as handle:
        handle.write('QCar2 EKF V1 diagnostic summary\n\n')
        for key, value in metrics.items():
            handle.write(f'{key}: {value}\n')


def main(args=None):
    parser = argparse.ArgumentParser(description='Analyze a QCar2 rosbag /nav_diag stream.')
    parser.add_argument('bag', type=Path, help='rosbag2 directory containing metadata.yaml')
    parser.add_argument('--output-root', type=Path, default=Path('analysis'))
    parsed = parser.parse_args(args)
    output = parsed.output_root / parsed.bag.name
    output.mkdir(parents=True, exist_ok=True)
    timestamps, data = read_diagnostics(parsed.bag)
    make_figures(output, timestamps, data)
    metrics = analyze(timestamps, data)
    write_summary(output, metrics)
    print(f'Analyzed {len(data)} /nav_diag samples from {parsed.bag}')
    print(f'Figures and summaries: {output}')


if __name__ == '__main__':
    main()
