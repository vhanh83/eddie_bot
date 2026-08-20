import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'eddie_bot'

    # ============================================================
    # Launch arguments
    # ============================================================

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_ros2_control = LaunchConfiguration('use_ros2_control')

    # ============================================================
    # Robot Xacro
    # ============================================================

    package_path = get_package_share_directory(package_name)

    xacro_file = os.path.join(
        package_path,
        'description',
        'robot.urdf.xacro'
    )

    robot_description = Command([
        'xacro ',
        xacro_file,
        ' use_ros2_control:=',
        use_ros2_control,
        ' sim_mode:=',
        use_sim_time
    ])

    # ============================================================
    # Robot State Publisher
    # ============================================================

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',

        name='robot_state_publisher',

        output='screen',

        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': use_sim_time
            }
        ]
    )

    # ============================================================
    # Launch
    # ============================================================

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time if true'
        ),

        DeclareLaunchArgument(
            'use_ros2_control',
            default_value='true',
            description='Enable ros2_control if true'
        ),

        robot_state_publisher

    ])