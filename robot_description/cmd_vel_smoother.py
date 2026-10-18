import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class CmdVelSmoother(Node):
    def __init__(self):
        super().__init__('cmd_vel_smoother')

        self.declare_parameter('frequency', 30.0)
        self.declare_parameter('linear_acceleration', 0.5)
        self.declare_parameter('linear_deceleration', 0.8)
        self.declare_parameter('angular_acceleration', 1.0)
        self.declare_parameter('angular_deceleration', 1.5)
        self.declare_parameter('command_timeout', 0.5)

        self.frequency = self.get_parameter('frequency').value
        self.linear_acceleration = self.get_parameter('linear_acceleration').value
        self.linear_deceleration = self.get_parameter('linear_deceleration').value
        self.angular_acceleration = self.get_parameter('angular_acceleration').value
        self.angular_deceleration = self.get_parameter('angular_deceleration').value
        self.command_timeout = self.get_parameter('command_timeout').value

        self.target_linear = 0.0
        self.target_angular = 0.0
        self.current_linear = 0.0
        self.current_angular = 0.0
        self.last_command_time = self.get_clock().now()

        self.command_subscriber = self.create_subscription(
            Twist,
            'cmd_vel_raw',
            self.command_callback,
            10,
        )
        self.command_publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(1.0 / self.frequency, self.update)

    def command_callback(self, message):
        self.target_linear = message.linear.x
        self.target_angular = message.angular.z
        self.last_command_time = self.get_clock().now()

    def approach(self, current, target, acceleration, deceleration, dt):
        if abs(target) < abs(current):
            step = deceleration * dt
        else:
            step = acceleration * dt

        if current < target:
            return min(current + step, target)
        return max(current - step, target)

    def update(self):
        elapsed = (self.get_clock().now() - self.last_command_time).nanoseconds / 1e9
        target_linear = self.target_linear
        target_angular = self.target_angular
        if elapsed > self.command_timeout:
            target_linear = 0.0
            target_angular = 0.0

        dt = 1.0 / self.frequency
        self.current_linear = self.approach(
            self.current_linear,
            target_linear,
            self.linear_acceleration,
            self.linear_deceleration,
            dt,
        )
        self.current_angular = self.approach(
            self.current_angular,
            target_angular,
            self.angular_acceleration,
            self.angular_deceleration,
            dt,
        )

        output = Twist()
        output.linear.x = self.current_linear
        output.angular.z = self.current_angular
        self.command_publisher.publish(output)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelSmoother()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
