// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from qcar2_interfaces:msg/BooleanLeds.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_HPP_
#define QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__qcar2_interfaces__msg__BooleanLeds __attribute__((deprecated))
#else
# define DEPRECATED__qcar2_interfaces__msg__BooleanLeds __declspec(deprecated)
#endif

namespace qcar2_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct BooleanLeds_
{
  using Type = BooleanLeds_<ContainerAllocator>;

  explicit BooleanLeds_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
  }

  explicit BooleanLeds_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
    (void)_alloc;
  }

  // field types and members
  using _led_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _led_names_type led_names;
  using _values_type =
    std::vector<bool, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<bool>>;
  _values_type values;

  // setters for named parameter idiom
  Type & set__led_names(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->led_names = _arg;
    return *this;
  }
  Type & set__values(
    const std::vector<bool, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<bool>> & _arg)
  {
    this->values = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> *;
  using ConstRawPtr =
    const qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__qcar2_interfaces__msg__BooleanLeds
    std::shared_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__qcar2_interfaces__msg__BooleanLeds
    std::shared_ptr<qcar2_interfaces::msg::BooleanLeds_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BooleanLeds_ & other) const
  {
    if (this->led_names != other.led_names) {
      return false;
    }
    if (this->values != other.values) {
      return false;
    }
    return true;
  }
  bool operator!=(const BooleanLeds_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BooleanLeds_

// alias to use template instance with default allocator
using BooleanLeds =
  qcar2_interfaces::msg::BooleanLeds_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace qcar2_interfaces

#endif  // QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_HPP_
