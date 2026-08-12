// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from qcar2_interfaces:msg/MotorCommands.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "qcar2_interfaces/msg/detail/motor_commands__rosidl_typesupport_introspection_c.h"
#include "qcar2_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "qcar2_interfaces/msg/detail/motor_commands__functions.h"
#include "qcar2_interfaces/msg/detail/motor_commands__struct.h"


// Include directives for member types
// Member `motor_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `values`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  qcar2_interfaces__msg__MotorCommands__init(message_memory);
}

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_fini_function(void * message_memory)
{
  qcar2_interfaces__msg__MotorCommands__fini(message_memory);
}

size_t qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__size_function__MotorCommands__motor_names(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__motor_names(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__motor_names(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__fetch_function__MotorCommands__motor_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__motor_names(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__assign_function__MotorCommands__motor_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__motor_names(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__resize_function__MotorCommands__motor_names(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

size_t qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__size_function__MotorCommands__values(
  const void * untyped_member)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return member->size;
}

const void * qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__values(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void * qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__values(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__fetch_function__MotorCommands__values(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const double * item =
    ((const double *)
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__values(untyped_member, index));
  double * value =
    (double *)(untyped_value);
  *value = *item;
}

void qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__assign_function__MotorCommands__values(
  void * untyped_member, size_t index, const void * untyped_value)
{
  double * item =
    ((double *)
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__values(untyped_member, index));
  const double * value =
    (const double *)(untyped_value);
  *item = *value;
}

bool qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__resize_function__MotorCommands__values(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  rosidl_runtime_c__double__Sequence__fini(member);
  return rosidl_runtime_c__double__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_member_array[2] = {
  {
    "motor_names",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(qcar2_interfaces__msg__MotorCommands, motor_names),  // bytes offset in struct
    NULL,  // default value
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__size_function__MotorCommands__motor_names,  // size() function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__motor_names,  // get_const(index) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__motor_names,  // get(index) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__fetch_function__MotorCommands__motor_names,  // fetch(index, &value) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__assign_function__MotorCommands__motor_names,  // assign(index, value) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__resize_function__MotorCommands__motor_names  // resize(index) function pointer
  },
  {
    "values",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(qcar2_interfaces__msg__MotorCommands, values),  // bytes offset in struct
    NULL,  // default value
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__size_function__MotorCommands__values,  // size() function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_const_function__MotorCommands__values,  // get_const(index) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__get_function__MotorCommands__values,  // get(index) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__fetch_function__MotorCommands__values,  // fetch(index, &value) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__assign_function__MotorCommands__values,  // assign(index, value) function pointer
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__resize_function__MotorCommands__values  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_members = {
  "qcar2_interfaces__msg",  // message namespace
  "MotorCommands",  // message name
  2,  // number of fields
  sizeof(qcar2_interfaces__msg__MotorCommands),
  qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_member_array,  // message members
  qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_init_function,  // function to initialize message memory (memory has to be allocated)
  qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_type_support_handle = {
  0,
  &qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_qcar2_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, qcar2_interfaces, msg, MotorCommands)() {
  if (!qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_type_support_handle.typesupport_identifier) {
    qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &qcar2_interfaces__msg__MotorCommands__rosidl_typesupport_introspection_c__MotorCommands_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
