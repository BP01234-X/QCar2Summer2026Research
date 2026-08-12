// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from qcar2_interfaces:msg/BooleanLeds.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__BUILDER_HPP_
#define QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "qcar2_interfaces/msg/detail/boolean_leds__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace qcar2_interfaces
{

namespace msg
{

namespace builder
{

class Init_BooleanLeds_values
{
public:
  explicit Init_BooleanLeds_values(::qcar2_interfaces::msg::BooleanLeds & msg)
  : msg_(msg)
  {}
  ::qcar2_interfaces::msg::BooleanLeds values(::qcar2_interfaces::msg::BooleanLeds::_values_type arg)
  {
    msg_.values = std::move(arg);
    return std::move(msg_);
  }

private:
  ::qcar2_interfaces::msg::BooleanLeds msg_;
};

class Init_BooleanLeds_led_names
{
public:
  Init_BooleanLeds_led_names()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BooleanLeds_values led_names(::qcar2_interfaces::msg::BooleanLeds::_led_names_type arg)
  {
    msg_.led_names = std::move(arg);
    return Init_BooleanLeds_values(msg_);
  }

private:
  ::qcar2_interfaces::msg::BooleanLeds msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::qcar2_interfaces::msg::BooleanLeds>()
{
  return qcar2_interfaces::msg::builder::Init_BooleanLeds_led_names();
}

}  // namespace qcar2_interfaces

#endif  // QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__BUILDER_HPP_
