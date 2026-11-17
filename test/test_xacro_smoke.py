# Copyright 2025 Lucy Robotics Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Generate URDF with xacro (no Gazebo / ROS nodes). Uses install share when available."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

from xacro_helper import run_xacro

ACTUATED_JOINTS = (
    "eye_left_joint",
    "arm_servo_gear_left_joint",
    "arm_servo_gear_right_joint",
    "leg_left_thigh_joint",
    "leg_right_thigh_joint",
    "leg_left_twist_joint",
    "leg_right_twist_joint",
    "leg_left_shin_joint",
    "leg_right_shin_joint",
)

TAGGED_FIXED_LINKS = {
    "side_panel_left": "arm_servo_gear_left_joint",
    "side_panel_right": "arm_servo_gear_right_joint",
    "hip_left": "leg_left_thigh_joint",
    "hip_right": "leg_right_thigh_joint",
    "leg_left_twist_upper": "leg_left_twist_joint",
    "leg_right_twist_upper": "leg_right_twist_joint",
    "leg_left_knee_lower": "leg_left_shin_joint",
    "leg_right_knee_lower": "leg_right_shin_joint",
    "hand_left": "arm_servo_gear_left_joint",
    "hand_right": "arm_servo_gear_right_joint",
}


def _marty_paths():
    try:
        from ament_index_python.packages import get_package_share_directory
        share = Path(get_package_share_directory("marty_urdf"))
        description = share / "description"
        urdf = description / "urdf" / "marty.urdf.xacro"
        if urdf.is_file():
            return urdf, description
    except Exception:
        pass
    root = Path(__file__).resolve().parents[1]
    description = root / "description"
    urdf = description / "urdf" / "marty.urdf.xacro"
    return urdf, description


def _controller_yaml() -> Path:
    try:
        from ament_index_python.packages import get_package_share_directory

        pkg_share = Path(get_package_share_directory("marty_urdf"))
        share_yaml = pkg_share / "config" / "controllers.yaml"
        if share_yaml.is_file():
            return share_yaml
    except Exception:
        pass
    root = Path(__file__).resolve().parents[1]
    return root / "config" / "controllers.yaml"


@pytest.fixture(scope="module")
def controller_config() -> Path:
    path = _controller_yaml()
    if not path.is_file():
        pytest.skip(
            "Missing marty_urdf/config/controllers.yaml — "
            "build marty_urdf from this workspace."
        )
    return path


def test_xacro_real_mode(controller_config: Path):
    urdf, base = _marty_paths()
    assert urdf.is_file(), f"missing {urdf} — colcon build marty_urdf to install description/"
    r = run_xacro(
        [
            str(urdf),
            f"base_path:={base}",
            f"controller_config:={controller_config}",
            "use_gazebo_sim:=false",
            "use_mock_hardware:=false",
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "<robot" in r.stdout
    assert "lucy_ros2_control/LucySystemHardware" in r.stdout
    assert '<param name="publisher_topic">actuators/marty</param>' in r.stdout
    for joint in ACTUATED_JOINTS:
        assert f'<joint name="{joint}"' in r.stdout
    meshes = re.findall(r'filename="file://([^"]+)"', r.stdout)
    assert meshes, "no file:// meshes in expanded URDF"
    missing = sorted({m for m in meshes if not Path(m).is_file()})
    assert not missing, f"meshes not found: {missing}"


def test_xacro_gazebo_mode(controller_config: Path):
    urdf, base = _marty_paths()
    assert urdf.is_file(), f"missing {urdf} — colcon build marty_urdf to install description/"
    r = run_xacro(
        [
            str(urdf),
            f"base_path:={base}",
            f"controller_config:={controller_config}",
            "use_gazebo_sim:=true",
            "use_mock_hardware:=false",
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "<robot" in r.stdout
    assert "gz_ros2_control" in r.stdout or "GazeboSimSystem" in r.stdout


def _expanded_urdf(controller_config: Path) -> str:
    urdf, base = _marty_paths()
    r = run_xacro(
        [
            str(urdf),
            f"base_path:={base}",
            f"controller_config:={controller_config}",
            "use_mock_hardware:=true",
        ]
    )
    assert r.returncode == 0, r.stderr + r.stdout
    return r.stdout


def test_housings_and_mimic_links_tag_their_visual_with_the_moving_joint(
    controller_config: Path,
):
    robot = ET.fromstring(_expanded_urdf(controller_config))
    expected = dict(TAGGED_FIXED_LINKS)
    for joint in robot.findall("joint"):
        mimic = joint.find("mimic")
        if mimic is not None:
            expected[joint.find("child").get("link")] = mimic.get("joint")
    tagged = {
        link.get("name"): link.find("visual").get("joint")
        for link in robot.findall("link")
        if link.find("visual") is not None and link.find("visual").get("joint")
    }
    assert tagged == expected
