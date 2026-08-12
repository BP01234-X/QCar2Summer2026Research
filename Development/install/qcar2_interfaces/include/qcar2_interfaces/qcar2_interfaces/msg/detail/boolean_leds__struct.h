// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from qcar2_interfaces:msg/BooleanLeds.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_H_
#define QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'led_names'
#include "rosidl_runtime_c/string.h"
// Member 'values'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/BooleanLeds in the package qcar2_interfaces.
/**
  *  LED commands for QCar2
  * std_msgs/Header header
 */
typedef struct qcar2_interfaces__msg__BooleanLeds
{
  /// Names of the LED.
  /// Must be the following:
  ///    "left_outside_brake_light"
  ///    "left_inside_brake_light"
  ///    "right_inside_brake_light"
  ///    "right_outside_brake_light"
  ///    "left_reverse_light"
  ///    "right_reverse_light"
  ///    "left_rear_signal"
  ///    "right_rear_signal"
  ///    "left_outside_headlight"
  ///    "left_middle_headlight"
  ///    "left_inside_headlight"
  ///    "right_inside_headlight"
  ///    "right_middle_headlight"
  ///    "right_outside_headlight"
  ///    "left_front_signal"
  ///    "right_front_signal"
  rosidl_runtime_c__String__Sequence led_names;
  /// Values for the "led_names".
  /// The order must be identical to the "led_names".
  /// Units are:
  ///   false or true
  rosidl_runtime_c__boolean__Sequence values;
} qcar2_interfaces__msg__BooleanLeds;

// Struct for a sequence of qcar2_interfaces__msg__BooleanLeds.
typedef struct qcar2_interfaces__msg__BooleanLeds__Sequence
{
  qcar2_interfaces__msg__BooleanLeds * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} qcar2_interfaces__msg__BooleanLeds__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__STRUCT_H_
