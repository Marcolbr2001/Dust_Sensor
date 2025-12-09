/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    BLE_Sensor_app.c
  * @author  MCD Application Team
  * @brief   BLE_Sensor_app application definition.
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

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "app_common.h"
#include "log_module.h"
#include "app_ble.h"
#include "ll_sys_if.h"
#include "dbg_trace.h"
#include "ble_sensor_app.h"
#include "ble_sensor.h"
#include "stm32_rtos.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <string.h>
#include "stm32_timer.h"

#include "DUST_functions.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

typedef enum
{
  Mydata_NOTIFICATION_OFF,
  Mydata_NOTIFICATION_ON,
  Recdata_NOTIFICATION_OFF,
  Recdata_NOTIFICATION_ON,
  /* USER CODE BEGIN Service1_APP_SendInformation_t */

  /* USER CODE END Service1_APP_SendInformation_t */
  BLE_SENSOR_APP_SENDINFORMATION_LAST
} BLE_SENSOR_APP_SendInformation_t;

typedef struct
{
  BLE_SENSOR_APP_SendInformation_t     Mydata_Notification_Status;
  BLE_SENSOR_APP_SendInformation_t     Recdata_Notification_Status;
  /* USER CODE BEGIN Service1_APP_Context_t */
  //UTIL_TIMER_Object_t MYDATA_Timer_Id;
  /* USER CODE END Service1_APP_Context_t */
  uint16_t              ConnectionHandle;
} BLE_SENSOR_APP_Context_t;

/* Private defines -----------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* External variables --------------------------------------------------------*/
/* USER CODE BEGIN EV */

/* USER CODE END EV */

/* Private macros ------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
static BLE_SENSOR_APP_Context_t BLE_SENSOR_APP_Context;

uint8_t a_BLE_SENSOR_UpdateCharData[247];

/* USER CODE BEGIN PV */
static void MYDATA_SendTest(void);
static UTIL_TIMER_Object_t MYDATA_Timer_Id;
static uint32_t mydata_counter = 0;
//extern TIM_HandleTypeDef htim3;
//uint16_t pwm_buf[] = {13000, 13000, 0, 0, 0, 0, 0, 0, 0, 0}; //to use in case of PWM DMA
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
static void BLE_SENSOR_Mydata_SendNotification(void);
static void BLE_SENSOR_Recdata_SendNotification(void);

/* USER CODE BEGIN PFP */
static void MYDATA_TimerCb(void *arg);
static void MYDATA_Update(void);

//static void DATA_RECEIVED(const uint8_t *data_received);
//static void LED_BLINKING(const uint32_t LED_COLOR, uint16_t *pwm_buf);
/* USER CODE END PFP */

