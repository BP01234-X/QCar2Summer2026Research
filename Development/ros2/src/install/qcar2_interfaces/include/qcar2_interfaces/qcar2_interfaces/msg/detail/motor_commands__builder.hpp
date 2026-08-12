// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from qcar2_interfaces:msg/MotorCommands.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__BUILDER_HPP_
#define QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "qcar2_interfaces/msg/detail/motor_commands__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace qcar2_interfaces
{

namespace msg
{

namespace builder
{

class Init_MotorCommands_values
{
public:
  explicit Init_MotorCommands_values(::qcar2_interfaces::msg::MotorCommands & msg)
  : msg_(msg)
  {}
  ::qcar2_interfaces::msg::MotorCommands values(::qcar2_interfaces::msg::MotorCommands::_values_type arg)
  {
    msg_.values = std::move(arg);
    return std::move(msg_);
  }

private:
  ::qcar2_interfaces::msg::MotorCommands msg_;
};

class Init_MotorCommands_motor_names
{
public:
  Init_MotorCommands_motor_names()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MotorCommands_values motor_names(::qcar2_interfaces::msg::MotorCommands::_motor_names_type arg)
  {
    msg_.motor_names = std::move(arg);
    return Init_MotorCommands_values(msg_);
  }

private:
  ::qcar2_interfaces::msg::MotorCommands msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::qcar2_interfaces::msg::MotorCommands>()
{
  return qcar2_interfaces::msg::builder::Init_MotorCommands_motor_names();
}

}  // namespace qcar2_interfaces

#endif  // QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__BUILDER_HPP_
