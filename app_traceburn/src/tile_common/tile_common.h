#include <xcore/chanend.h>

#include "FreeRTOS.h"
#include "task.h"

void vApplicationMinimalIdleHook(void);
void vApplicationMallocFailedHook(void);
void tile_common_start_rtos_app(chanend_t c, TaskFunction_t task_function, UBaseType_t task_stack, void* servicer_args);