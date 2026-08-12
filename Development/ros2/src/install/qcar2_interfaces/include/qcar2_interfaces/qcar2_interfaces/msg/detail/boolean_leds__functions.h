// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from qcar2_interfaces:msg/BooleanLeds.idl
// generated code does not contain a copyright notice

#ifndef QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__FUNCTIONS_H_
#define QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "qcar2_interfaces/msg/rosidl_generator_c__visibility_control.h"

#include "qcar2_interfaces/msg/detail/boolean_leds__struct.h"

/// Initialize msg/BooleanLeds message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * qcar2_interfaces__msg__BooleanLeds
 * )) before or use
 * qcar2_interfaces__msg__BooleanLeds__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__init(qcar2_interfaces__msg__BooleanLeds * msg);

/// Finalize msg/BooleanLeds message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
void
qcar2_interfaces__msg__BooleanLeds__fini(qcar2_interfaces__msg__BooleanLeds * msg);

/// Create msg/BooleanLeds message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * qcar2_interfaces__msg__BooleanLeds__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
qcar2_interfaces__msg__BooleanLeds *
qcar2_interfaces__msg__BooleanLeds__create();

/// Destroy msg/BooleanLeds message.
/**
 * It calls
 * qcar2_interfaces__msg__BooleanLeds__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
void
qcar2_interfaces__msg__BooleanLeds__destroy(qcar2_interfaces__msg__BooleanLeds * msg);

/// Check for msg/BooleanLeds message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__are_equal(const qcar2_interfaces__msg__BooleanLeds * lhs, const qcar2_interfaces__msg__BooleanLeds * rhs);

/// Copy a msg/BooleanLeds message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__copy(
  const qcar2_interfaces__msg__BooleanLeds * input,
  qcar2_interfaces__msg__BooleanLeds * output);

/// Initialize array of msg/BooleanLeds messages.
/**
 * It allocates the memory for the number of elements and calls
 * qcar2_interfaces__msg__BooleanLeds__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__Sequence__init(qcar2_interfaces__msg__BooleanLeds__Sequence * array, size_t size);

/// Finalize array of msg/BooleanLeds messages.
/**
 * It calls
 * qcar2_interfaces__msg__BooleanLeds__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
void
qcar2_interfaces__msg__BooleanLeds__Sequence__fini(qcar2_interfaces__msg__BooleanLeds__Sequence * array);

/// Create array of msg/BooleanLeds messages.
/**
 * It allocates the memory for the array and calls
 * qcar2_interfaces__msg__BooleanLeds__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
qcar2_interfaces__msg__BooleanLeds__Sequence *
qcar2_interfaces__msg__BooleanLeds__Sequence__create(size_t size);

/// Destroy array of msg/BooleanLeds messages.
/**
 * It calls
 * qcar2_interfaces__msg__BooleanLeds__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
void
qcar2_interfaces__msg__BooleanLeds__Sequence__destroy(qcar2_interfaces__msg__BooleanLeds__Sequence * array);

/// Check for msg/BooleanLeds message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__Sequence__are_equal(const qcar2_interfaces__msg__BooleanLeds__Sequence * lhs, const qcar2_interfaces__msg__BooleanLeds__Sequence * rhs);

/// Copy an array of msg/BooleanLeds messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_qcar2_interfaces
bool
qcar2_interfaces__msg__BooleanLeds__Sequence__copy(
  const qcar2_interfaces__msg__BooleanLeds__Sequence * input,
  qcar2_interfaces__msg__BooleanLeds__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // QCAR2_INTERFACES__MSG__DETAIL__BOOLEAN_LEDS__FUNCTIONS_H_
