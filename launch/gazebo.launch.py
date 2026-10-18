import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('robot_description')
    xacro_file = os.path.join(package_share, 'urdf', 'robot.xacro')
    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    use_ros2_control = LaunchConfiguration('use_ros2_control')
    spawn_roll = LaunchConfiguration('spawn_roll')
    spawn_pitch = LaunchConfiguration('spawn_pitch')
    spawn_yaw = LaunchConfiguration('spawn_yaw')
    ekf = LaunchConfiguration('ekf')
    robot_description = Command([
        'xacro ', xacro_file, ' use_ros2_control:=', use_ros2_control,
    ])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py',
            )
        ),
        launch_arguments={
            'world': world,
            'gui': gui,
            'pause': 'false',
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True},
        ],
        output='screen',
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'robot',
            '-topic', 'robot_description',
            # Wheel STL radius is approximately 0.0675 m.
            '-z', '0.07',
            '-R', spawn_roll,
            '-P', spawn_pitch,
            '-Y', spawn_yaw,
        ],
        output='screen',
    )

    joint_state_broadcaster = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )
    diff_drive_controller = Node(
        package='controller_manager', executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
        output='screen',
    )
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        parameters=[os.path.join(package_share, 'config', 'ekf.yaml')],
        output='screen',
        condition=IfCondition(ekf),
    )
    spawn_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster, diff_drive_controller],
        ),
        condition=IfCondition(use_ros2_control),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(package_share, 'worlds', 'basic.world'),
            description='Gazebo world file',
        ),
        DeclareLaunchArgument(
            'gui',
            default_value='true',
            description='Start the Gazebo client',
        ),
        DeclareLaunchArgument(
            'use_ros2_control', default_value='true',
            description='Use ros2_control; requires gazebo_ros2_control',
        ),
        DeclareLaunchArgument(
            'spawn_roll', default_value='0.0',
            description='Initial roll in radians',
        ),
        DeclareLaunchArgument('spawn_pitch', default_value='0.0'),
        DeclareLaunchArgument('spawn_yaw', default_value='0.0'),
        DeclareLaunchArgument(
            'ekf', default_value='true',
            description='Start robot_localization EKF',
        ),
        gazebo,
        robot_state_publisher,
        spawn_robot,
        spawn_controllers,
        ekf_node,
    ])