/* Functions Definition ------------------------------------------------------*/
void BLE_SENSOR_Notification(BLE_SENSOR_NotificationEvt_t *p_Notification)
{
  /* USER CODE BEGIN Service1_Notification_1 */

  /* USER CODE END Service1_Notification_1 */
  switch(p_Notification->EvtOpcode)
  {
    /* USER CODE BEGIN Service1_Notification_Service1_EvtOpcode */

    /* USER CODE END Service1_Notification_Service1_EvtOpcode */

    case BLE_SENSOR_MYDATA_READ_EVT:
      /* USER CODE BEGIN Service1Char1_READ_EVT */

      /* USER CODE END Service1Char1_READ_EVT */
      break;

    case BLE_SENSOR_MYDATA_NOTIFY_ENABLED_EVT:
      /* USER CODE BEGIN Service1Char1_NOTIFY_ENABLED_EVT */
		mydata_counter = 0; // reset contatore, se vuoi
		UTIL_TIMER_Stop(&MYDATA_Timer_Id);
		//UTIL_TIMER_StartWithPeriod(&MYDATA_Timer_Id, 100);   // 1 s
		// invia subito il primo valore
		//MYDATA_Update();
      /* USER CODE END Service1Char1_NOTIFY_ENABLED_EVT */
      break;

    case BLE_SENSOR_MYDATA_NOTIFY_DISABLED_EVT:
      /* USER CODE BEGIN Service1Char1_NOTIFY_DISABLED_EVT */
  	  UTIL_TIMER_Stop(&MYDATA_Timer_Id);
      /* USER CODE END Service1Char1_NOTIFY_DISABLED_EVT */
      break;

    case BLE_SENSOR_RECDATA_READ_EVT:
      /* USER CODE BEGIN Service1Char2_READ_EVT */

      /* USER CODE END Service1Char2_READ_EVT */
      break;

    case BLE_SENSOR_RECDATA_WRITE_NO_RESP_EVT:
      /* USER CODE BEGIN Service1Char2_WRITE_NO_RESP_EVT */
		const uint8_t *buf = p_Notification->DataTransfered.p_Payload;
		uint16_t len       = p_Notification->DataTransfered.Length;

		if (len >= 1) {
		  DATA_RECEIVED(buf, len);
		}
      /* USER CODE END Service1Char2_WRITE_NO_RESP_EVT */
      break;

    case BLE_SENSOR_RECDATA_WRITE_EVT:
      /* USER CODE BEGIN Service1Char2_WRITE_EVT */

      /* USER CODE END Service1Char2_WRITE_EVT */
      break;

    case BLE_SENSOR_RECDATA_NOTIFY_ENABLED_EVT:
      /* USER CODE BEGIN Service1Char2_NOTIFY_ENABLED_EVT */

      /* USER CODE END Service1Char2_NOTIFY_ENABLED_EVT */
      break;

    case BLE_SENSOR_RECDATA_NOTIFY_DISABLED_EVT:
      /* USER CODE BEGIN Service1Char2_NOTIFY_DISABLED_EVT */

      /* USER CODE END Service1Char2_NOTIFY_DISABLED_EVT */
      break;

    default:
      /* USER CODE BEGIN Service1_Notification_default */

      /* USER CODE END Service1_Notification_default */
      break;
  }
  /* USER CODE BEGIN Service1_Notification_2 */

  /* USER CODE END Service1_Notification_2 */
  return;
}

void BLE_SENSOR_APP_EvtRx(BLE_SENSOR_APP_ConnHandleNotEvt_t *p_Notification)
{
  /* USER CODE BEGIN Service1_APP_EvtRx_1 */

  /* USER CODE END Service1_APP_EvtRx_1 */

  switch(p_Notification->EvtOpcode)
  {
    /* USER CODE BEGIN Service1_APP_EvtRx_Service1_EvtOpcode */

    /* USER CODE END Service1_APP_EvtRx_Service1_EvtOpcode */
    case BLE_SENSOR_CONN_HANDLE_EVT :
      /* USER CODE BEGIN Service1_APP_CONN_HANDLE_EVT */

      /* USER CODE END Service1_APP_CONN_HANDLE_EVT */
      break;

    case BLE_SENSOR_DISCON_HANDLE_EVT :
      /* USER CODE BEGIN Service1_APP_DISCON_HANDLE_EVT */

      /* USER CODE END Service1_APP_DISCON_HANDLE_EVT */
      break;

    default:
      /* USER CODE BEGIN Service1_APP_EvtRx_default */

      /* USER CODE END Service1_APP_EvtRx_default */
      break;
  }

  /* USER CODE BEGIN Service1_APP_EvtRx_2 */

  /* USER CODE END Service1_APP_EvtRx_2 */

  return;
}

void BLE_SENSOR_APP_Init(void)
{
  UNUSED(BLE_SENSOR_APP_Context);
  BLE_SENSOR_Init();

  /* USER CODE BEGIN Service1_APP_Init */
  // timer periodico da 1000 ms
  UTIL_TIMER_Create(&MYDATA_Timer_Id, 1000, UTIL_TIMER_PERIODIC, &MYDATA_TimerCb, 0);

  // registra la task che invia il pacchetto
  UTIL_SEQ_RegTask(1U << CFG_TASK_MYDATA_UPDATE_ID, UTIL_SEQ_RFU, MYDATA_Update);
  /* USER CODE END Service1_APP_Init */
  return;
}

/* USER CODE BEGIN FD */

/* USER CODE END FD */

/*************************************************************
 *
 * LOCAL FUNCTIONS
 *
 *************************************************************/
