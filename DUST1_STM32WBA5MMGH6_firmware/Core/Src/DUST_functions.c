#include "main.h"
#include "app_common.h"
#include "log_module.h"
#include "app_ble.h"
#include "ll_sys_if.h"
#include "dbg_trace.h"
#include "ble_sensor_app.h"
#include "ble_sensor.h"
#include "stm32_rtos.h"


#include "string.h"
#include "stm32_timer.h"
#include "DUST_functions.h"

#include "stm32wbaxx_hal.h"
#include "stm32wbaxx_hal_lptim.h"

#include "log_module.h"


#define DUST_CHANNELS   32u
#define SENDING_ROUND	  2
#define DUST_MAVG_WINDOW_MAX 99u

#define FRAME_SYNC1   0xAA
#define FRAME_SYNC2   0x55
#define PKT_SYNC_CAN  0xA5


uint16_t adc_val = 0;
uint8_t dust_mavg_window = 4u;   // moving average over N samples (to be tuned)
// Buffer di prova (array di uint8_t)
uint8_t test_message[] = "UART DMA TEST: Linea Operativa\r\n";
uint16_t message_size = sizeof(test_message) - 1;

// Buffer per contenere la stringa di testo da inviare
char uart_text_buffer[64];

//extern TIM_HandleTypeDef htim3;
uint16_t pwm_buf[] = {13000, 13000, 0, 0, 0, 0, 0, 0, 0, 0}; //to use in case of PWM DMA
uint8_t channel;

uint8_t spi_data[] = {0};
uint8_t size = 1;

// Buffer per inviare il "comando" (un byte dummy/comando di 16 bit)
// Nota: Userai il cast a uint8_t* in HAL_SPI_TransmitReceive_DMA
uint16_t Tx_Command_Buffer[1] = {0x0001}; // Byte dummy
uint16_t Rx_Data_Buffer[1];
uint16_t transfer_length = 1; // 1 parola (unità di 16 bit)


volatile uint8_t g_ble_dust_stream_enabled = 0;
volatile uint8_t g_usb_dust_stream_enabled = 0;


// -------------------- strutture dati per canali ------ //
typedef enum
{
    DUST_STATE_MONITORING = 0,
    DUST_STATE_CONFIRMING,
    DUST_STATE_FOUND
} DustState_t;

typedef struct
{
    // Moving average
    uint16_t mavg_buffer[DUST_MAVG_WINDOW_MAX];
    uint32_t mavg_sum;
    uint8_t  mavg_index;
    uint8_t  mavg_count;

    // Baseline (IIR lento)
    uint16_t baseline;

    // State machine
    DustState_t state;
    uint8_t  over_cnt;
    uint8_t  under_cnt;
    uint8_t refr_cnt;
    uint16_t last_raw;

    // Evento corrente
    uint16_t event_buf[DUST_EVENT_SAMPLES];
    uint8_t  event_len;
    uint32_t event_timestamp_ms;

    // Contatore particelle per canale
    uint8_t particle_count;
} DustChannelState_t;

static DustChannelState_t   g_ch[DUST_CHANNELS];
static uint8_t              g_current_channel = 0u;
static DustEventCallback_t  g_dust_cb = NULL;   // callback utente

static uint8_t              next_ch = 0u;
static uint8_t  			sending_round   = 0u;

static uint8_t uart_frame[2 + DUST_CHANNELS * 5 + 2]; // header + 32*(sync+ch+count+2B) + "\r\n"


// ---------------------------------------------- //

static const uint32_t bsrrA[32] = {
    0x80020000,  // i=0   (bits 1,3=0,0 => reset PA15, PA9)
    0x00000002,  // i=1   (bits 1,3=0,0 => same as i=0, because bit1 is 0)
    0x80000000,  // i=2   (bits 1,3=0,0 => same, bit3 is 0)
    0x00000000,  // i=3   (bits 1,3=0,1 => set PA9, reset PA15)
    0x00028000,  // i=4   (bits 1,3=1,0 => set PA15, reset PA9)
    0x00028000,  // i=5
    0x00008000,  // i=6
    0x00008000,  // i=7   (bits 1,3=1,1 => set PA15 and PA9)
    0x80020000,  // i=8
    0x00020000,  // i=9
    0x80000000,  // i=10
    0x00000000,  // i=11
    0x00028000,  // i=12
    0x00028000,  // i=13
    0x00008000,  // i=14
    0x00008000,  // i=15
    0x80020000,  // i=16
    0x00020000,  // i=17
    0x80000000,  // i=18
    0x00000000,  // i=19
    0x00028000,  // i=20
    0x00028000,  // i=21
    0x00008000,  // i=22
    0x00008000,  // i=23
    0x80020000,  // i=24
    0x00020000,  // i=25
    0x80000000,  // i=26
    0x00000000,  // i=27
    0x00028000,  // i=28
    0x00028000,  // i=29
    0x00008000,  // i=30
    0x00008000   // i=31
};

