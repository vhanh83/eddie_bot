import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    package_name = "eddie_bot"

    pkg_share = get_package_share_directory(package_name)

    # ==========================================================
    # EKF configuration
    # ==========================================================

    ekf_config = os.path.join(
        pkg_share,
        "config",
        "ekf.yaml"
    )

    # ==========================================================
    # SLAM configuration
    # ==========================================================

    slam_config = os.path.join(
        pkg_share,
        "config",
        "slam_toolbox.yaml"
    )

    # ==========================================================
    # RViz configuration
    # ==========================================================

    rviz_config = os.path.join(
        pkg_share,
        "config",
        "rviz",
        "slambuild.rviz"
    )

    # ==========================================================
    # EKF
    # Wheel odometry + IMU
    # ==========================================================

    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",

        parameters=[
            ekf_config
        ],

        output="screen"
    )

    # ==========================================================
    # SLAM Toolbox
    # ==========================================================

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",

        parameters=[
            slam_config
        ],

        output="screen"
    )

    # ==========================================================
    # RViz2
    # ==========================================================

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",

        arguments=[
            "-d",
            rviz_config
        ],

        output="screen"
    )

    # ==========================================================
    # Launch
    # ==========================================================

    return LaunchDescription([

        ekf_node,

        slam_node,

        rviz_node,

    ])