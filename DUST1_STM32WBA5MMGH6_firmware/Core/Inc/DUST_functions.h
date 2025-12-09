
#ifndef DUST_H
#define DUST_H

#include "main.h"
#include "app_common.h"
#include "log_module.h"
#include "app_ble.h"
#include "ll_sys_if.h"
#include "dbg_trace.h"
#include "ble_sensor_app.h"
#include "ble_sensor.h"
#include "stm32_rtos.h"
#include "stm32wbaxx_hal.h"

#include "stm32wbaxx_hal_lptim.h"

#include <string.h>
#include "stm32_timer.h"



#define DUST_CHANNELS           32u
#define DUST_MAVG_WINDOW        10u    // finestra moving average
#define DUST_THRESH_OFFSET      50u    // offset sopra baseline (da tarare)
#define DUST_BASE_SHIFT         8u     // baseline IIR shift (~1/256)
#define DUST_MIN_OVER_SAMPLES   2u     // campioni consecutivi sopra soglia alta
#define DUST_MIN_UNDER_SAMPLES  2u     // campioni consecutivi sotto soglia bassa
#define DUST_EVENT_SAMPLES      5u     // quanti sample salvare per evento


extern TIM_HandleTypeDef htim3;
extern LPTIM_HandleTypeDef hlptim1;
extern SPI_HandleTypeDef hspi3;

extern volatile uint8_t g_ble_dust_stream_enabled;
extern volatile uint8_t g_usb_dust_stream_enabled;

//extern uint16_t pwm_buf[] = {13000, 13000, 0, 0, 0, 0, 0, 0, 0, 0}; //to use in case of PWM DMA

void DATA_RECEIVED(const uint8_t *data_received, uint16_t len);
static inline void CHANNEL_SET(uint8_t channel);
static inline void CHANNEL_SET_Init(void);
void LED_BLINKING(const uint32_t LED_COLOR, uint16_t *pwm_buf);
void GET_ADC_VALUES();
void GET_ADC_VALUES_continous();

typedef struct
{
    uint8_t  channel;                     
    uint32_t timestamp_ms;                
    uint16_t samples[DUST_EVENT_SAMPLES]; 
    uint8_t  len;                         // valid samples
} DustEvent_t;

typedef void (*DustEventCallback_t)(const DustEvent_t *ev);

void DUST_Init(void);
void DUST_SetCallback(DustEventCallback_t cb);
void DUST_SetCurrentChannel(uint8_t ch);
void DUST_OnAdcSample(uint8_t channel, uint16_t raw_sample, uint32_t timestamp_ms);
uint16_t DUST_BuildFrame(uint8_t *dst, uint16_t max_len);
void DUST_SendFrame_UART(void);


#endif // DUST_H