void DATA_RECEIVED(const uint8_t *data_received, uint16_t len)
{
	uint8_t cmd = data_received[0];
	switch (cmd) {

		case '1':

			if (len >= 2 && data_received[1] == 'a')
				CHANNEL_SET(1);//LED ON, poi itereremo da 0 a 32 per selezionare i canali
			else
				CHANNEL_SET(9);//LED ON, poi itereremo da 0 a 32 per selezionare i canali

			break;

		case 'k':

			if (data_received[1] == 'g')
			  LED_BLINKING(TIM_CHANNEL_1, pwm_buf); //green
			if (data_received[1] == 'r')
			  LED_BLINKING(TIM_CHANNEL_2, pwm_buf); //red --> questo è collegato al led della EBoard
			if (data_received[1] == 'b')
			  LED_BLINKING(TIM_CHANNEL_3, pwm_buf); //blue

			break;

		case 'A':

				HAL_LPTIM_Counter_Stop_IT(&hlptim1);
				g_ble_dust_stream_enabled = 0;
				g_usb_dust_stream_enabled = 0;
				GET_ADC_VALUES();
			break;

		case 'C':

				HAL_LPTIM_Counter_Start_IT(&hlptim1);

				if (len >= 2 && data_received[1] == 'b')
				{
					g_ble_dust_stream_enabled = 1;
					g_usb_dust_stream_enabled = 0;
				}
				else //use "Cu" for USB
				{
					g_ble_dust_stream_enabled = 0;
					g_usb_dust_stream_enabled = 1;
				}
				//GET_ADC_VALUES_continous();

			break;

		case 'B':
				HAL_LPTIM_Counter_Start_IT(&hlptim1);

				g_ble_dust_stream_enabled = 1;
				g_usb_dust_stream_enabled = 0;

			break;


		case 'V':

		    if (len <= 1)
		    {
		        // Nessun numero dopo 'V', ignoro
		        break;
		    }

		    char tmp[4];  // max 3 cifre + '\0'
		    uint16_t num_bytes = len - 1;

		    // Limito il numero di byte copiati a sizeof(tmp)-1
		    if (num_bytes > (sizeof(tmp) - 1))
		    {
		        num_bytes = sizeof(tmp) - 1;
		    }

		    memcpy(tmp, &data_received[1], num_bytes);
		    tmp[num_bytes] = '\0';

		    int val = atoi(tmp);   // converto la stringa in intero

		    // Clamp nella banda sensata
		    if (val < 1)
		        val = 1;
		    if (val > DUST_MAVG_WINDOW_MAX)
		        val = DUST_MAVG_WINDOW_MAX;

		    dust_mavg_window = (uint8_t)val;

		break;


		case '0':
			HAL_LPTIM_Counter_Stop_IT(&hlptim1);
			g_ble_dust_stream_enabled = 0;
			g_usb_dust_stream_enabled = 0;

			//CHANNEL_SET(1); //Led off

			HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_1);
			HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_1);

			HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_2);
			HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_2);

			HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_3);
			HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_3);

			break;

		case 0xA5:

			break;

		default:

			break;
	}
}

static inline void CHANNEL_SET_Init(void)
{
	//At initialization, all the selection pins are set to 0, so CH0 is
	//selected. This avoids ESD protection of the sensor pads to be activated.
	GPIOA->BSRR = 0x00DA0000;
}

static inline void CHANNEL_SET(uint8_t channel)
{
	channel &= 0x1F; //keep only 5 LSB bits

	GPIOA->BSRR = bsrrA[channel]; //select dust sensor channel
}

void LED_BLINKING(const uint32_t LED_COLOR, uint16_t *pwm_buffer)
{
	//HAL_TIM_PWM_Stop_DMA(&htim3, LED_COLOR);
	//__HAL_TIM_SET_AUTORELOAD(&htim3, 65535);
	//__HAL_TIM_SET_COMPARE(&htim3, LED_COLOR, 65535);
	HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_1);
	HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_2);
	HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_3);

	HAL_TIM_PWM_Start(&htim3, LED_COLOR);
}

