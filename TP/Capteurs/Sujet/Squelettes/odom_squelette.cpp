#include <memory>
#include <vector>
#include <cmath>
#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/quaternion.hpp"

using std::placeholders::_1;

class OdomReconstruction : public rclcpp::Node
{
public:
    OdomReconstruction()
    : Node("odom_reconstruction")
    {
        // ----------- Paramètres ----------- 
        this->declare_parameter<std::string>("odom_topic",        ""); //Complétez par le nom du topic
        this->declare_parameter<std::string>("path_topic",        ""); //Choisissez un nom
        this->declare_parameter<std::string>("output_odom_topic", ""); //Choisissez un nom

        std::string odom_topic        = this->get_parameter("odom_topic").as_string();
        std::string path_topic        = this->get_parameter("path_topic").as_string();
        std::string output_odom_topic = this->get_parameter("output_odom_topic").as_string();

        // ----------- Subscription -----------
        sub_ = this->create_subscription<nav_msgs::msg::Odometry>(
            odom_topic, 10,
            std::bind(&OdomReconstruction::odomCallback, this, _1));

        // ----------- Publishers -----------
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(output_odom_topic, 10);
        path_pub_ = this->create_publisher<nav_msgs::msg::Path>(path_topic, 10);

        path_msg_.header.frame_id = "odom";

        timer_ = this->create_wall_timer(
            std::chrono::seconds(1),
            [this]() {
                if (!path_msg_.poses.empty())
                {
                    path_msg_.header.stamp = this->now();
                    path_pub_->publish(path_msg_);
                }
            });

        RCLCPP_INFO(this->get_logger(),
            "odom_reconstruction started | in: %s | path out: %s | odom out: %s",
            odom_topic.c_str(), path_topic.c_str(), output_odom_topic.c_str());
    }

private:
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
    {
        geometry_msgs::msg::PoseStamped pose;
        pose.header = msg->header;
        pose.pose   = msg->pose.pose;
        path_msg_.header.stamp = msg->header.stamp;
        path_msg_.poses.push_back(pose);

        if (path_msg_.poses.size() > 1000)
            path_msg_.poses.erase(path_msg_.poses.begin());

        path_pub_->publish(path_msg_);
    }

    // ---------------- VARIABLES ----------------
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr    odom_pub_;
    rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr        path_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    nav_msgs::msg::Path path_msg_;
    std::optional<rclcpp::Time> last_time_;
};

// ---------------- MAIN ----------------
int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<OdomReconstruction>());
    rclcpp::shutdown();
    return 0;
}