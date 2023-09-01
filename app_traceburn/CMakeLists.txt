set(TRACE_OUTPUT_FILE freertos_trace)

file(GLOB_RECURSE APP_SOURCES src/*.c)

set(APP_INCLUDES
    src
    src/tile_common
)

set(APP_CONF_INCLUDES
    src/config_app
)

set(RTOS_CONF_INCLUDES
    src/config_rtos
)

set(TRACE_CONF_INCLUDES
    src/config_trace
)

set(APP_COMPILER_FLAGS
    -Os
    -g
    -report
    -fxscope
    -mcmodel=large
    -Wno-xcore-fptrgroup
    ${CMAKE_CURRENT_LIST_DIR}/src/config.xscope
)

set(APP_COMPILE_DEFINITIONS
    configENABLE_DEBUG_PRINTF=1
    PLATFORM_USES_TILE_0=1
    PLATFORM_USES_TILE_1=1
)

set(APP_LINK_OPTIONS
    -report
    ${CMAKE_CURRENT_LIST_DIR}/src/config.xscope
)

set(APP_COMMON_LINK_LIBRARIES
    bsp::xk_voice_l71
    rtos::freertos
    rtos::drivers::trace
    core::general
)

# ************
# Tile Targets
# ************

set(TILES 0 1)
foreach(TILE ${TILES})
    set(TARGET_NAME tile${TILE}_${PROJECT_NAME})
    add_executable(${TARGET_NAME} EXCLUDE_FROM_ALL)
    target_sources(${TARGET_NAME} PUBLIC ${APP_SOURCES})
    target_include_directories(${TARGET_NAME} PUBLIC ${APP_INCLUDES} ${RTOS_CONF_INCLUDES} ${TRACE_CONF_INCLUDES} ${APP_CONF_INCLUDES})
    target_compile_options(${TARGET_NAME} PRIVATE ${APP_COMPILER_FLAGS})
    target_compile_definitions(${TARGET_NAME} PUBLIC ${APP_COMPILE_DEFINITIONS} THIS_XCORE_TILE=${TILE})
    target_link_options(${TARGET_NAME} PRIVATE ${APP_LINK_OPTIONS})
    target_link_libraries(${TARGET_NAME} PUBLIC ${APP_COMMON_LINK_LIBRARIES})
    list(APPEND TARGETS ${TARGET_NAME})
    unset(TARGET_NAME)
endforeach()

# **************
# Merge Binaries
# **************

merge_binaries(app_traceburn ${TARGETS} 1)

# ****************************
# Create run and debug targets
# ****************************

create_run_xscope_to_file_target(app_traceburn ${TRACE_OUTPUT_FILE})
create_run_target(app_traceburn)
create_debug_target(app_traceburn)
create_install_target(app_traceburn)