void GET_ADC_VALUES()
{
	CHANNEL_SET(9);
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET); //Read dust chip values
	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET); //Read dust chip values
	//HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_RESET); //Do not read SD
	HAL_StatusTypeDef status;
	HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_1);

	status = HAL_SPI_TransmitReceive(&hspi3, (uint8_t*)Tx_Command_Buffer, (uint8_t*)Rx_Data_Buffer, transfer_length, 10);
    adc_val = Rx_Data_Buffer[0];
    // 2. Trasmette i 2 byte ricevuti via UART (come discusso)
    //HAL_UART_Transmit_DMA(&huart1, test_message, message_size);
    int len = sprintf(uart_text_buffer, "ADC: %d\r\n", adc_val);
    HAL_UART_Transmit_DMA(&huart1, (uint8_t*)uart_text_buffer, len);
	//status = HAL_SPI_Receive_DMA(&hspi3, spi_data, size);
}


void GET_ADC_VALUES_continous()
{

	if (hspi3.State != HAL_SPI_STATE_READY) return;

	HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET); //Read dust chip values

	// Il timer è configurato in One-Pulse Mode, quindi si fermerà da solo.
	__HAL_TIM_SET_COUNTER(&htim1, 0); // Resetta il contatore
	HAL_TIM_Base_Start_IT(&htim1);    // Avvia il timer con interrupt


	//HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET); //Read dust chip values
	//HAL_GPIO_WritePin(GPIOB, GPIO_PIN_11, GPIO_PIN_RESET); //Do not read SD
	//HAL_StatusTypeDef status;

	//status = HAL_SPI_TransmitReceive_DMA(&hspi3, (uint8_t*)Tx_Command_Buffer, (uint8_t*)Rx_Data_Buffer, transfer_length);

	//status = HAL_SPI_Receive_DMA(&hspi3, spi_data, size);
}


// Puoi mettere questa funzione in main.c o DUST_functions.c
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    // Controlla che sia TIM1 a chiamare
    if (htim->Instance == TIM1)
    {
        // 1. Ferma il timer (sicurezza, anche se in OnePulse dovrebbe fermarsi)
        HAL_TIM_Base_Stop_IT(&htim1);

        // 2. Fine Conversione: CONVST BASSO
        // Ora i dati sono pronti nel registro dell'ADC
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET);

        // 3. Avvia la lettura DMA
        // Se fallisce (es. SPI occupata), riporta CS alto per reset
        if (HAL_SPI_TransmitReceive_DMA(&hspi3, (uint8_t*)Tx_Command_Buffer, (uint8_t*)Rx_Data_Buffer, transfer_length) != HAL_OK)
        {
            HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET);
        }
    }
}

void HAL_LPTIM_AutoReloadMatchCallback(LPTIM_HandleTypeDef *hlptim)
{
	//HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_1); DEBUG

    // Selecting prossimo canale SW e HW --> POI LI METTO INSIEME
	DUST_SetCurrentChannel(next_ch);
    CHANNEL_SET(next_ch);

	GET_ADC_VALUES_continous();

    next_ch++;

    if (next_ch >= DUST_CHANNELS)
    {
        next_ch = 0u;
        //dust_send_pending = 1;
        
        sending_round++;

        // Invio dati una volta ogni N giri
        if (sending_round >= SENDING_ROUND)
        {
        	sending_round = 0;

        	if ((huart1.gState == HAL_UART_STATE_READY) && (g_usb_dust_stream_enabled == 1))
			{
        		DUST_SendFrame_UART();
			}
        	else if(g_ble_dust_stream_enabled == 1)
        	{
        		UTIL_SEQ_SetTask(1U << CFG_TASK_MYDATA_UPDATE_ID, CFG_SEQ_PRIO_0);
        	}
        }

    }

}

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi)
{
    if (hspi->Instance == SPI3)
    {
        // 1. FINE LETTURA: Riporta il pin CONVST (CS) HIGH
        // Questo fa tornare DOUT in 3-state e l'ADC in fase di Acquisizione.
        //HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET);

        uint16_t adc_val = Rx_Data_Buffer[0];
        uint32_t now_ms  = HAL_GetTick();

        //adc_val = adc_val + 1; DEBUG
        // Passo il sample al modulo dust (usa g_current_channel interno)
        DUST_Process(g_current_channel, adc_val, now_ms);

		//int len = sprintf(uart_text_buffer, "CH %02u RAW:%5u FILT:%5u\r\n", g_current_dust_channel, adc_val, filtered);
		//HAL_UART_Transmit_DMA(&huart1, (uint8_t*)uart_text_buffer, len);

    }
}

