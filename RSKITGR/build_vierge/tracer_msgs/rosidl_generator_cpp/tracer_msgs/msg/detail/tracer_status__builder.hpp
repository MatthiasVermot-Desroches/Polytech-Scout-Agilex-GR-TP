// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from tracer_msgs:msg/TracerStatus.idl
// generated code does not contain a copyright notice

#ifndef TRACER_MSGS__MSG__DETAIL__TRACER_STATUS__BUILDER_HPP_
#define TRACER_MSGS__MSG__DETAIL__TRACER_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "tracer_msgs/msg/detail/tracer_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace tracer_msgs
{

namespace msg
{

namespace builder
{

class Init_TracerStatus_right_odomter
{
public:
  explicit Init_TracerStatus_right_odomter(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  ::tracer_msgs::msg::TracerStatus right_odomter(::tracer_msgs::msg::TracerStatus::_right_odomter_type arg)
  {
    msg_.right_odomter = std::move(arg);
    return std::move(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_left_odomter
{
public:
  explicit Init_TracerStatus_left_odomter(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_right_odomter left_odomter(::tracer_msgs::msg::TracerStatus::_left_odomter_type arg)
  {
    msg_.left_odomter = std::move(arg);
    return Init_TracerStatus_right_odomter(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_front_light_state
{
public:
  explicit Init_TracerStatus_front_light_state(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_left_odomter front_light_state(::tracer_msgs::msg::TracerStatus::_front_light_state_type arg)
  {
    msg_.front_light_state = std::move(arg);
    return Init_TracerStatus_left_odomter(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_light_control_enabled
{
public:
  explicit Init_TracerStatus_light_control_enabled(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_front_light_state light_control_enabled(::tracer_msgs::msg::TracerStatus::_light_control_enabled_type arg)
  {
    msg_.light_control_enabled = std::move(arg);
    return Init_TracerStatus_front_light_state(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_actuator_states
{
public:
  explicit Init_TracerStatus_actuator_states(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_light_control_enabled actuator_states(::tracer_msgs::msg::TracerStatus::_actuator_states_type arg)
  {
    msg_.actuator_states = std::move(arg);
    return Init_TracerStatus_light_control_enabled(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_battery_voltage
{
public:
  explicit Init_TracerStatus_battery_voltage(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_actuator_states battery_voltage(::tracer_msgs::msg::TracerStatus::_battery_voltage_type arg)
  {
    msg_.battery_voltage = std::move(arg);
    return Init_TracerStatus_actuator_states(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_error_code
{
public:
  explicit Init_TracerStatus_error_code(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_battery_voltage error_code(::tracer_msgs::msg::TracerStatus::_error_code_type arg)
  {
    msg_.error_code = std::move(arg);
    return Init_TracerStatus_battery_voltage(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_control_mode
{
public:
  explicit Init_TracerStatus_control_mode(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_error_code control_mode(::tracer_msgs::msg::TracerStatus::_control_mode_type arg)
  {
    msg_.control_mode = std::move(arg);
    return Init_TracerStatus_error_code(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_vehicle_state
{
public:
  explicit Init_TracerStatus_vehicle_state(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_control_mode vehicle_state(::tracer_msgs::msg::TracerStatus::_vehicle_state_type arg)
  {
    msg_.vehicle_state = std::move(arg);
    return Init_TracerStatus_control_mode(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_angular_velocity
{
public:
  explicit Init_TracerStatus_angular_velocity(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_vehicle_state angular_velocity(::tracer_msgs::msg::TracerStatus::_angular_velocity_type arg)
  {
    msg_.angular_velocity = std::move(arg);
    return Init_TracerStatus_vehicle_state(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_linear_velocity
{
public:
  explicit Init_TracerStatus_linear_velocity(::tracer_msgs::msg::TracerStatus & msg)
  : msg_(msg)
  {}
  Init_TracerStatus_angular_velocity linear_velocity(::tracer_msgs::msg::TracerStatus::_linear_velocity_type arg)
  {
    msg_.linear_velocity = std::move(arg);
    return Init_TracerStatus_angular_velocity(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

class Init_TracerStatus_header
{
public:
  Init_TracerStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TracerStatus_linear_velocity header(::tracer_msgs::msg::TracerStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TracerStatus_linear_velocity(msg_);
  }

private:
  ::tracer_msgs::msg::TracerStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::tracer_msgs::msg::TracerStatus>()
{
  return tracer_msgs::msg::builder::Init_TracerStatus_header();
}

}  // namespace tracer_msgs

#endif  // TRACER_MSGS__MSG__DETAIL__TRACER_STATUS__BUILDER_HPP_
