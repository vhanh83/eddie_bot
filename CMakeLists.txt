cmake_minimum_required(VERSION 3.8)
project(eddie_bot)

# ============================================================
# C++ Standard
# ============================================================

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()


# ============================================================
# ROS 2 Dependencies
# ============================================================

find_package(ament_cmake REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)


# ============================================================
# LibSerial
#
# Ubuntu 22.04 PC / Raspberry Pi 4
#
# Install:
#   sudo apt install libserial-dev
# ============================================================

find_package(PkgConfig REQUIRED)

pkg_check_modules(LIBSERIAL REQUIRED libserial)


# ============================================================
# Hardware Plugin
# ============================================================

add_library(${PROJECT_NAME} SHARED

  hardware/diffbot_system.cpp

)


# ============================================================
# Include Directories
# ============================================================

target_include_directories(${PROJECT_NAME} PUBLIC

  # Project headers
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/hardware/include>

  # Installed headers
  $<INSTALL_INTERFACE:include>

  # LibSerial headers
  ${LIBSERIAL_INCLUDE_DIRS}

)


# ============================================================
# ROS 2 Dependencies
# ============================================================

ament_target_dependencies(${PROJECT_NAME}

  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle

)


# ============================================================
# LibSerial
# ============================================================

target_link_directories(${PROJECT_NAME} PUBLIC
  ${LIBSERIAL_LIBRARY_DIRS}
)

target_link_libraries(${PROJECT_NAME}

  ${LIBSERIAL_LIBRARIES}

)


# ============================================================
# Compile Options from LibSerial
# ============================================================

target_compile_options(${PROJECT_NAME} PUBLIC
  ${LIBSERIAL_CFLAGS_OTHER}
)


# ============================================================
# ros2_control Hardware Plugin
# ============================================================

pluginlib_export_plugin_description_file(
  hardware_interface
  eddie_bot.xml
)


# ============================================================
# Install Headers
# ============================================================

install(
  DIRECTORY hardware/include/
  DESTINATION include
)


# ============================================================
# Install Hardware Library
# ============================================================

install(
  TARGETS ${PROJECT_NAME}

  EXPORT export_${PROJECT_NAME}

  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)


# ============================================================
# Install Config
# ============================================================

install(
  DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)


# ============================================================
# Install Description
# ============================================================

install(
  DIRECTORY description/
  DESTINATION share/${PROJECT_NAME}/description
)


# ============================================================
# Install Launch
# ============================================================

install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)


# ============================================================
# Export Library
# ============================================================

ament_export_targets(
  export_${PROJECT_NAME}
  HAS_LIBRARY_TARGET
)


# ============================================================
# Export ROS 2 Dependencies
# ============================================================

ament_export_dependencies(
  hardware_interface
  pluginlib
  rclcpp
  rclcpp_lifecycle
)


# ============================================================
# Testing
# ============================================================

if(BUILD_TESTING)

  find_package(ament_lint_auto REQUIRED)

  ament_lint_auto_find_test_dependencies()

endif()


# ============================================================
# Package
# ============================================================

ament_package()