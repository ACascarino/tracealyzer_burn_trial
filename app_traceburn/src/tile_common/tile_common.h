#include <xcore/chanend.h>
#include <xcore/parallel.h>

#include "FreeRTOS.h"
#include "task.h"

typedef struct
{
    uint32_t timeout;
    TaskHandle_t target;
    uint32_t wait;
} burn_task_data_t;

void vApplicationMinimalIdleHook(void);
void vApplicationMallocFailedHook(void);

void tile_common_start_rtos_app(chanend_t c, TaskFunction_t task_function, UBaseType_t task_stack, void *servicer_args);
void burn(void *args);