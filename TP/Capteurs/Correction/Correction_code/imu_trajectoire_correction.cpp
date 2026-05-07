#include <memory>
#include <cmath>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/magnetic_field.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "nav_msgs/msg/path.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"

using std::placeholders::_1;

class ImuTrajectory : public rclcpp::Node
{
public:
    ImuTrajectory()
    : Node("imu_trajectory")//,

    {
        // ----------- Paramètres -----------
        this->declare_parameter<std::string>("imu_topic", "/imu/data_raw");
        this->declare_parameter<std::string>("mag_topic", "/imu/mag");
        this->declare_parameter<double>("alpha", 0.98);

        std::string imu_topic = this->get_parameter("imu_topic").as_string();
        std::string mag_topic = this->get_parameter("mag_topic").as_string();
        alpha_     = this->get_parameter("alpha").as_double();

        // ----------- Subscriptions -----------
        imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
            imu_topic, rclcpp::QoS(10).reliable(),
            std::bind(&ImuTrajectory::imuCallback, this, _1));

        mag_sub_ = this->create_subscription<sensor_msgs::msg::MagneticField>(
            mag_topic, rclcpp::QoS(10).reliable(),
            std::bind(&ImuTrajectory::magCallback, this, _1));

        // ----------- Publishers -----------
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>(
            "/odometry/imu", 10);
        path_pub_ = this->create_publisher<nav_msgs::msg::Path>(
            "/trajectory_imu", 10);

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
            "imu_trajectory lancé | imu: %s | mag: %s | alpha: %.2f",
            imu_topic.c_str(), mag_topic.c_str(), alpha_);
        RCLCPP_WARN(this->get_logger(),
            "Dead reckoning from IMU only — expect drift. This is intentional.");
    }

