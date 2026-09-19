# QCar2 EKF V1

This repository is a QCar2/QLabs research workspace for an experimental ROS 2 localization estimator. V1 combines wheel encoder and IMU gyro information locally, with an independent LiDAR-only Cartographer pose correction.

## V1 estimator

The state is:

```text
X = [x, y, theta, v, omega, b]^T
```

Prediction uses constant local velocity, yaw rate, and residual gyro bias:

```text
x' = x + v*cos(theta)*dt
y' = y + v*sin(theta)*dt
theta' = theta + omega*dt
v' = v, omega' = omega, b' = b
```

Measurements are:

- Encoder: `v`
- Applied-steering Ackermann pseudo-measurement: `omega - v/L*tan(delta_applied) = 0`
- Filtered/debiased gyro: `gyro_z = omega + b`
- Cartographer: `[x, y, theta]`

Cartographer is intentionally independent in V1:

```text
use_odometry = false
TRAJECTORY_BUILDER_2D.use_imu_data = false
```

The adaptive process covariance uses observed encoder and gyro changes with floor/ceiling limits, plus gyro-bias random walk. Static characterization defaults are:

```text
sigma_encoder    = 0.015 m/s
sigma_gyro       = 0.041 rad/s
sigma_cart_x     = 0.010 m
sigma_cart_y     = 0.006 m
sigma_cart_theta = 0.008 rad
sigma_ackermann  = 0.2 (provisional)
```

Cartographer corrections use the configurable Mahalanobis gate:

```text
d^2 = r^T S^-1 r
threshold = 11.345
```

These values are initial experimental settings, not guarantees for dynamic operation. V1 has no ground-truth QLabs localization, no ZUPT, no camera/semantic localization, and no production safety guarantees. Future work may include dynamic noise characterization, V2 bias/zero-update logic, physical QCar2 validation, camera landmarks, and broader sensor fusion.

## Build and launch

The ROS workspace is `Development` with source base `ros2/src`.

1. Start the virtual QCar container and configure the map:

```bash
docker run --rm -it --network host --name virtual-qcar2 quanser/virtual-qcar2 bash
cd /home/qcar2_scripts/python
python3 Base_Scenarios_Python/Setup_Competition_Map.py
```

2. In a second terminal, start the ROS development container:

```bash
cd /home/bp02-ubuntu/Documents/GitHub/QCar2Summer2026Research/isaac_ros_common
./scripts/run_dev.sh /home/bp02-ubuntu/Documents/GitHub/QCar2Summer2026Research/Development
```

3. Inside the ROS container, build and source:

```bash
cd /workspaces/isaac_ros-dev/Development
colcon build --base-paths ros2/src
source install/setup.bash
export ROS_DOMAIN_ID=7
```

4. Start the virtual QCar2 drivers, IMU preprocessing, and LiDAR-only Cartographer:

```bash
ros2 launch qcar2_nodes qcar2_cartographer_virtual_launch.py
```

5. In additional ROS terminals, source the workspace and start the existing controller:

```bash
source /workspaces/isaac_ros-dev/Development/install/setup.bash
export ROS_DOMAIN_ID=7
ros2 run qcar2_autonomy path_follower
```

6. Start the live dashboard independently:

```bash
ros2 run qcar2_autonomy nav_diag_live_plot
```

The controller starts with `start_path` false. Enable the existing autonomous path only when the system is ready:

```bash
ros2 param set /path_follower start_path "[True]"
```

## Recording

Start recording after the ROS graph is running. For the final stationary test, leave `start_path` false and record for 20-30 seconds after IMU calibration:

```bash
ros2 bag record -o v1_final_static \
  /nav_diag /qcar2_joint /qcar2_imu/bias_corrected_200hz \
  /cmd_vel_nav /scan /tf /tf_static
```

For the final autonomous run, use the same command with a different output name, then enable `start_path`:

```bash
ros2 bag record -o v1_final_run \
  /nav_diag /qcar2_joint /qcar2_imu/bias_corrected_200hz \
  /cmd_vel_nav /scan /tf /tf_static
```

## Offline analysis

Analyze any rosbag2 directory without editing source code:

```bash
ros2 run qcar2_autonomy analyze_nav_diag_bag /path/to/v1_final_run
```

Results are written to `analysis/<bag_name>/` as eight PNG figures, `summary.csv`, and `summary.txt`. The analyzer reports state ranges, local and Cartographer innovation statistics, gate acceptance, covariance endpoints, adaptive process-noise ranges, timing, and invalid/negative values.

The live dashboard shows velocity, yaw-rate/bias, local innovations, Cartographer innovations, Mahalanobis gate status, covariance, adaptive process noise, XY trajectory, and a numerical status line. It only subscribes to `/nav_diag`; it never publishes commands.
