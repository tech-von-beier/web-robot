cmake_minimum_required(VERSION 3.0.2)
project(web_robot)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  message_generation
)

## Generate messages in the 'msg' folder
add_message_files(
  FILES
  Jog.msg
)

## Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package(
  CATKIN_DEPENDS message_runtime
)

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

## Mark executable scripts (Python) for installation
catkin_install_python(PROGRAMS
  scripts/teleop_gesture.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