// ------------------- algoritmo canali ------------------- //

static void DUST_Internal_ResetChannel(DustChannelState_t *s)
{
    memset(s->mavg_buffer, 0, sizeof(s->mavg_buffer));
    s->mavg_sum          = 0u;
    s->mavg_index        = 0u;
    s->mavg_count        = 0u;
    s->baseline        = 0u;
    s->state           = DUST_STATE_MONITORING;
    s->over_cnt        = 0u;
    s->under_cnt       = 0u;
    s->refr_cnt        = 0u;
    s->last_raw        = 0u;
    s->event_len       = 0u;
    s->event_timestamp_ms = 0u;
    s->particle_count  = 0u;
}

// Moving average su una finestra di DUST_MAVG_WINDOW campioni
static uint16_t DUST_Internal_MAVG_Update(DustChannelState_t *s, uint16_t sample)
{
    uint8_t idx   = s->mavg_index;
    uint8_t count = s->mavg_count;

    // Finestra effettiva: clamp a [1, DUST_MAVG_WINDOW_MAX]
    uint8_t win = dust_mavg_window;
    if (win == 0u)
        win = 1u;
    if (win > DUST_MAVG_WINDOW_MAX)
        win = DUST_MAVG_WINDOW_MAX;

    if (count < win)
    {
        s->mavg_count = (uint8_t)(count + 1u);
    }

    // Rimuovo il campione vecchio dalla somma, aggiungo il nuovo
    s->mavg_sum -= s->mavg_buffer[idx];
    s->mavg_sum += sample;

    // Scrivo il nuovo campione nel buffer circolare
    s->mavg_buffer[idx] = sample;

    // Avanzo indice
    idx++;
    if (idx >= win)
    {
        idx = 0u;
    }
    s->mavg_index = idx;

    // Media: uso count se non ho ancora riempito la finestra
    uint8_t denom = s->mavg_count;
    if (denom == 0u)
    {
        return sample; // protezione, non dovrebbe succedere
    }

    uint16_t avg = (uint16_t)(s->mavg_sum / (uint32_t)denom);
    return avg;
}

// Baseline IIR: y += (x - y) >> shift
static uint16_t DUST_Internal_Baseline_Update(uint16_t prev, uint16_t x, uint8_t shift)
{
    int32_t diff = (int32_t)x - (int32_t)prev;
    prev = (uint16_t)((int32_t)prev + (diff >> shift));
    return prev;
}

// Chiama la callback utente con i dati dell'evento
static void DUST_Internal_CallCallback(uint8_t ch, DustChannelState_t *s)
{
    if (g_dust_cb == NULL)
        return;

    DustEvent_t ev;
    ev.channel      = ch;
    ev.timestamp_ms = s->event_timestamp_ms;
    ev.len          = s->event_len;
    if (ev.len > DUST_EVENT_SAMPLES)
        ev.len = DUST_EVENT_SAMPLES;

    for (uint8_t i = 0u; i < ev.len; i++)
    {
        ev.samples[i] = s->event_buf[i];
    }

    // IMPORTANTE: questa funzione viene chiamata in contesto di ISR (SPI callback).
    // Qui dentro la callback NON deve fare cose lente o bloccanti.
    g_dust_cb(&ev);
}

void DUST_Init(void)
{
    for (uint8_t ch = 0u; ch < DUST_CHANNELS; ch++)
    {
        DUST_Internal_ResetChannel(&g_ch[ch]);
    }
    g_current_channel = 0u;
    g_dust_cb         = NULL;
}

void DUST_SetCallback(DustEventCallback_t cb)
{
    g_dust_cb = cb;
}

void DUST_SetCurrentChannel(uint8_t ch)
{
    if (ch >= DUST_CHANNELS)
    {
        ch = 0u;
    }
    g_current_channel = ch;

    // QUI NON faccio niente sull'hardware: gestire mux HW
    // nella CHANNEL_SET(...)
}