private:
    void magCallback(const sensor_msgs::msg::MagneticField::SharedPtr msg)
    {
        last_mag_ = msg;
    }

    void imuCallback(const sensor_msgs::msg::Imu::SharedPtr msg)
    {
        rclcpp::Time t(msg->header.stamp);

        if (!last_time_)
        {
            last_time_ = t;
            initAttitudeFromAccel(msg);
            return;
        }

        double dt = (t - last_time_.value()).seconds();
        last_time_ = t;

        if (dt <= 0.0 || dt > 1.0)   
        //1. lecture des capteurs
        //accéléromètre (accélération linéaire)

        double ax = msg->linear_acceleration.x;
        double ay = msg->linear_acceleration.y;
        double az = msg->linear_acceleration.z;

        //gyromètre (vitesse angulaire)
        double gx = msg->angular_velocity.x;   
        double gy = msg->angular_velocity.y;   
        double gz = msg->angular_velocity.z;   

        //2. pitch et roll basé sur l'accéléromètre
        double roll_accel  = atan2(ay, az);
        double pitch_accel = atan2(-ax, sqrt(ay * ay + az * az));

        //3. filtre complémentaire avec l'accélérateur et le gyroscope
        roll_  = alpha_ * (roll_  + gx * dt) + (1.0 - alpha_) * roll_accel;
        pitch_ = alpha_ * (pitch_ + gy * dt) + (1.0 - alpha_) * pitch_accel;

        //4. Yaw à partir du magnétomètre (champ magnétique)
        if (last_mag_)
        {
            double mx = last_mag_->magnetic_field.x;
            double my = last_mag_->magnetic_field.y;
            double mz = last_mag_->magnetic_field.z;


            //check s'il y a bien un champ magnétique ou s'il n'y a pas de champ distordu
            double mag_norm = sqrt(mx*mx + my*my + mz*mz);
            if (mag_norm > 1e-6)
            {
                // Tilt-compensated yaw
                double mx2 =  mx * cos(pitch_) + mz * sin(pitch_);
                double my2 =  mx * sin(roll_) * sin(pitch_)
                            + my * cos(roll_)
                            - mz * sin(roll_) * cos(pitch_);
                double yaw_mag = atan2(-my2, mx2);

                // filtre complémentaire avec le magnétomètre et le gyromètre
                yaw_ = alpha_ * (yaw_ + gz * dt) + (1.0 - alpha_) * yaw_mag;
            }
            else
            {
                //Intégration avec uniquement le gyromètre
                yaw_ += gz * dt;
            }
        }
        else
        {
            //Pas encore de msg, donc intégration avec uniquement le gyromètre
            yaw_ += gz * dt;
        }

        yaw_ = normalizeAngle(yaw_);

        //5.Rotation vers le repère world
        double cr = cos(roll_),  sr = sin(roll_);
        double cp = cos(pitch_), sp = sin(pitch_);
        double cy = cos(yaw_),   sy = sin(yaw_);

        //Uniquement besoin de x et y dans une trajectoire 2D
        double ax_world =  (cy*cp)*ax
                     + (cy*sp*sr - sy*cr)*ay
                     + (cy*sp*cr + sy*sr)*az;

        double ay_world =  (sy*cp)*ax
                     + (sy*sp*sr + cy*cr)*ay
                     + (sy*sp*cr - cy*sr)*az;

        //6 suppression du bruit faible
        const double accel_threshold = 0.05;
        if (std::abs(ax_world) < accel_threshold) ax_world = 0.0;
        if (std::abs(ay_world) < accel_threshold) ay_world = 0.0;

        //7 Calcul de la position
        vx_ += ax_world * dt;
        vy_ += ay_world * dt;
        x_  += vx_ * dt;
        y_  += vy_ * dt;

        //8 publisher de l'odométrie calculée
        nav_msgs::msg::Odometry odom_out;
        odom_out.header.stamp    = msg->header.stamp;
        odom_out.header.frame_id = "odom";
        odom_out.child_frame_id  = "base_link";

        odom_out.pose.pose.position.x  = x_;
        odom_out.pose.pose.position.y  = -y_;
        odom_out.pose.pose.position.z  = 0.0;
        odom_out.pose.pose.orientation = rpyToQuaternion(roll_, pitch_, yaw_);

        odom_out.twist.twist.linear.x  = vx_;
        odom_out.twist.twist.linear.y  = vy_;
        odom_out.twist.twist.angular.z = gz;

        odom_pub_->publish(odom_out);

        //9 publisher du path
        geometry_msgs::msg::PoseStamped pose;
        pose.header = odom_out.header;
        pose.pose   = odom_out.pose.pose;
        path_msg_.header.stamp = odom_out.header.stamp;
        path_msg_.poses.push_back(pose);

        if (path_msg_.poses.size() > 1000)
            path_msg_.poses.erase(path_msg_.poses.begin());

        path_pub_->publish(path_msg_);
    }

    void initAttitudeFromAccel(const sensor_msgs::msg::Imu::SharedPtr msg)
    {
        double ax = msg->linear_acceleration.x;
        double ay = msg->linear_acceleration.y;
        double az = msg->linear_acceleration.z;
        if (invert_z_) az = -az;

        roll_  = atan2(ay, az);
        pitch_ = atan2(-ax, sqrt(ay * ay + az * az));
    }

    double normalizeAngle(double angle)
    {
        return atan2(sin(angle), cos(angle));
    }

    geometry_msgs::msg::Quaternion rpyToQuaternion(double roll, double pitch, double yaw)
    {
        double cy = cos(yaw   * 0.5), sy = sin(yaw   * 0.5);
        double cp = cos(pitch * 0.5), sp = sin(pitch * 0.5);
        double cr = cos(roll  * 0.5), sr = sin(roll  * 0.5);

        geometry_msgs::msg::Quaternion q;
        q.w = cr * cp * cy + sr * sp * sy;
        q.x = sr * cp * cy - cr * sp * sy;
        q.y = cr * sp * cy + sr * cp * sy;
        q.z = cr * cp * sy - sr * sp * cy;
        return q;
    }

    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr         imu_sub_;
    rclcpp::Subscription<sensor_msgs::msg::MagneticField>::SharedPtr mag_sub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr           odom_pub_;
    rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr               path_pub_;
    rclcpp::TimerBase::SharedPtr timer_;

    nav_msgs::msg::Path path_msg_;

    sensor_msgs::msg::MagneticField::SharedPtr last_mag_;

    std::optional<rclcpp::Time> last_time_;

    double roll_, pitch_, yaw_;

    double x_, y_;
    double vx_, vy_;

    double alpha_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ImuTrajectory>());
    rclcpp::shutdown();
    return 0;
}