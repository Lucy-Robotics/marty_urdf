# Developer guide - `marty_urdf`

ROS 2 **Jazzy** description package for the **Robotical Marty v2**.
Bringup, hardware plugin, and cameras live in **`lucy_ros_packages`**.
Workspace contract for robot packages: [`lucy_ws/docs/adding_robot_packages.md`](../../../docs/adding_robot_packages.md).

## 1. Role of this package

| Concern | Lives in |
|---------|----------|
| Robot description (xacro, STL meshes, joint limits) | `description/robot_description/` |
| ros2_control hardware interfaces (real / mock) | `description/ros2_control/` (generated) |
| Gazebo physics + generated plugin | `description/gazebo/` |
| Hardware mapping | `config/hardware/active.yaml` |
| Controller parameters | `config/controllers.yaml` (generated) |
| RViz layout | `config/marty_rviz.rviz` |

**Robot selection:** `robot_package:=marty_urdf` or `LUCY_ROBOT_PACKAGE=marty_urdf`.

## 2. Model origin

The kinematic tree and meshes are ported from `marty2_description`
(Apache-2.0, license kept in `description/robot_description/LICENSE.marty2_description`).
Lucy changes: meshes resolve through `${mesh_dir}` (`file://` + `base_path`) instead of
`package://marty2_description`, the entry xacro follows the Lucy include pattern, and the
head is lifted 0.15338 m so `base_link` sits on the ground under the feet.

Links carry placeholder inertias (1e-5 kg), so Gazebo pins `base_link` to the world
with the feet resting on the ground (`marty_gazebo_physics.xacro`); the robot cannot balance or walk in sim.

## 3. Joints

Nine actuated joints, all on one `marty_controller` (JointTrajectoryController):

| Joint | Moves |
|-------|-------|
| `eye_left_joint` | Eyes (`eye_right_joint` mimics, x-1) |
| `arm_servo_gear_left_joint` / `arm_servo_gear_right_joint` | Arms (`arm_*_joint` mimic through the gear, x-1.3077) |
| `leg_{left,right}_thigh_joint` | Hip pitch (parallel thigh + knee links mimic) |
| `leg_{left,right}_twist_joint` | Leg twist |
| `leg_{left,right}_shin_joint` | Knee roll (parallel shin + foot links mimic) |

Mimic joints are left out of ros2_control; `robot_state_publisher` derives them.

## 4. Hardware status

Real Marty servos are driven by Robotical's RIC controller, which Lucy has no driver for.
`active.yaml` therefore declares a single placeholder `rp2040_marty` board
(`internal_servo_only`, 9 PWM slots) with every actuator **`enabled: false`** and a neutral
180-degree mapping (`offset` pi/2, travel clamped to 0..pi). Mock hardware works (Gazebo is not a
target yet: its files are generated but untested);
calibrate offsets / limits and enable actuators only once a real board is wired.

## 5. Regenerate

After editing `config/hardware/active.yaml` or URDF limits, from the workspace root:

```bash
generate_config \
  --input src/marty_urdf/config/hardware/active.yaml \
  --urdf src/marty_urdf/description/urdf/marty.urdf.xacro \
  --base-path $PWD/src/marty_urdf/description \
  --controller-config src/marty_urdf/config/controllers.yaml \
  --output-dir /tmp/marty_gen
cp /tmp/marty_gen/marty_ros2_control.xacro src/marty_urdf/description/ros2_control/
cp /tmp/marty_gen/controllers.yaml src/marty_urdf/config/
cp /tmp/marty_gen/gazebo.xacro /tmp/marty_gen/gazebo_bridge.yaml src/marty_urdf/description/gazebo/
```

Keep `config/hardware/configs/default.yaml` in sync with `active.yaml`.

## 6. Launches

```bash
ros2 launch marty_urdf joint_preview.launch.py            # sliders + RViz, no control stack
ros2 launch marty_urdf control.launch.py use_mock_hardware:=true
ros2 launch marty_urdf gazebo.launch.py headless:=true   # untested, not a target yet
```