// Da chiamare nella callback SPI quando arriva un nuovo sample ADC
void DUST_Process(uint8_t channel, uint16_t raw_sample, uint32_t timestamp_ms)
{
    uint8_t ch = channel;
    if (ch >= DUST_CHANNELS)
        return;

    DustChannelState_t *s = &g_ch[ch];

    // 1) Moving average
    uint16_t filtered = DUST_Internal_MAVG_Update(s, raw_sample);
    s->last_raw = raw_sample;

    // 2) Baseline lenta solo quando non siamo in evento
    if (s->state == DUST_STATE_MONITORING)
    {
        s->baseline = DUST_Internal_Baseline_Update(s->baseline,
                                                    filtered,
                                                    DUST_BASE_SHIFT);
    }

    // 3) Calcolo soglie (isteresi)
    uint16_t thr_high = (uint16_t)(s->baseline + DUST_THRESH_OFFSET);
    uint16_t thr_low  = (uint16_t)(s->baseline + (DUST_THRESH_OFFSET / 2u));

    // 4) State machine
    switch (s->state)
    {
        case DUST_STATE_MONITORING:
        {
            if (filtered > thr_high)
            {
                if (s->over_cnt < 255u) s->over_cnt++;

                if (s->over_cnt >= DUST_MIN_OVER_SAMPLES)
                {
                    // Inizio nuovo evento
                    s->state              = DUST_STATE_CONFIRMING;
                    s->over_cnt           = 0u;
                    s->under_cnt          = 0u;
                    s->event_len          = 0u;
                    s->event_timestamp_ms = timestamp_ms;

                    // Primo sample dell'evento
                    if (s->event_len < DUST_EVENT_SAMPLES)
                    {
                        s->event_buf[s->event_len++] = filtered;
                    }
                }
            }
            else
            {
                s->over_cnt = 0u;
            }
        } break;

        case DUST_STATE_CONFIRMING:
        {

            // Se il segnale resta alto, contyinuo a confermare l'evento
            if (filtered > thr_high)
            {
            
                if (s->over_cnt < 255u) s->over_cnt++;

                if (s->over_cnt >= 4u)   // se trovo 5 campioni alti
                {
                    // Confermo definitivamente, particella rivelata
                    s->state        = DUST_STATE_FOUND;
                    s->over_cnt     = 0u;
                    s->under_cnt    = 0u;
                    s->particle_count++;

                    // salvo sample
                    if (s->event_len < DUST_EVENT_SAMPLES)
                    {
                        s->event_buf[s->event_len++] = filtered;
                    }

                    // contatore di assestamento
                    s->refr_cnt = 1;  // ad es. 4 o 5
                }
            }
            else
            {
                // Il segnale e' tornato basso, quindi era solo picco di rumore
                s->state    = DUST_STATE_MONITORING;
                s->over_cnt = 0u;
                s->event_len = 0u;
            }

        } break;

        case DUST_STATE_FOUND:
        {
            // Eventi di assestamento
            if (s->event_len < DUST_EVENT_SAMPLES)
            {
                s->event_buf[s->event_len++] = filtered;
            }

            if (s->refr_cnt > 0u)
            {
                s->refr_cnt--;
            }
            else
            {
                // Fine del periodo di assestamento, l'evento si conclude e viene registrato con un callback
                s->state     = DUST_STATE_MONITORING;
                s->over_cnt  = 0u;
                s->under_cnt = 0u;

                DUST_Internal_CallCallback(ch, s);
            }

        } break;

        default:
            s->state = DUST_STATE_MONITORING;
            break;
    }
}

uint16_t DUST_BuildFrame(uint8_t *dst, uint16_t max_len)
{
    uint8_t *p = dst;

    // Header
    *p++ = FRAME_SYNC1;
    *p++ = FRAME_SYNC2;

    // Corpo: per ogni canale -> [PKT_SYNC_CAN][CHANNEL][PARTICLES][ADC_MSB][ADC_LSB]
    for (uint8_t ch = 0; ch < DUST_CHANNELS; ch++)
    {
        uint16_t adc = g_ch[ch].last_raw;        // oppure last_filtered

        *p++ = PKT_SYNC_CAN;
        *p++ = ch;                               // channel number
        *p++ = g_ch[ch].particle_count;
        *p++ = (uint8_t)(adc >> 8);              // ADC_HI
        *p++ = (uint8_t)(adc & 0xFF);            // ADC_LO
    }

    // Terminatore di riga
    *p++ = '\r';
    *p++ = '\n';

    //uint16_t total_len = (uint16_t)(p - uart_frame);

    return (uint16_t)(p - dst);
    //HAL_UART_Transmit_DMA(&huart1, uart_frame, total_len);

}

void DUST_SendFrame_UART(void)
{
	uint16_t len = DUST_BuildFrame(uart_frame, sizeof(uart_frame));

	if (len == 0u)
	{
		return; // buffer troppo piccolo o errore
	}

	HAL_UART_Transmit_DMA(&huart1, uart_frame, len);
}
