// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from qcar2_interfaces:msg/MotorCommands.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__STRUCT_H_
#define QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'motor_names'
#include "rosidl_runtime_c/string.h"
// Member 'values'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/MotorCommands in the package qcar2_interfaces.
/**
  *  Driving command for QCar2 to directly control the Steering angle and Motor throttle
  * std_msgs/Header header
 */
typedef struct qcar2_interfaces__msg__MotorCommands
{
  /// Names of whether to drive steering or throttle. Must be "steering_angle" or "motor_throttle"
  rosidl_runtime_c__String__Sequence motor_names;
  /// Values for the "command_names".
  /// The order must be identical to the "command_names".
  /// Units are:
  ///   "rad" for "steering_angle"
  ///   "m/s" for "motor_throttle"
  rosidl_runtime_c__double__Sequence values;
} qcar2_interfaces__msg__MotorCommands;

// Struct for a sequence of qcar2_interfaces__msg__MotorCommands.
typedef struct qcar2_interfaces__msg__MotorCommands__Sequence
{
  qcar2_interfaces__msg__MotorCommands * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} qcar2_interfaces__msg__MotorCommands__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // QCAR2_INTERFACES__MSG__DETAIL__MOTOR_COMMANDS__STRUCT_H_
