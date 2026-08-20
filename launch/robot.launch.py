import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command

from launch_ros.actions import Node


def generate_launch_description():

    package_name = "eddie_bot"

    pkg_share = get_package_share_directory(package_name)

    # ==========================================================
    # Robot description
    # ==========================================================

    xacro_file = os.path.join(
        pkg_share,
        "description",
        "robot.urdf.xacro"
    )

    robot_description = {
        "robot_description": Command([
            "xacro ",
            xacro_file,
            " use_ros2_control:=true",
            " sim_mode:=false"
        ])
    }

    # ==========================================================
    # Controller configuration
    # ==========================================================

    controller_config = os.path.join(
        pkg_share,
        "config",
        "my_controllers.yaml"
    )

    # ==========================================================
    # ros2_control_node
    # ==========================================================

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            robot_description,
            controller_config
        ],
        output="screen",
    )

    # ==========================================================
    # robot_state_publisher
    # ==========================================================

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            robot_description
        ],
        output="screen",
    )

    # ==========================================================
    # Joint State Broadcaster
    # ==========================================================

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_broad",
            "--controller-manager",
            "/controller_manager"
        ],
        output="screen",
    )

    # ==========================================================
    # Differential Drive Controller
    # ==========================================================

    diff_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "diff_cont",
            "--controller-manager",
            "/controller_manager"
        ],
        output="screen",
    )

    # ==========================================================
    # Start diff controller after joint broadcaster
    # ==========================================================

    delay_diff_drive_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[
                diff_drive_controller_spawner
            ],
        )
    )

    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([
        control_node,
        robot_state_pub_node,

        joint_state_broadcaster_spawner,

        delay_diff_drive_controller,
    ])