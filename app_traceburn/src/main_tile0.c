#define DEBUG_UNIT MAIN_TILE0
#ifndef DEBUG_PRINT_ENABLE_MAIN_TILE0
#define DEBUG_PRINT_ENABLE_MAIN_TILE0 1
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

#include "rtos_osal.h"

#if ON_TILE(0)

burn_task_data_t burn_a = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

burn_task_data_t burn_b = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

burn_task_data_t burn_c = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

burn_task_data_t burn_d = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

#if configNUM_CORES > 5

burn_task_data_t burn_e = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

#if configNUM_CORES > 6

burn_task_data_t burn_f = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

#if configNUM_CORES > 7

burn_task_data_t burn_g = {.timeout = 990000, 
                            .target = NULL, 
                            .wait = RTOS_OSAL_WAIT_FOREVER};

#endif
#endif
#endif

burn_task_data_t burn_h = {.timeout = 1000000, 
                            .target = NULL, 
                            .wait = 5};

static void rtos_app(void *args)
{
    debug_printf("RTOS starting on tile[%d]\n", THIS_XCORE_TILE);

    xTaskCreate(burn,
                "burn_a",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_a,
                configMAX_PRIORITIES / 2,
                &burn_h.target);

    xTaskCreate(burn,
                "burn_b",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_b,
                configMAX_PRIORITIES / 2,
                &burn_a.target);

    xTaskCreate(burn,
                "burn_c",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_c,
                configMAX_PRIORITIES / 2,
                &burn_b.target);

    xTaskCreate(burn,
                "burn_d",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_d,
                configMAX_PRIORITIES / 2,
                &burn_c.target);

#if configNUM_CORES > 5

    xTaskCreate(burn,
                "burn_e",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_e,
                configMAX_PRIORITIES / 2,
                &burn_d.target);

#if configNUM_CORES > 6

    xTaskCreate(burn,
                "burn_f",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_f,
                configMAX_PRIORITIES / 2,
                &burn_e.target);

#if configNUM_CORES > 7

    xTaskCreate(burn,
                "burn_g",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_g,
                configMAX_PRIORITIES / 2,
                &burn_f.target);

#endif
#endif
#endif

    xTaskCreate(burn,
                "burn_h",
                RTOS_THREAD_STACK_SIZE(burn),
                &burn_h,
                configMAX_PRIORITIES / 2,
                NULL);

    vTaskDelete(NULL);
}

void main_tile0(chanend_t c0, chanend_t c1, chanend_t c2, chanend_t c3)
{
#if (USE_TRACE_MODE == TRACE_MODE_TRACEALYZER_STREAMING)
    xTraceInitialize();
    xTraceEnable(TRC_START);
#endif
    tile_common_start_rtos_app(c1, rtos_app, RTOS_THREAD_STACK_SIZE(rtos_app), NULL);
}
#endif