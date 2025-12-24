/*-----------------------------------------------------------------------*/
/* Low level disk I/O module for STM32 - ROBUST VERSION                  */
/*-----------------------------------------------------------------------*/

#include "ff.h"
#include "diskio.h"
#include "main.h"

extern SPI_HandleTypeDef hspi3;

// --- CONFIGURAZIONE PIN (Verifica che siano i tuoi!) ---
#define SD_CS_PORT    GPIOB
#define SD_CS_PIN     GPIO_PIN_11

// Macro per il Chip Select
#define CS_HIGH()	HAL_GPIO_WritePin(SD_CS_PORT, SD_CS_PIN, GPIO_PIN_SET)
#define CS_LOW()	HAL_GPIO_WritePin(SD_CS_PORT, SD_CS_PIN, GPIO_PIN_RESET)

// Comandi SD Standard
#define CMD0	(0)			/* GO_IDLE_STATE */
#define CMD1	(1)			/* SEND_OP_COND (MMC) */
#define	ACMD41	(0x80+41)	/* SEND_OP_COND (SDC) */
#define CMD8	(8)			/* SEND_IF_COND */
#define CMD16	(16)		/* SET_BLOCKLEN */
#define CMD17	(17)		/* READ_SINGLE_BLOCK */
#define CMD24	(24)		/* WRITE_BLOCK */
#define CMD55	(55)		/* APP_CMD */
#define CMD58	(58)		/* READ_OCR */

/*-----------------------------------------------------------------------*/
/* Funzioni di Trasmissione/Ricezione SPI "Pure"                         */
/*-----------------------------------------------------------------------*/

static uint8_t SPI_TxRx(uint8_t data) {
    uint8_t rx_data;
    // Timeout breve ma bloccante per essere sicuri che il dato passi
    HAL_SPI_TransmitReceive(&hspi3, &data, &rx_data, 1, 100);
    return rx_data;
}

static void xmit_spi(uint8_t data) {
    SPI_TxRx(data);
}

static uint8_t rcvr_spi(void) {
    return SPI_TxRx(0xFF); // Invia dummy 0xFF per leggere
}

/* Attesa che la SD rilasci il BUS (Wait for Ready) */
static int wait_ready(void) {
    uint8_t d;
    uint16_t tmr;
    for (tmr = 5000; tmr; tmr--) { // Timeout circa 500ms
        d = rcvr_spi();
        if (d == 0xFF) return 1; // OK, la SD ha rilasciato MISO
        HAL_Delay(1);
    }
    return 0; // Timeout
}

/* Deseleziona la card e rilascia SPI */
static void deselect(void) {
    CS_HIGH();
    rcvr_spi(); // Clock dummy dopo CS alto (richiesto da alcune SD)
}

/* Seleziona la card e aspetta che sia pronta */
static int select(void) {
    CS_LOW();
    if (wait_ready()) return 1; // OK
    deselect();
    return 0; // Timeout
}

/* Invia un comando alla SD */
static uint8_t send_cmd(uint8_t cmd, uint32_t arg) {
    uint8_t n, res;

    // Se è un comando ACMD, invia prima CMD55
    if (cmd & 0x80) {
        cmd &= 0x7F;
        res = send_cmd(CMD55, 0);
        if (res > 1) return res;
    }

    // Seleziona la card
    deselect();
    if (!select()) return 0xFF;

    // Invia pacchetto comando
    xmit_spi(0x40 | cmd);
    xmit_spi((uint8_t)(arg >> 24));
    xmit_spi((uint8_t)(arg >> 16));
    xmit_spi((uint8_t)(arg >> 8));
    xmit_spi((uint8_t)arg);

    // CRC (Valido solo per CMD0 e CMD8, gli altri lo ignorano in SPI mode)
    n = 0x01;
    if (cmd == CMD0) n = 0x95;
    if (cmd == CMD8) n = 0x87;
    xmit_spi(n);

    // Attendi risposta (ignora il byte di stuffing se presente)
    if (cmd == 12) rcvr_spi();

    n = 10;
    do {
        res = rcvr_spi();
    } while ((res & 0x80) && --n);

    return res;
}

