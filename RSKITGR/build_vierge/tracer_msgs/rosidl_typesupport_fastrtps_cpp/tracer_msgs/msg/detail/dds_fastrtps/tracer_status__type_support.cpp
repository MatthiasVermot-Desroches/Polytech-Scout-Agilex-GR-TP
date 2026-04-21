// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from tracer_msgs:msg/TracerStatus.idl
// generated code does not contain a copyright notice
#include "tracer_msgs/msg/detail/tracer_status__rosidl_typesupport_fastrtps_cpp.hpp"
#include "tracer_msgs/msg/detail/tracer_status__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions
namespace std_msgs
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const std_msgs::msg::Header &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  std_msgs::msg::Header &);
size_t get_serialized_size(
  const std_msgs::msg::Header &,
  size_t current_alignment);
size_t
max_serialized_size_Header(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace std_msgs

namespace tracer_msgs
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const tracer_msgs::msg::TracerActuatorState &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  tracer_msgs::msg::TracerActuatorState &);
size_t get_serialized_size(
  const tracer_msgs::msg::TracerActuatorState &,
  size_t current_alignment);
size_t
max_serialized_size_TracerActuatorState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace tracer_msgs

namespace tracer_msgs
{
namespace msg
{
namespace typesupport_fastrtps_cpp
{
bool cdr_serialize(
  const tracer_msgs::msg::TracerLightState &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  tracer_msgs::msg::TracerLightState &);
size_t get_serialized_size(
  const tracer_msgs::msg::TracerLightState &,
  size_t current_alignment);
size_t
max_serialized_size_TracerLightState(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace tracer_msgs


namespace tracer_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_tracer_msgs
cdr_serialize(
  const tracer_msgs::msg::TracerStatus & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: header
  std_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
    ros_message.header,
    cdr);
  // Member: linear_velocity
  cdr << ros_message.linear_velocity;
  // Member: angular_velocity
  cdr << ros_message.angular_velocity;
  // Member: vehicle_state
  cdr << ros_message.vehicle_state;
  // Member: control_mode
  cdr << ros_message.control_mode;
  // Member: error_code
  cdr << ros_message.error_code;
  // Member: battery_voltage
  cdr << ros_message.battery_voltage;
  // Member: actuator_states
  {
    for (size_t i = 0; i < 2; i++) {
      tracer_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
        ros_message.actuator_states[i],
        cdr);
    }
  }
  // Member: light_control_enabled
  cdr << (ros_message.light_control_enabled ? true : false);
  // Member: front_light_state
  tracer_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
    ros_message.front_light_state,
    cdr);
  // Member: left_odomter
  cdr << ros_message.left_odomter;
  // Member: right_odomter
  cdr << ros_message.right_odomter;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_tracer_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  tracer_msgs::msg::TracerStatus & ros_message)
{
  // Member: header
  std_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
    cdr, ros_message.header);

  // Member: linear_velocity
  cdr >> ros_message.linear_velocity;

  // Member: angular_velocity
  cdr >> ros_message.angular_velocity;

  // Member: vehicle_state
  cdr >> ros_message.vehicle_state;

  // Member: control_mode
  cdr >> ros_message.control_mode;

  // Member: error_code
  cdr >> ros_message.error_code;

  // Member: battery_voltage
  cdr >> ros_message.battery_voltage;

  // Member: actuator_states
  {
    for (size_t i = 0; i < 2; i++) {
      tracer_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
        cdr,
        ros_message.actuator_states[i]);
    }
  }

  // Member: light_control_enabled
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message.light_control_enabled = tmp ? true : false;
  }

  // Member: front_light_state
  tracer_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
    cdr, ros_message.front_light_state);

  // Member: left_odomter
  cdr >> ros_message.left_odomter;

  // Member: right_odomter
  cdr >> ros_message.right_odomter;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_tracer_msgs
get_serialized_size(
  const tracer_msgs::msg::TracerStatus & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: header

  current_alignment +=
    std_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
    ros_message.header, current_alignment);
  // Member: linear_velocity
  {
    size_t item_size = sizeof(ros_message.linear_velocity);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: angular_velocity
  {
    size_t item_size = sizeof(ros_message.angular_velocity);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: vehicle_state
  {
    size_t item_size = sizeof(ros_message.vehicle_state);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: control_mode
  {
    size_t item_size = sizeof(ros_message.control_mode);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: error_code
  {
    size_t item_size = sizeof(ros_message.error_code);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: battery_voltage
  {
    size_t item_size = sizeof(ros_message.battery_voltage);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: actuator_states
  {
    size_t array_size = 2;

    for (size_t index = 0; index < array_size; ++index) {
      current_alignment +=
        tracer_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
        ros_message.actuator_states[index], current_alignment);
    }
  }
  // Member: light_control_enabled
  {
    size_t item_size = sizeof(ros_message.light_control_enabled);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: front_light_state

  current_alignment +=
    tracer_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
    ros_message.front_light_state, current_alignment);
  // Member: left_odomter
  {
    size_t item_size = sizeof(ros_message.left_odomter);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: right_odomter
  {
    size_t item_size = sizeof(ros_message.right_odomter);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_tracer_msgs
max_serialized_size_TracerStatus(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;


  // Member: header
  {
    size_t array_size = 1;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size =
        std_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_Header(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Member: linear_velocity
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: angular_velocity
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: vehicle_state
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: control_mode
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: error_code
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  // Member: battery_voltage
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: actuator_states
  {
    size_t array_size = 2;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size =
        tracer_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_TracerActuatorState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Member: light_control_enabled
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: front_light_state
  {
    size_t array_size = 1;


    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size =
        tracer_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_TracerLightState(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  // Member: left_odomter
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  // Member: right_odomter
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint64_t);
    current_alignment += array_size * sizeof(uint64_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint64_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = tracer_msgs::msg::TracerStatus;
    is_plain =
      (
      offsetof(DataType, right_odomter) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _TracerStatus__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const tracer_msgs::msg::TracerStatus *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _TracerStatus__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<tracer_msgs::msg::TracerStatus *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _TracerStatus__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const tracer_msgs::msg::TracerStatus *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _TracerStatus__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_TracerStatus(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _TracerStatus__callbacks = {
  "tracer_msgs::msg",
  "TracerStatus",
  _TracerStatus__cdr_serialize,
  _TracerStatus__cdr_deserialize,
  _TracerStatus__get_serialized_size,
  _TracerStatus__max_serialized_size
};

static rosidl_message_type_support_t _TracerStatus__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_TracerStatus__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace tracer_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_tracer_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<tracer_msgs::msg::TracerStatus>()
{
  return &tracer_msgs::msg::typesupport_fastrtps_cpp::_TracerStatus__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, tracer_msgs, msg, TracerStatus)() {
  return &tracer_msgs::msg::typesupport_fastrtps_cpp::_TracerStatus__handle;
}

#ifdef __cplusplus
}
#endif
