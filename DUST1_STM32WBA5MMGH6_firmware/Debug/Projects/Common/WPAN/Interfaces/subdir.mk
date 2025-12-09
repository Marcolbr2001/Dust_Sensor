################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Projects/Common/WPAN/Interfaces/adv_trace_usart_if.c \
../Projects/Common/WPAN/Interfaces/hw_aes.c \
../Projects/Common/WPAN/Interfaces/hw_otp.c \
../Projects/Common/WPAN/Interfaces/hw_pka.c \
../Projects/Common/WPAN/Interfaces/hw_pka_p256.c \
../Projects/Common/WPAN/Interfaces/hw_rng.c \
../Projects/Common/WPAN/Interfaces/timer_if.c 

OBJS += \
./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.o \
./Projects/Common/WPAN/Interfaces/hw_aes.o \
./Projects/Common/WPAN/Interfaces/hw_otp.o \
./Projects/Common/WPAN/Interfaces/hw_pka.o \
./Projects/Common/WPAN/Interfaces/hw_pka_p256.o \
./Projects/Common/WPAN/Interfaces/hw_rng.o \
./Projects/Common/WPAN/Interfaces/timer_if.o 

C_DEPS += \
./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.d \
./Projects/Common/WPAN/Interfaces/hw_aes.d \
./Projects/Common/WPAN/Interfaces/hw_otp.d \
./Projects/Common/WPAN/Interfaces/hw_pka.d \
./Projects/Common/WPAN/Interfaces/hw_pka_p256.d \
./Projects/Common/WPAN/Interfaces/hw_rng.d \
./Projects/Common/WPAN/Interfaces/timer_if.d 


# Each subdirectory must supply rules for building sources it contributes
Projects/Common/WPAN/Interfaces/%.o Projects/Common/WPAN/Interfaces/%.su Projects/Common/WPAN/Interfaces/%.cyclo: ../Projects/Common/WPAN/Interfaces/%.c Projects/Common/WPAN/Interfaces/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m33 -std=gnu11 -g3 -DDEBUG -DUSE_FULL_LL_DRIVER -DBLE -DUSE_HAL_DRIVER -DSTM32WBA5Mxx -c -I../Core/Inc -I../System/Interfaces -I../System/Modules -I../System/Config/Log -I../System/Config/LowPower -I../System/Config/Debug_GPIO -I../System/Config/Flash -I../System/Config/ADC_Ctrl -I../System/Config/CRC_Ctrl -I../STM32_WPAN/App -I../STM32_WPAN/Target -I../Drivers/STM32WBAxx_HAL_Driver/Inc -I../Drivers/STM32WBAxx_HAL_Driver/Inc/Legacy -I../Utilities/trace/adv_trace -I../Projects/Common/WPAN/Interfaces -I../Projects/Common/WPAN/Modules -I../Projects/Common/WPAN/Modules/BasicAES -I../Projects/Common/WPAN/Modules/Flash -I../Projects/Common/WPAN/Modules/MemoryManager -I../Projects/Common/WPAN/Modules/RTDebug -I../Projects/Common/WPAN/Modules/SerialCmdInterpreter -I../Projects/Common/WPAN/Modules/Log -I../Utilities/misc -I../Utilities/sequencer -I../Utilities/tim_serv -I../Utilities/lpm/tiny_lpm -I../Middlewares/ST/STM32_WPAN -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/config/ble_basic -I../Middlewares/ST/STM32_WPAN/ble/svc/Src -I../Drivers/CMSIS/Device/ST/STM32WBAxx/Include -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc/_40nm_reg_files -I../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/inc/ot_inc -I../Middlewares/ST/STM32_WPAN/link_layer/ll_sys/inc -I../Middlewares/ST/STM32_WPAN/ble/stack/include -I../Middlewares/ST/STM32_WPAN/ble/stack/include/auto -I../Middlewares/ST/STM32_WPAN/ble/svc/Inc -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Projects-2f-Common-2f-WPAN-2f-Interfaces

clean-Projects-2f-Common-2f-WPAN-2f-Interfaces:
	-$(RM) ./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.cyclo ./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.d ./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.o ./Projects/Common/WPAN/Interfaces/adv_trace_usart_if.su ./Projects/Common/WPAN/Interfaces/hw_aes.cyclo ./Projects/Common/WPAN/Interfaces/hw_aes.d ./Projects/Common/WPAN/Interfaces/hw_aes.o ./Projects/Common/WPAN/Interfaces/hw_aes.su ./Projects/Common/WPAN/Interfaces/hw_otp.cyclo ./Projects/Common/WPAN/Interfaces/hw_otp.d ./Projects/Common/WPAN/Interfaces/hw_otp.o ./Projects/Common/WPAN/Interfaces/hw_otp.su ./Projects/Common/WPAN/Interfaces/hw_pka.cyclo ./Projects/Common/WPAN/Interfaces/hw_pka.d ./Projects/Common/WPAN/Interfaces/hw_pka.o ./Projects/Common/WPAN/Interfaces/hw_pka.su ./Projects/Common/WPAN/Interfaces/hw_pka_p256.cyclo ./Projects/Common/WPAN/Interfaces/hw_pka_p256.d ./Projects/Common/WPAN/Interfaces/hw_pka_p256.o ./Projects/Common/WPAN/Interfaces/hw_pka_p256.su ./Projects/Common/WPAN/Interfaces/hw_rng.cyclo ./Projects/Common/WPAN/Interfaces/hw_rng.d ./Projects/Common/WPAN/Interfaces/hw_rng.o ./Projects/Common/WPAN/Interfaces/hw_rng.su ./Projects/Common/WPAN/Interfaces/timer_if.cyclo ./Projects/Common/WPAN/Interfaces/timer_if.d ./Projects/Common/WPAN/Interfaces/timer_if.o ./Projects/Common/WPAN/Interfaces/timer_if.su

.PHONY: clean-Projects-2f-Common-2f-WPAN-2f-Interfaces

