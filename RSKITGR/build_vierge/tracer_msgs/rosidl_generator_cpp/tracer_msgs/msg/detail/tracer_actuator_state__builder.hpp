// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from tracer_msgs:msg/TracerActuatorState.idl
// generated code does not contain a copyright notice

#ifndef TRACER_MSGS__MSG__DETAIL__TRACER_ACTUATOR_STATE__BUILDER_HPP_
#define TRACER_MSGS__MSG__DETAIL__TRACER_ACTUATOR_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "tracer_msgs/msg/detail/tracer_actuator_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace tracer_msgs
{

namespace msg
{

namespace builder
{

class Init_TracerActuatorState_driver_state
{
public:
  explicit Init_TracerActuatorState_driver_state(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  ::tracer_msgs::msg::TracerActuatorState driver_state(::tracer_msgs::msg::TracerActuatorState::_driver_state_type arg)
  {
    msg_.driver_state = std::move(arg);
    return std::move(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_motor_temperature
{
public:
  explicit Init_TracerActuatorState_motor_temperature(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_driver_state motor_temperature(::tracer_msgs::msg::TracerActuatorState::_motor_temperature_type arg)
  {
    msg_.motor_temperature = std::move(arg);
    return Init_TracerActuatorState_driver_state(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_driver_temperature
{
public:
  explicit Init_TracerActuatorState_driver_temperature(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_motor_temperature driver_temperature(::tracer_msgs::msg::TracerActuatorState::_driver_temperature_type arg)
  {
    msg_.driver_temperature = std::move(arg);
    return Init_TracerActuatorState_motor_temperature(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_driver_voltage
{
public:
  explicit Init_TracerActuatorState_driver_voltage(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_driver_temperature driver_voltage(::tracer_msgs::msg::TracerActuatorState::_driver_voltage_type arg)
  {
    msg_.driver_voltage = std::move(arg);
    return Init_TracerActuatorState_driver_temperature(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_pulse_count
{
public:
  explicit Init_TracerActuatorState_pulse_count(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_driver_voltage pulse_count(::tracer_msgs::msg::TracerActuatorState::_pulse_count_type arg)
  {
    msg_.pulse_count = std::move(arg);
    return Init_TracerActuatorState_driver_voltage(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_current
{
public:
  explicit Init_TracerActuatorState_current(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_pulse_count current(::tracer_msgs::msg::TracerActuatorState::_current_type arg)
  {
    msg_.current = std::move(arg);
    return Init_TracerActuatorState_pulse_count(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_rpm
{
public:
  explicit Init_TracerActuatorState_rpm(::tracer_msgs::msg::TracerActuatorState & msg)
  : msg_(msg)
  {}
  Init_TracerActuatorState_current rpm(::tracer_msgs::msg::TracerActuatorState::_rpm_type arg)
  {
    msg_.rpm = std::move(arg);
    return Init_TracerActuatorState_current(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

class Init_TracerActuatorState_motor_id
{
public:
  Init_TracerActuatorState_motor_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TracerActuatorState_rpm motor_id(::tracer_msgs::msg::TracerActuatorState::_motor_id_type arg)
  {
    msg_.motor_id = std::move(arg);
    return Init_TracerActuatorState_rpm(msg_);
  }

private:
  ::tracer_msgs::msg::TracerActuatorState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::tracer_msgs::msg::TracerActuatorState>()
{
  return tracer_msgs::msg::builder::Init_TracerActuatorState_motor_id();
}

}  // namespace tracer_msgs

#endif  // TRACER_MSGS__MSG__DETAIL__TRACER_ACTUATOR_STATE__BUILDER_HPP_