__USED void BLE_SENSOR_Mydata_SendNotification(void) /* Property Notification */
{
  BLE_SENSOR_APP_SendInformation_t notification_on_off = Mydata_NOTIFICATION_OFF;
  BLE_SENSOR_Data_t ble_sensor_notification_data;

  ble_sensor_notification_data.p_Payload = (uint8_t*)a_BLE_SENSOR_UpdateCharData;
  ble_sensor_notification_data.Length = 0;

  /* USER CODE BEGIN Service1Char1_NS_1 */

  /* USER CODE END Service1Char1_NS_1 */

  if (notification_on_off != Mydata_NOTIFICATION_OFF)
  {
    BLE_SENSOR_UpdateValue(BLE_SENSOR_MYDATA, &ble_sensor_notification_data);
  }

  /* USER CODE BEGIN Service1Char1_NS_Last */

  /* USER CODE END Service1Char1_NS_Last */

  return;
}

__USED void BLE_SENSOR_Recdata_SendNotification(void) /* Property Notification */
{
  BLE_SENSOR_APP_SendInformation_t notification_on_off = Recdata_NOTIFICATION_OFF;
  BLE_SENSOR_Data_t ble_sensor_notification_data;

  ble_sensor_notification_data.p_Payload = (uint8_t*)a_BLE_SENSOR_UpdateCharData;
  ble_sensor_notification_data.Length = 0;

  /* USER CODE BEGIN Service1Char2_NS_1 */

  /* USER CODE END Service1Char2_NS_1 */

  if (notification_on_off != Recdata_NOTIFICATION_OFF)
  {
    BLE_SENSOR_UpdateValue(BLE_SENSOR_RECDATA, &ble_sensor_notification_data);
  }

  /* USER CODE BEGIN Service1Char2_NS_Last */

  /* USER CODE END Service1Char2_NS_Last */

  return;
}

/* USER CODE BEGIN FD_LOCAL_FUNCTIONS */


static void MYDATA_TimerCb(void *arg)
{
  // esegui in background (evita di chiamare ACI nel contesto del timer)
  UTIL_SEQ_SetTask(1U << CFG_TASK_MYDATA_UPDATE_ID, CFG_SEQ_PRIO_0);
}

static void MYDATA_Update(void)
{
  BLE_SENSOR_Data_t pkt;
  pkt.p_Payload = (uint8_t*)a_BLE_SENSOR_UpdateCharData;

  if(!g_ble_dust_stream_enabled)
  {
	  return;
  }

  // DUST frame nel buffer BLE
  uint16_t len = DUST_BuildFrame(pkt.p_Payload, sizeof(a_BLE_SENSOR_UpdateCharData));
  if (len == 0u)
  {
      // buffer troppo piccolo: non invio niente
      return;
  }

  // BLE_SENSOR_Data_t.Length è uint8_t, ma il frame è ~136 byte, quindi ok (<255)
  pkt.Length = (uint8_t)len;

  // Invia notifica sulla caratteristica MYDATA
  BLE_SENSOR_UpdateValue(BLE_SENSOR_MYDATA, &pkt);



  // --- formato A: ASCII, esattamente come vedi "31 31 ..." su LightBlue ---
//  mydata_counter++;
//  int n = snprintf((char*)pkt.p_Payload, 16, "%08lu", (unsigned long)mydata_counter);
//  if (n < 0) n = 0;
//  if (n > 16) n = 16;               // <= Value length impostata nell'IOC
//  pkt.Length = (uint8_t)n;

  // se preferisci 4 byte binari little-endian:
  // uint32_t c = ++mydata_counter;
  // memcpy(pkt.p_Payload, &c, 4);
  // pkt.Length = 4;

//  BLE_SENSOR_UpdateValue(BLE_SENSOR_MYDATA, &pkt);
}


static void MYDATA_SendTest(void)
{
  BLE_SENSOR_Data_t pkt;
  pkt.p_Payload = (uint8_t*)a_BLE_SENSOR_UpdateCharData;

  // Esempio A: 16 byte ASCII '1'
  pkt.Length = 16;                          // <= Value length impostata nell’IOC
  memset(pkt.p_Payload, '1', pkt.Length);   // 0x31 ripetuto

  // Esempio B (alternativo): 0x11 ripetuto
  // pkt.Length = 16;
  // memset(pkt.p_Payload, 0x11, pkt.Length);

  // Sostituisci BLE_SENSOR_MYDATA_C con il simbolo reale della tua char
  BLE_SENSOR_UpdateValue(BLE_SENSOR_MYDATA, &pkt);
}
/* USER CODE END FD_LOCAL_FUNCTIONS */
