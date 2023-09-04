#define DEBUG_UNIT MAIN_TILE1
#ifndef DEBUG_PRINT_ENABLE_MAIN_TILE1
#define DEBUG_PRINT_ENABLE_MAIN_TILE1 1
#endif
#include "debug_print.h"
#include "rtos_printf.h"

#include "platform.h"
#include <xs1.h>
#include <xcore/chanend.h>
#include <xcore/parallel.h>

#include "FreeRTOS.h"
#include "tile_common.h"
#include "platform/platform_init.h"

#if ON_TILE(1)

static void rtos_app(void *args)
{
    debug_printf("RTOS starting on tile[%d]\n", THIS_XCORE_TILE);
    // platform_start();
    vTaskDelete(NULL);
}

void main_tile1(chanend_t c0, chanend_t c1, chanend_t c2, chanend_t c3)
{
    tile_common_start_rtos_app(c0, rtos_app, RTOS_THREAD_STACK_SIZE(rtos_app), NULL);
}
#endif