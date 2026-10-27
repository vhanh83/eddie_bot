import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch_ros.actions import Node


def generate_launch_description():

    package_name = "eddie_bot"

    pkg_share = get_package_share_directory(package_name)

    slam_config = os.path.join(
        pkg_share,
        "config",
        "slam_toolbox.yaml"
    )

    slam_node = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",

        name="slam_toolbox",

        parameters=[
            slam_config
        ],

        output="screen"
    )

    return LaunchDescription([
        slam_node
    ])