# marty_urdf

Robotical Marty v2 description package for the Lucy workspace (URDF, ros2_control, Gazebo, RViz).

- 9 actuated joints (eyes, arms, hip / twist / knee per leg) on one `marty_controller`
- Mock hardware supported; Gazebo files are generated but untested; real hardware is a disabled placeholder until a driver exists

Select it with `robot_package:=marty_urdf` (or `LUCY_ROBOT_PACKAGE=marty_urdf`).
See [docs/DEVELOPER.md](docs/DEVELOPER.md) for joints, hardware status and regeneration.

Meshes and kinematics are ported from `marty2_description` (Apache-2.0); see
`description/robot_description/LICENSE.marty2_description`. Everything else is GPL-3.0-or-later.
