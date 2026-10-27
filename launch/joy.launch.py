import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_name = "eddie_bot"

    pkg_share = get_package_share_directory(package_name)

    joystick_config = os.path.join(
        pkg_share,
        "config",
        "joystick.yaml"
    )

    # ==========================================================
    # Joystick driver
    # ==========================================================

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        parameters=[
            joystick_config
        ],
        output="screen",
    )

    # ==========================================================
    # Joystick -> Twist
    # ==========================================================

    teleop_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        name="teleop_twist_joy_node",
        parameters=[
            joystick_config
        ],
        remappings=[
            (
                "/cmd_vel",
                "/joy/cmd_vel"
            )
        ],
        output="screen",
    )

    return LaunchDescription([
        joy_node,
        teleop_node,
    ])
