#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"

class OdomCovarianceFixer : public rclcpp::Node
{
public:
    OdomCovarianceFixer() : Node("odom_covariance_fixer")
    {
        sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
            "/odom", 10,
            std::bind(&OdomCovarianceFixer::callback, this, std::placeholders::_1));

        pub_ = this->create_publisher<nav_msgs::msg::Odometry>("/odom_fixed", 10);

        RCLCPP_INFO(this->get_logger(), "Odom covariance fixer started.");
    }

private:
    void callback(const nav_msgs::msg::Odometry::SharedPtr msg)
    {
        nav_msgs::msg::Odometry fixed = *msg;

        fixed.pose.covariance = {
            0.05, 0.0,   0.0,  0.0,  0.0,  0.0,
            0.0,   0.05, 0.0,  0.0,  0.0,  0.0,
            0.0,   0.0,   999.0,  0.0,  0.0,  0.0,
            0.0,   0.0,   0.0,  999.0,  0.0,  0.0,
            0.0,   0.0,   0.0,  0.0,  999.0,  0.0,
            0.0,   0.0,   0.0,  0.0,  0.0,  0.2
        };

        fixed.twist.covariance = {
            0.02, 0.0,  0.0,  0.0,  0.0,  0.0,
            0.0,   0.02,  0.0,  0.0,  0.0,  0.0,
            0.0,   0.0,  999.0,  0.0,  0.0,  0.0,
            0.0,   0.0,  0.0,  999.0,  0.0,  0.0,
            0.0,   0.0,  0.0,  0.0,  999.0,  0.0,
            0.0,   0.0,  0.0,  0.0,  0.0,  0.05
        };

        pub_->publish(fixed);
    }

    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr pub_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OdomCovarianceFixer>());
    rclcpp::shutdown();
    return 0;
}