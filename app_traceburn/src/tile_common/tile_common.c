#define DEBUG_UNIT TILE_COMMON
#ifndef DEBUG_PRINT_ENABLE_TILE_COMMON
#define DEBUG_PRINT_ENABLE_TILE_COMMON 1
#endif
#include "debug_print.h"
#include "rtos_printf.h"

#include "app_conf.h"

#include "tile_common.h"
#include "platform/platform_init.h"

#include <xcore/chanend.h>
#include <xcore/hwtimer.h>

#include "FreeRTOS.h"
#include "task.h"

void vApplicationMinimalIdleHook(void)
{
    rtos_printf("Idle hook on tile %d core %d\n", THIS_XCORE_TILE, rtos_core_id_get());

    asm volatile("waiteu");
}

void vApplicationMallocFailedHook(void)
{
    rtos_printf("Malloc Failed on tile %d!\n", THIS_XCORE_TILE);
    xassert(0);
    for (;;)
        ;
}

void tile_common_start_rtos_app(chanend_t c, TaskFunction_t task_function, UBaseType_t task_stack, void *servicer_args)
{
    debug_printf("Starting scheduler tile %d\n", THIS_XCORE_TILE);
    // platform_init(c);
    chanend_free(c);

    xTaskCreate(
        task_function,
        "rtos start",
        task_stack,
        servicer_args,
        appconfSTARTUP_TASK_PRIORITY,
        NULL);
    vTaskStartScheduler();
}

void burn(void *args)
{
    burn_task_data_t *params = (burn_task_data_t *)args;
    while (1)
    {
        // rtos_printf("Burn %dms restart\n", params->timeout / 100000);
        uint32_t t_start = get_reference_time();
        uint32_t t_now = t_start;

        do
        {
            t_now = get_reference_time();
        } while ((t_now - t_start) < params->timeout);

        ulTaskNotifyTake(pdTRUE, params->wait);
        if (params->target != NULL)
        {
            xTaskNotifyGive(params->target);
        }
    }
}