#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/magnetic_field.hpp"
#include <cmath>

class ImuFusionNode : public rclcpp::Node
{
public:
    ImuFusionNode()
    : Node("imu_fusion_node")
    {
        imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
            "",
            rclcpp::SensorDataQoS(),
            std::bind(&ImuFusionNode::imu_callback, this, std::placeholders::_1)
        );

        mag_sub_ = this->create_subscription<sensor_msgs::msg::MagneticField>(
            "",
            rclcpp::SensorDataQoS(),
            std::bind(&ImuFusionNode::mag_callback, this, std::placeholders::_1)
        );

        imu_pub_ = this->create_publisher<sensor_msgs::msg::Imu>(
            "/imu/data",
            10
        );
    }

private:
    sensor_msgs::msg::Imu::SharedPtr last_imu_;
    sensor_msgs::msg::MagneticField::SharedPtr last_mag_;

    void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg)
    {
        last_imu_ = msg;
        compute_and_publish();
    }

    void mag_callback(const sensor_msgs::msg::MagneticField::SharedPtr msg)
    {
        last_mag_ = msg;
        compute_and_publish();
    }

    void compute_and_publish()
    {
        if (!last_imu_ || !last_mag_) return;

        // Accéléromètre
        double ax = last_imu_-> ;
        double ay = last_imu_-> ;
        double az = last_imu_-> ;

        //az = -az; //ajustement du signe si besoin

        double roll  = ;
        double pitch = ;

        // Magnétomètre
        double mx = last_mag_-> ;
        double my = last_mag_-> ;
        double mz = last_mag_-> ;

        // Tilt compensation
        double mx2 =  ;
        double my2 =  ;

        double yaw = ;

        //Quaternion
        double cy = cos(yaw * 0.5);
        double sy = sin(yaw * 0.5);
        double cp = cos(pitch * 0.5);
        double sp = sin(pitch * 0.5);
        double cr = cos(roll * 0.5);
        double sr = sin(roll * 0.5);

        sensor_msgs::msg::Imu imu_msg;

        // Header
        imu_msg.header.stamp = this->now();
        imu_msg.header.frame_id = "imu_link";

        // Orientation
        imu_msg.orientation.w = cr * cp * cy + sr * sp * sy;
        imu_msg.orientation.x = sr * cp * cy - cr * sp * sy;
        imu_msg.orientation.y = cr * sp * cy + sr * cp * sy;
        imu_msg.orientation.z = cr * cp * sy - sr * sp * cy;

        //Copie du gyromètre et de l'accéléromètre
        imu_msg.angular_velocity = last_imu_->angular_velocity;
        imu_msg.linear_acceleration = last_imu_->linear_acceleration;

        // Orientation covariance
        imu_msg.orientation_covariance[0] = 0.00;
        imu_msg.orientation_covariance[4] = 0.00;
        imu_msg.orientation_covariance[8] = 0.00;

        // Angular velocity covariance
        imu_msg.angular_velocity_covariance[0] = 0.00;
        imu_msg.angular_velocity_covariance[4] = 0.00;
        imu_msg.angular_velocity_covariance[8] = 0.00;

        // Linear acceleration covariance
        imu_msg.linear_acceleration_covariance[0] = 0.00;
        imu_msg.linear_acceleration_covariance[4] = 0.00;
        imu_msg.linear_acceleration_covariance[8] = 0.00;

        imu_pub_->publish(imu_msg);
    }

    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
    rclcpp::Subscription<sensor_msgs::msg::MagneticField>::SharedPtr mag_sub_;
    rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_pub_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ImuFusionNode>());
    rclcpp::shutdown();
    return 0;
}