################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.c 

OBJS += \
./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.o 

C_DEPS += \
./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.d 


# Each subdirectory must supply rules for building sources it contributes
Projects/Common/WPAN/Modules/SerialCmdInterpreter/%.o Projects/Common/WPAN/Modules/SerialCmdInterpreter/%.su Projects/Common/WPAN/Modules/SerialCmdInterpreter/%.cyclo: ../Projects/Common/WPAN/Modules/SerialCmdInterpreter/%.c Projects/Common/WPAN/Modules/SerialCmdInterpreter/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m33 -std=gnu11 -g3 -DDEBUG -DUSE_FULL_LL_DRIVER -DBLE -DUSE_HAL_DRIVER -DSTM32WBA5Mxx -c -I../Core/Inc -I../System/Interfaces -I../System/Modules -I../System/Config/Log -I../System/Config/LowPower -I../System/Config/Debug_GPIO -I../System/Config/Flash -I../System/Config/ADC_Ctrl -I../System/Config/CRC_Ctrl -I../STM32_WPAN/App -I../STM32_WPAN/Target -I../Drivers/STM32WBAxx_HAL_Driver/Inc -I../Drivers/STM32WBAxx_HAL_Driver/Inc/Legacy -I../Utilities/trace/adv_trace -I../Projects/Common/WPAN/Interfaces -I../Projects/Common/WPAN/Modules -I../Projects/Common/WPAN/Modules/BasicAES -I../Projects/Common/WPAN/Modules/Flash -I../Projects/Common/WPAN/Modules/MemoryManager -I../Projects/Common/WPAN/Modules/RTDebug -I../Projects/Common/WPAN/Modules/SerialCmdInterpreter -I../Projects/Common/WPAN/Modules/Log -I../Utilities/misc -I../Utilities/sequencer -I../Utilities/tim_serv -I../Utilities/lpm/tiny_lpm -I../Middlewares/ST/STM32_WPAN -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/config/ble_basic -I../Middlewares/ST/STM32_WPAN/ble/svc/Src -I../Drivers/CMSIS/Device/ST/STM32WBAxx/Include -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc/_40nm_reg_files -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc/ot_inc -I../Middlewares/ST/STM32_WPAN/link_layer/ll_sys/inc -I../Middlewares/ST/STM32_WPAN/ble/stack/include -I../Middlewares/ST/STM32_WPAN/ble/stack/include/auto -I../Middlewares/ST/STM32_WPAN/ble/svc/Inc -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Projects-2f-Common-2f-WPAN-2f-Modules-2f-SerialCmdInterpreter

clean-Projects-2f-Common-2f-WPAN-2f-Modules-2f-SerialCmdInterpreter:
	-$(RM) ./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.cyclo ./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.d ./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.o ./Projects/Common/WPAN/Modules/SerialCmdInterpreter/serial_cmd_interpreter.su

.PHONY: clean-Projects-2f-Common-2f-WPAN-2f-Modules-2f-SerialCmdInterpreter

