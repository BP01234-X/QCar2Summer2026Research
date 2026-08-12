// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from qcar2_interfaces:msg/MotorCommands.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__TRAITS_HPP_
#define QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "qcar2_interfaces/msg/detail/motor_commands__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace qcar2_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const MotorCommands & msg,
  std::ostream & out)
{
  out << "{";
  // member: motor_names
  {
    if (msg.motor_names.size() == 0) {
      out << "motor_names: []";
    } else {
      out << "motor_names: [";
      size_t pending_items = msg.motor_names.size();
      for (auto item : msg.motor_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: values
  {
    if (msg.values.size() == 0) {
      out << "values: []";
    } else {
      out << "values: [";
      size_t pending_items = msg.values.size();
      for (auto item : msg.values) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MotorCommands & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: motor_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.motor_names.size() == 0) {
      out << "motor_names: []\n";
    } else {
      out << "motor_names:\n";
      for (auto item : msg.motor_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: values
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.values.size() == 0) {
      out << "values: []\n";
    } else {
      out << "values:\n";
      for (auto item : msg.values) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MotorCommands & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace qcar2_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use qcar2_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const qcar2_interfaces::msg::MotorCommands & msg,
  std::ostream & out, size_t indentation = 0)
{
  qcar2_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use qcar2_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const qcar2_interfaces::msg::MotorCommands & msg)
{
  return qcar2_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<qcar2_interfaces::msg::MotorCommands>()
{
  return "qcar2_interfaces::msg::MotorCommands";
}

template<>
inline const char * name<qcar2_interfaces::msg::MotorCommands>()
{
  return "qcar2_interfaces/msg/MotorCommands";
}

template<>
struct has_fixed_size<qcar2_interfaces::msg::MotorCommands>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<qcar2_interfaces::msg::MotorCommands>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<qcar2_interfaces::msg::MotorCommands>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__TRAITS_HPP_
