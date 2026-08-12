// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from qcar2_interfaces:msg/MotorCommands.idl
// generated code does not contain a copyright notice
#include "qcar2_interfaces/msg/detail/motor_commands__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `motor_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `values`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
qcar2_interfaces__msg__MotorCommands__init(qcar2_interfaces__msg__MotorCommands * msg)
{
  if (!msg) {
    return false;
  }
  // motor_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->motor_names, 0)) {
    qcar2_interfaces__msg__MotorCommands__fini(msg);
    return false;
  }
  // values
  if (!rosidl_runtime_c__double__Sequence__init(&msg->values, 0)) {
    qcar2_interfaces__msg__MotorCommands__fini(msg);
    return false;
  }
  return true;
}

void
qcar2_interfaces__msg__MotorCommands__fini(qcar2_interfaces__msg__MotorCommands * msg)
{
  if (!msg) {
    return;
  }
  // motor_names
  rosidl_runtime_c__String__Sequence__fini(&msg->motor_names);
  // values
  rosidl_runtime_c__double__Sequence__fini(&msg->values);
}

bool
qcar2_interfaces__msg__MotorCommands__are_equal(const qcar2_interfaces__msg__MotorCommands * lhs, const qcar2_interfaces__msg__MotorCommands * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // motor_names
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->motor_names), &(rhs->motor_names)))
  {
    return false;
  }
  // values
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->values), &(rhs->values)))
  {
    return false;
  }
  return true;
}

bool
qcar2_interfaces__msg__MotorCommands__copy(
  const qcar2_interfaces__msg__MotorCommands * input,
  qcar2_interfaces__msg__MotorCommands * output)
{
  if (!input || !output) {
    return false;
  }
  // motor_names
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->motor_names), &(output->motor_names)))
  {
    return false;
  }
  // values
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->values), &(output->values)))
  {
    return false;
  }
  return true;
}

qcar2_interfaces__msg__MotorCommands *
qcar2_interfaces__msg__MotorCommands__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  qcar2_interfaces__msg__MotorCommands * msg = (qcar2_interfaces__msg__MotorCommands *)allocator.allocate(sizeof(qcar2_interfaces__msg__MotorCommands), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(qcar2_interfaces__msg__MotorCommands));
  bool success = qcar2_interfaces__msg__MotorCommands__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
qcar2_interfaces__msg__MotorCommands__destroy(qcar2_interfaces__msg__MotorCommands * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    qcar2_interfaces__msg__MotorCommands__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
qcar2_interfaces__msg__MotorCommands__Sequence__init(qcar2_interfaces__msg__MotorCommands__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  qcar2_interfaces__msg__MotorCommands * data = NULL;

  if (size) {
    data = (qcar2_interfaces__msg__MotorCommands *)allocator.zero_allocate(size, sizeof(qcar2_interfaces__msg__MotorCommands), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = qcar2_interfaces__msg__MotorCommands__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        qcar2_interfaces__msg__MotorCommands__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
qcar2_interfaces__msg__MotorCommands__Sequence__fini(qcar2_interfaces__msg__MotorCommands__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      qcar2_interfaces__msg__MotorCommands__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

qcar2_interfaces__msg__MotorCommands__Sequence *
qcar2_interfaces__msg__MotorCommands__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  qcar2_interfaces__msg__MotorCommands__Sequence * array = (qcar2_interfaces__msg__MotorCommands__Sequence *)allocator.allocate(sizeof(qcar2_interfaces__msg__MotorCommands__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = qcar2_interfaces__msg__MotorCommands__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
qcar2_interfaces__msg__MotorCommands__Sequence__destroy(qcar2_interfaces__msg__MotorCommands__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    qcar2_interfaces__msg__MotorCommands__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
qcar2_interfaces__msg__MotorCommands__Sequence__are_equal(const qcar2_interfaces__msg__MotorCommands__Sequence * lhs, const qcar2_interfaces__msg__MotorCommands__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!qcar2_interfaces__msg__MotorCommands__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
qcar2_interfaces__msg__MotorCommands__Sequence__copy(
  const qcar2_interfaces__msg__MotorCommands__Sequence * input,
  qcar2_interfaces__msg__MotorCommands__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(qcar2_interfaces__msg__MotorCommands);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    qcar2_interfaces__msg__MotorCommands * data =
      (qcar2_interfaces__msg__MotorCommands *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!qcar2_interfaces__msg__MotorCommands__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          qcar2_interfaces__msg__MotorCommands__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!qcar2_interfaces__msg__MotorCommands__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
