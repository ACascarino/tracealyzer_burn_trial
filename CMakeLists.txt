cmake_minimum_required(VERSION 3.27.2)

## Disable in-source build.
if("${CMAKE_SOURCE_DIR}" STREQUAL "${CMAKE_BINARY_DIR}")
    message(FATAL_ERROR "In-source build is not allowed! Please specify a build folder.\n\tex:cmake -B build")
endif()

project(app_traceburn)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

enable_language(CXX C ASM)

include(modules/rtos/tools/cmake_utils/xmos_macros.cmake)

add_subdirectory(modules)

if(PROJECT_IS_TOP_LEVEL)
    add_subdirectory(app_traceburn)
endif()