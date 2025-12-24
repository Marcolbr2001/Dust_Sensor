/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32wbaxx_hal.h"
#include "app_conf.h"
#include "app_entry.h"
#include "app_common.h"
#include "app_debug.h"

#include "stm32wbaxx_ll_icache.h"
#include "stm32wbaxx_ll_tim.h"
#include "stm32wbaxx_ll_bus.h"
#include "stm32wbaxx_ll_cortex.h"
#include "stm32wbaxx_ll_rcc.h"
#include "stm32wbaxx_ll_system.h"
#include "stm32wbaxx_ll_utils.h"
#include "stm32wbaxx_ll_pwr.h"
#include "stm32wbaxx_ll_gpio.h"
#include "stm32wbaxx_ll_dma.h"

#include "stm32wbaxx_ll_exti.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);
void MX_GPIO_Init(void);
void MX_GPDMA1_Init(void);
void MX_RAMCFG_Init(void);
void MX_RTC_Init(void);
void MX_USART1_UART_Init(void);
void MX_ADC4_Init(void);
void MX_CRC_Init(void);
void MX_RNG_Init(void);
void MX_ICACHE_Init(void);
void MX_TIM16_Init(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LED1_Pin GPIO_PIN_10
#define LED1_GPIO_Port GPIOA
#define LED2_Pin GPIO_PIN_9
#define LED2_GPIO_Port GPIOA
#define LED3_Pin GPIO_PIN_14
#define LED3_GPIO_Port GPIOB
#define DT_CS_Pin GPIO_PIN_13
#define DT_CS_GPIO_Port GPIOB
#define SD_CS_Pin GPIO_PIN_11
#define SD_CS_GPIO_Port GPIOB
#define S0_Pin GPIO_PIN_7
#define S0_GPIO_Port GPIOA
#define S1_Pin GPIO_PIN_6
#define S1_GPIO_Port GPIOA
#define S2_Pin GPIO_PIN_4
#define S2_GPIO_Port GPIOA
#define S3_Pin GPIO_PIN_3
#define S3_GPIO_Port GPIOA
#define S4_Pin GPIO_PIN_1
#define S4_GPIO_Port GPIOA
#define SEL_Pin GPIO_PIN_5
#define SEL_GPIO_Port GPIOA
#define MUX_STATUS_Pin GPIO_PIN_13
#define MUX_STATUS_GPIO_Port GPIOC
#define DCC_Counter_Pin GPIO_PIN_6
#define DCC_Counter_GPIO_Port GPIOB
#define RES_DCC_Pin GPIO_PIN_7
#define RES_DCC_GPIO_Port GPIOB
#define DCC_Sel_Pin GPIO_PIN_5
#define DCC_Sel_GPIO_Port GPIOB
#define OUT_D_Pin GPIO_PIN_15
#define OUT_D_GPIO_Port GPIOA
#define OUT_P_Pin GPIO_PIN_4
#define OUT_P_GPIO_Port GPIOB
#define OUT_N_Pin GPIO_PIN_12
#define OUT_N_GPIO_Port GPIOA
#define RES_ch_read_Pin GPIO_PIN_11
#define RES_ch_read_GPIO_Port GPIOA
#define Hfb1_Pin GPIO_PIN_2
#define Hfb1_GPIO_Port GPIOB
#define Hfb2_Pin GPIO_PIN_1
#define Hfb2_GPIO_Port GPIOB
#define Enable_Sensor_Pin GPIO_PIN_0
#define Enable_Sensor_GPIO_Port GPIOB
#define SD_DETECT_Pin GPIO_PIN_15
#define SD_DETECT_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
