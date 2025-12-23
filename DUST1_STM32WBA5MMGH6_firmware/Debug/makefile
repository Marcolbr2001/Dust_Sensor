################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include Utilities/trace/adv_trace/subdir.mk
-include Utilities/tim_serv/subdir.mk
-include Utilities/sequencer/subdir.mk
-include Utilities/misc/subdir.mk
-include Utilities/lpm/tiny_lpm/subdir.mk
-include System/Modules/subdir.mk
-include System/Interfaces/subdir.mk
-include System/Config/LowPower/subdir.mk
-include System/Config/Flash/subdir.mk
-include System/Config/Debug_GPIO/subdir.mk
-include System/Config/CRC_Ctrl/subdir.mk
-include System/Config/ADC_Ctrl/subdir.mk
-include STM32_WPAN/Target/subdir.mk
-include STM32_WPAN/App/subdir.mk
-include Projects/Common/WPAN/Startup/subdir.mk
-include Projects/Common/WPAN/Modules/SerialCmdInterpreter/subdir.mk
-include Projects/Common/WPAN/Modules/RTDebug/subdir.mk
-include Projects/Common/WPAN/Modules/MemoryManager/subdir.mk
-include Projects/Common/WPAN/Modules/Log/subdir.mk
-include Projects/Common/WPAN/Modules/Flash/subdir.mk
-include Projects/Common/WPAN/Modules/BasicAES/subdir.mk
-include Projects/Common/WPAN/Modules/subdir.mk
-include Projects/Common/WPAN/Interfaces/subdir.mk
-include Middlewares/ST/STM32_WPAN/link_layer/ll_sys/src/subdir.mk
-include Middlewares/ST/STM32_WPAN/ble/svc/Src/subdir.mk
-include Drivers/STM32WBAxx_HAL_Driver/Src/subdir.mk
-include Core/Startup/subdir.mk
-include Core/Src/subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(S_DEPS)),)
-include $(S_DEPS)
endif
ifneq ($(strip $(S_UPPER_DEPS)),)
-include $(S_UPPER_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

OPTIONAL_TOOL_DEPS := \
$(wildcard ../makefile.defs) \
$(wildcard ../makefile.init) \
$(wildcard ../makefile.targets) \


BUILD_ARTIFACT_NAME := DUST1_STM32WBA5MMGH6_firmware
BUILD_ARTIFACT_EXTENSION := elf
BUILD_ARTIFACT_PREFIX :=
BUILD_ARTIFACT := $(BUILD_ARTIFACT_PREFIX)$(BUILD_ARTIFACT_NAME)$(if $(BUILD_ARTIFACT_EXTENSION),.$(BUILD_ARTIFACT_EXTENSION),)

# Add inputs and outputs from these tool invocations to the build variables 
EXECUTABLES += \
DUST1_STM32WBA5MMGH6_firmware.elf \

MAP_FILES += \
DUST1_STM32WBA5MMGH6_firmware.map \

SIZE_OUTPUT += \
default.size.stdout \

OBJDUMP_LIST += \
DUST1_STM32WBA5MMGH6_firmware.list \

OBJCOPY_HEX += \
DUST1_STM32WBA5MMGH6_firmware.hex \

OBJCOPY_BIN += \
DUST1_STM32WBA5MMGH6_firmware.bin \


# All Target
all: main-build

# Main-build Target
main-build: DUST1_STM32WBA5MMGH6_firmware.elf secondary-outputs

# Tool invocations
DUST1_STM32WBA5MMGH6_firmware.elf DUST1_STM32WBA5MMGH6_firmware.map: $(OBJS) $(USER_OBJS) C:\Users\marco\STM32CubeIDE\workspace_1.19.0\DUST1_STM32WBA5MMGH6_firmware\STM32WBA5MMGHX_FLASH.ld makefile objects.list $(OPTIONAL_TOOL_DEPS)
	arm-none-eabi-gcc -o "DUST1_STM32WBA5MMGH6_firmware.elf" @"objects.list" $(USER_OBJS) -Wl,--start-group $(LIBS) -Wl,--end-group -mcpu=cortex-m33 -T"C:\Users\marco\STM32CubeIDE\workspace_1.19.0\DUST1_STM32WBA5MMGH6_firmware\STM32WBA5MMGHX_FLASH.ld" --specs=nosys.specs -Wl,-Map="DUST1_STM32WBA5MMGH6_firmware.map" -Wl,--gc-sections -static -L../Middlewares/ST/STM32_WPAN/link_layer/ll_cmd_lib/lib -L../Middlewares/ST/STM32_WPAN/ble/stack/lib --specs=nano.specs -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -Wl,--start-group -lc -lm -Wl,--end-group
	@echo 'Finished building target: $@'
	@echo ' '

default.size.stdout: $(EXECUTABLES) makefile objects.list $(OPTIONAL_TOOL_DEPS)
	arm-none-eabi-size  $(EXECUTABLES)
	@echo 'Finished building: $@'
	@echo ' '

DUST1_STM32WBA5MMGH6_firmware.list: $(EXECUTABLES) makefile objects.list $(OPTIONAL_TOOL_DEPS)
	arm-none-eabi-objdump -h -S $(EXECUTABLES) > "DUST1_STM32WBA5MMGH6_firmware.list"
	@echo 'Finished building: $@'
	@echo ' '

DUST1_STM32WBA5MMGH6_firmware.hex: $(EXECUTABLES) makefile objects.list $(OPTIONAL_TOOL_DEPS)
	arm-none-eabi-objcopy  -O ihex $(EXECUTABLES) "DUST1_STM32WBA5MMGH6_firmware.hex"
	@echo 'Finished building: $@'
	@echo ' '

DUST1_STM32WBA5MMGH6_firmware.bin: $(EXECUTABLES) makefile objects.list $(OPTIONAL_TOOL_DEPS)
	arm-none-eabi-objcopy  -O binary $(EXECUTABLES) "DUST1_STM32WBA5MMGH6_firmware.bin"
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) DUST1_STM32WBA5MMGH6_firmware.bin DUST1_STM32WBA5MMGH6_firmware.elf DUST1_STM32WBA5MMGH6_firmware.hex DUST1_STM32WBA5MMGH6_firmware.list DUST1_STM32WBA5MMGH6_firmware.map default.size.stdout
	-@echo ' '

secondary-outputs: $(SIZE_OUTPUT) $(OBJDUMP_LIST) $(OBJCOPY_HEX) $(OBJCOPY_BIN)

fail-specified-linker-script-missing:
	@echo 'Error: Cannot find the specified linker script. Check the linker settings in the build configuration.'
	@exit 2

warn-no-linker-script-specified:
	@echo 'Warning: No linker script specified. Check the linker settings in the build configuration.'

.PHONY: all clean dependents main-build fail-specified-linker-script-missing warn-no-linker-script-specified

-include ../makefile.targets
