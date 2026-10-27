import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch.actions import TimerAction

from launch.actions import IncludeLaunchDescription

from launch.launch_description_sources import (
    PythonLaunchDescriptionSource
)


def generate_launch_description():

    realsense_launch_file = os.path.join(
        get_package_share_directory("realsense2_camera"),
        "launch",
        "rs_launch.py"
    )

    realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            realsense_launch_file
        ),

        launch_arguments={

            # ==============================================
            # Camera
            # ==============================================

            "camera_name": "camera",

            # ==============================================
            # COLOR
            # ==============================================

            "enable_color": "true",

            "rgb_camera.color_profile":
                "640x480x15",

            # ==============================================
            # DEPTH
            # ==============================================

            "enable_depth": "true",

            "depth_module.depth_profile":
                "640x480x15",

            # ==============================================
            # IMU
            # Tạm thời OFF để test ổn định
            # ==============================================

            "enable_gyro": "false",

            "enable_accel": "false",

            # ==============================================
            # IR
            # ==============================================

            "enable_infra1": "false",

            "enable_infra2": "false",

            # ==============================================
            # POINT CLOUD
            # ==============================================

            "pointcloud.enable": "false",

            # ==============================================
            # RESET
            # ==============================================

            "initial_reset": "true",

        }.items()
    )

    # Cho USB ổn định trước khi mở camera

    delayed_camera = TimerAction(
        period=3.0,
        actions=[
            realsense
        ]
    )

    return LaunchDescription([
        delayed_camera
    ])