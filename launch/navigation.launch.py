import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    package_name = "eddie_bot"

    pkg_share = get_package_share_directory(package_name)

    nav2_params = os.path.join(
        pkg_share,
        "config",
        "nav2_params.yaml"
    )

    rviz_config = os.path.join(
        pkg_share,
        "config",
        "rviz",
        "nav.rviz"
    )

    # map_file = LaunchConfiguration("map")

    # map_server = Node(
    #     package="nav2_map_server",
    #     executable="map_server",
    #     name="map_server",
    #     output="screen",
    #     parameters=[
    #         nav2_params,
    #         {
    #             "yaml_filename": map_file
    #         }
    #     ]
    # )
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            nav2_params
        ]
    )
    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[
            nav2_params
        ]
    )

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        parameters=[
            nav2_params
        ]
    )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        output="screen",
        parameters=[
            nav2_params
        ],
        remappings=[
            (
                "cmd_vel",
                "/diff_cont/cmd_vel_unstamped"
            )
        ]
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        parameters=[
            nav2_params
        ]
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        parameters=[
            nav2_params
        ]
    )

    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        output="screen",
        parameters=[
            nav2_params
        ]
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[
            {
                "autostart": True,
                "node_names": [
                    "map_server",
                    "amcl",
                    "planner_server",
                    "controller_server",
                    "behavior_server",
                    "bt_navigator",
                    "waypoint_follower",
                ]
            }
        ]
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d",
            rviz_config
        ],
        output="screen"
    )

    return LaunchDescription([

        # DeclareLaunchArgument(
        #     "map",
        #     default_value=os.path.expanduser(
        #         "~/ros_ws/src/eddie_bot/map/map.yaml"
        #     )
        # ),

        map_server,
        amcl,
        planner_server,
        controller_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        lifecycle_manager,
        rviz,

    ])