import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from sim_interfaces.srv import ComputeTarget
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist

class RobotController(Node):
    def __init__(self):
        super().__init__(self.__class__.__name__)

        self.declare_parameter('service_name', 'ComputeTargetService')
        self.service_name = self.get_parameter('service_name').get_parameter_value().string_value


        # TODO shouldn't be the service module but rather the DTO and the service name
        self.client = self.create_client(ComputeTarget, self.service_name)

        self.declare_parameter('robot_id', '0')
        self.robot_id = self.get_parameter('robot_id').get_parameter_value().string_value

        # Ideally we'd update our robots to interact directly with the BoidsService
        # as opposed to this roundabout way that allows the existing pub-sub
        # architecture to utilise a the service model
        qos_profile = QoSProfile(depth=10)
        self.sub_location = self.create_subscription(PoseWithCovarianceStamped, 
                "robot_{}/pose".format(self.robot_id), self.compute_target, qos_profile)
        self.pub_target = self.create_publisher(Twist, 
                "robot_{}/cmd_vel".format(self.robot_id), qos_profile)
        
        
        self.get_logger().info("Created RobotController (ID: {}) using {}".format(self.robot_id, self.service_name))
    

    """
    Upon receiving a pose update from a robot, calculate target velocity and 
    publish to back to the robot. It will do this through the central control
    service that has visibility of all robots' pose
    """
    def compute_target(self, payload:PoseWithCovarianceStamped):
        if not self.client.wait_for_service(timeout_sec=0.5):
            self.get_logger().warn('Service unavailable, no action undertaken')
            return
        
        request = ComputeTarget.Request()
        request.robot_id = self.robot_id
        request.pose = payload

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        response = future.result()
        self.pub_target.publish(response.vel)





## Boilerplate

def main():
    rclpy.init()
    node = RobotController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        return

    rclpy.shutdown()

if __name__ == '__main__':
    main()