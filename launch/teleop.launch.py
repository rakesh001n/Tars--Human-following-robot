from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_description',
            executable='cmd_vel_smoother',
            name='cmd_vel_smoother',
            parameters=[{
                'frequency': 30.0,
                'linear_acceleration': 0.5,
                'linear_deceleration': 0.8,
                'angular_acceleration': 1.0,
                'angular_deceleration': 1.5,
                'command_timeout': 0.5,
            }],
            output='screen',
            remappings=[
                ('cmd_vel_raw', 'cmd_vel_raw'),
                ('cmd_vel', '/diff_drive_controller/cmd_vel_unstamped'),
            ],
        ),
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_twist_keyboard',
            output='screen',
            # teleop_twist_keyboard needs a real TTY for raw key input.
            prefix='gnome-terminal --',
            remappings=[('cmd_vel', 'cmd_vel_raw')],
        ),
    ])
