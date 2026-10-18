import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_description')
    xacro_file = os.path.join(package_share, 'urdf', 'robot.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[
                {'robot_description': robot_description},
                {'use_sim_time': LaunchConfiguration('use_sim_time')},
            ],
            output='screen',
        ),
    ])