/*-----------------------------------------------------------------------*/
/* Inizializzazione Disco                                                */
/*-----------------------------------------------------------------------*/
DSTATUS disk_initialize(BYTE pdrv) {
    uint8_t n, cmd, ty, ocr[4];

    if (pdrv) return STA_NOINIT;

    // 1. Ritardo accensione
    HAL_Delay(20);

    // 2. Invia 80 clock dummy con CS ALTO per svegliare la SD (FONDAMENTALE)
    CS_HIGH();
    for (n = 10; n; n--) rcvr_spi();

    // 3. Entra in Idle State
    ty = 0;
    if (send_cmd(CMD0, 0) == 1) {
        // Timer software approssimativo (1 sec)
        uint16_t timeout = 1000;

        if (send_cmd(CMD8, 0x1AA) == 1) { /* SDv2? */
            for (n = 0; n < 4; n++) ocr[n] = rcvr_spi();
            if (ocr[2] == 0x01 && ocr[3] == 0xAA) {
                while (timeout-- && send_cmd(ACMD41, 1UL << 30)); // Wait Init
                if (timeout && send_cmd(CMD58, 0) == 0) {
                    for (n = 0; n < 4; n++) ocr[n] = rcvr_spi();
                    ty = (ocr[0] & 0x40) ? 12 : 4;
                }
            }
        } else { /* SDv1 or MMCv3 */
            if (send_cmd(ACMD41, 0) <= 1) {
                ty = 2; cmd = ACMD41; /* SDv1 */
            } else {
                ty = 1; cmd = CMD1; /* MMCv3 */
            }
            while (timeout-- && send_cmd(cmd, 0));
            if (!timeout || send_cmd(CMD16, 512) != 0) ty = 0;
        }
    }

    deselect();
    return ty ? 0 : STA_NOINIT;
}

/*-----------------------------------------------------------------------*/
/* Lettura                                                               */
/*-----------------------------------------------------------------------*/
DRESULT disk_read(BYTE pdrv, BYTE *buff, LBA_t sector, UINT count) {
    if (pdrv || !count) return RES_PARERR;
    if (send_cmd(CMD17, sector) == 0) { // READ_SINGLE_BLOCK
        // Wait data token
        uint16_t tmr = 2000;
        uint8_t d;
        do {
            d = rcvr_spi();
        } while (d != 0xFE && --tmr);

        if (d == 0xFE) {
            for (uint16_t i = 0; i < 512; i++) *buff++ = rcvr_spi();
            rcvr_spi(); rcvr_spi(); // CRC
            deselect();
            return RES_OK;
        }
    }
    deselect();
    return RES_ERROR;
}

/*-----------------------------------------------------------------------*/
/* Scrittura                                                             */
/*-----------------------------------------------------------------------*/
DRESULT disk_write(BYTE pdrv, const BYTE *buff, LBA_t sector, UINT count) {
    if (pdrv || !count) return RES_PARERR;
    if (send_cmd(CMD24, sector) == 0) { // WRITE_BLOCK
        xmit_spi(0xFF); // Dummy
        xmit_spi(0xFE); // Data token
        for (uint16_t i = 0; i < 512; i++) xmit_spi(*buff++);
        xmit_spi(0xFF); xmit_spi(0xFF); // CRC Dummy

        uint8_t resp = rcvr_spi();
        if ((resp & 0x1F) == 0x05) { // Data Accepted
            wait_ready(); // Aspetta fine scrittura flash interna
            deselect();
            return RES_OK;
        }
    }
    deselect();
    return RES_ERROR;
}

DRESULT disk_ioctl(BYTE pdrv, BYTE cmd, void *buff) { return RES_OK; }
DSTATUS disk_status(BYTE pdrv) { return 0; }
DWORD get_fattime(void) { return 0; }
