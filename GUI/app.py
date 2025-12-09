import os
from PIL import Image
import customtkinter as ctk
import time
import serial
from serial.tools import list_ports
import asyncio
import threading
from bleak import BleakScanner, BleakClient
from connection_tab import ConnectionTab
from visual_tab import VisualTab
from advanced_tab import AdvancedTab
from settings_tab import SettingsTab
from collections import deque


# --------- UUID BLE ---------
BT_SERVICE_UUID       = "00000000-0001-11e1-9ab4-0002a5d5c51b"
BT_CHAR_MYDATA_UUID   = "00c00000-0001-11e1-ac36-0002a5d5c51b"  # notify
BT_CHAR_RECVDATA_UUID = "000c0000-0001-11e1-ac36-0002a5d5c51b"  # write

# --------- Costanti protocollo DUST ---------
DUST_CHANNELS = 32
FRAME_SYNC1 = 0xAA
FRAME_SYNC2 = 0x55
PKT_SYNC_CAN = 0xA5
FRAME_LEN = 2 + DUST_CHANNELS * 5 + 2  # AA 55 + 32*(A5 ch hi lo) + \r\n


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Profiling semplice delle prestazioni
        self._profile_last_log = time.perf_counter()
        self._profile_frame_count = 0
        self._profile_last_frame_ms = 0.0
        self._profile_total_frame_ms = 0.0

        # Throttling del disegno grafici
        self._last_draw_time = 0.0
        self._min_draw_interval = 0.1  # 40 ms ≈ 25 Hz di refresh grafico
        # ------------------------------------ #

        self.title("DUST Monitor")
        self.geometry("1000x650")
        self.minsize(800, 500)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # ----- Barra superiore con loghi dipendenti dal tema -----
        base_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            # LEFT logo: light + dark
            left_light = Image.open(os.path.join(base_dir, "img/polimiD.png"))
            left_dark = Image.open(os.path.join(base_dir, "img/polimiW.png"))
            self.logo_l = ctk.CTkImage(
                light_image=left_light,
                dark_image=left_dark,
                size=(190, 60),
            )

            # RIGHT logo: light + dark
            right_light = Image.open(os.path.join(base_dir, "img/i3n.png"))
            right_dark = Image.open(os.path.join(base_dir, "img/i3nW.png"))
            self.logo_r = ctk.CTkImage(
                light_image=right_light,
                dark_image=right_dark,
                size=(200, 48),
            )
        except Exception as e:
            print("Errore nel caricamento dei loghi:", e)
            self.logo_l = None
            self.logo_r = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=10, pady=(5, 0))
        header.grid_rowconfigure(0, weight=1)
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        if self.logo_l is not None:
            left_logo_label = ctk.CTkLabel(header, text="", image=self.logo_l)
            left_logo_label.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            header,
            text="DUST Tracker Monitor",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
        )
        title_label.grid(row=0, column=1, sticky="nsew", pady=(10, 10))

        if self.logo_r is not None:
            right_logo_label = ctk.CTkLabel(header, text="", image=self.logo_r)
            right_logo_label.grid(row=0, column=2, sticky="e")

        # --- Serial e BLE ---
        self.serial = None
        self.ble_client = None
        self._bt_scan_results = {}

        # Event loop BLE dedicato
        self.ble_loop = asyncio.new_event_loop()
        self.ble_thread = threading.Thread(target=self._ble_loop_runner, daemon=True)
        self.ble_thread.start()

        # Buffer e dati
        self._dust_rx_buffer = bytearray()
        self.channel_values = [0 for _ in range(DUST_CHANNELS)]
        self.channel_particles = [0 for _ in range(DUST_CHANNELS)]
        self.global_count = 0
        self.channel_history = [deque(maxlen=200) for _ in range(DUST_CHANNELS)]

        # GUI
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_connection_page = self.tabview.add("Connection")
        self.tab_visual_page = self.tabview.add("Global")
        self.tab_advanced_page = self.tabview.add("Channels")
        self.tab_settings_page = self.tabview.add("Settings")

        self.connection_tab = ConnectionTab(self.tab_connection_page, controller=self)
        self.connection_tab.pack(fill="both", expand=True)
        self.visual_tab = VisualTab(self.tab_visual_page, controller=self)
        self.visual_tab.pack(fill="both", expand=True)
        self.advanced_tab = AdvancedTab(
            self.tab_advanced_page, controller=self, num_channels=DUST_CHANNELS
        )
        self.advanced_tab.pack(fill="both", expand=True)
        self.settings_tab = SettingsTab(self.tab_settings_page, controller=self)
        self.settings_tab.pack(fill="both", expand=True)

        self._refresh_serial_ports()

    # ---------- BLE loop ----------
    def _ble_loop_runner(self):
        asyncio.set_event_loop(self.ble_loop)
        self.ble_loop.run_forever()

    # ---------- Log ----------
    def _log(self, text: str):
        self.connection_tab.log(text)

    # ---------- Serial ----------
    def _get_serial_ports(self):
        ports = list_ports.comports()
        return [p.device for p in ports] or ["No ports found"]

    def _refresh_serial_ports(self):
        ports = self._get_serial_ports()
        self.connection_tab.set_serial_ports(ports)
        self._log("[INFO] Serial ports refreshed")

    # ---------- BLE SCAN ----------
    def _on_bt_scan(self):
        self._log("[BT] Scanning for BLE devices...")

        async def do_scan():
            devices = await BleakScanner.discover(timeout=3.0)
            dust_devices = [d for d in devices if d.name and d.name.startswith("DUST_")]
            addr_map = {d.name: d.address for d in dust_devices}
            names = list(addr_map.keys())
            return names, addr_map

        future = asyncio.run_coroutine_threadsafe(do_scan(), self.ble_loop)

        def done_cb(fut):
            try:
                names, addr_map = fut.result()
            except Exception as err:
                self.after(0, lambda: self._log(f"[BT] Scan error: {err}"))
                return

            def update_ui():
                self._bt_scan_results = addr_map
                self.connection_tab.set_bt_devices(names)
                if names:
                    self._log(f"[BT] Found: {', '.join(names)}")
                else:
                    self._log("[BT] No DUST_ devices found")

            self.after(0, update_ui)

        future.add_done_callback(done_cb)

    # ---------- BLE CONNECT ----------
    def _on_bt_connect(self):
        # Se già connesso -> disconnette
        if self.ble_client is not None:
            self._log("[BT] Disconnecting...")
            future = asyncio.run_coroutine_threadsafe(self._bt_disconnect_async(), self.ble_loop)

            def done_cb(fut):
                try:
                    fut.result()
                except Exception as err:
                    self.after(0, lambda: self._log(f"[BT] Disconnect error: {err}"))
                else:
                    self.after(0, lambda: self._log("[BT] Disconnected"))
                finally:
                    self.ble_client = None

            future.add_done_callback(done_cb)
            return

        # Altrimenti connetti
        name = self.connection_tab.get_bt_selection()
        if not name or name.startswith("Press") or name.startswith("No DUST"):
            self._log("[BT] Please scan and select a valid device")
            return

        address = self._bt_scan_results.get(name)
        if not address:
            self._log(f"[BT] No address for device '{name}' (scan again)")
            return

        self._log(f"[BT] Connecting to {name} ({address})...")

        future = asyncio.run_coroutine_threadsafe(self._bt_connect_async(address), self.ble_loop)

        def done_cb(fut):
            try:
                ok = fut.result()
            except Exception as err:
                self.after(0, lambda: self._log(f"[BT] Connect error: {err}"))
                return

            if ok:
                self.after(0, lambda: self._log("[BT] Connected successfully"))
            else:
                self.after(0, lambda: self._log("[BT] Connection failed"))

        future.add_done_callback(done_cb)

    async def _bt_connect_async(self, address: str) -> bool:
        """Connessione BLE e start_notify."""
        try:
            client = BleakClient(address)
            await client.connect()
            await asyncio.sleep(0.4)  # stabilizza connessione GATT
            if not client.is_connected:
                return False

            self.ble_client = client
            try:
                await client.start_notify(BT_CHAR_MYDATA_UUID, self._bt_notification_handler)
            except Exception as err:
                await asyncio.sleep(0.5)
                try:
                    await client.start_notify(BT_CHAR_MYDATA_UUID, self._bt_notification_handler)
                except Exception as err2:
                    self.after(0, lambda: self._log(f"[BT] start_notify error: {err2}"))
                    return False

            return True

        except Exception as e:
            self.after(0, lambda: self._log(f"[BT] Connect exception: {e}"))
            return False

    async def _bt_disconnect_async(self):
        if self.ble_client is not None:
            try:
                try:
                    await self.ble_client.stop_notify(BT_CHAR_MYDATA_UUID)
                except Exception:
                    pass
                await self.ble_client.disconnect()
            except Exception:
                pass
            self.ble_client = None

    # ---------- INVIO COMANDI ----------
    def _bt_send_command(self, cmd_byte: bytes):
        if self.ble_client is None or not self.ble_client.is_connected:
            self._log("[BT] Not connected, cannot send command")
            return

        self._log(f"[BT] Sending command {cmd_byte!r}")

        async def do_write():
            await self.ble_client.write_gatt_char(BT_CHAR_RECVDATA_UUID, cmd_byte, response=True)

        future = asyncio.run_coroutine_threadsafe(do_write(), self.ble_loop)

        def done_cb(fut):
            try:
                fut.result()
            except Exception as err:
                self.after(0, lambda: self._log(f"[BT] Write error: {err}"))
            else:
                self.after(0, lambda: self._log("[BT] Command sent OK"))

        future.add_done_callback(done_cb)

    def _on_send_text(self, text: str):
        if not text:
            self._log("[CMD] Empty command")
            return
        self._bt_send_command(text.encode("ascii", errors="ignore"))

    def _on_start_acquisition(self):
        self._bt_send_command(b'Cb')

    def _on_stop_acquisition(self):
        self._bt_send_command(b'0')

    # ---------- NOTIFY HANDLER ----------
    def _bt_notification_handler(self, sender, data: bytes):
        hex_str = " ".join(f"{b:02X}" for b in data)
        data_copy = bytes(data)
        self.after(0, lambda: self._handle_bt_message(hex_str, data_copy))

    def _handle_bt_message(self, hex_text: str, raw: bytes):
        self._log(f"[BT RX] {hex_text}")
        self._append_dust_bytes(raw)

    # ---------- PARSING FRAME DUST ----------
    def _append_dust_bytes(self, data: bytes):
        buf = self._dust_rx_buffer
        buf.extend(data)

        while True:
            # serve almeno AA 55
            if len(buf) < 2:
                return

            # cerca la sequenza di sync
            start = -1
            for i in range(len(buf) - 1):
                if buf[i] == FRAME_SYNC1 and buf[i + 1] == FRAME_SYNC2:
                    start = i
                    break

            if start < 0:
                # nessun sync trovato, butto tutto
                buf.clear()
                return

            if start > 0:
                # scarto eventuale spazzatura prima del sync
                del buf[:start]

            # se non ho ancora tutto il frame, esco
            if len(buf) < FRAME_LEN:
                return

            candidate = buf[:FRAME_LEN]

            # controllo terminazione \r\n
            if not (candidate[-2] == 0x0D and candidate[-1] == 0x0A):
                # pacchetto corrotto: scarto il primo byte e riprovo
                del buf[0]
                continue

            adc_values = [0] * DUST_CHANNELS
            particles_values = [0] * DUST_CHANNELS
            valid = True

            # parse dei 32 blocchi A5 ch part MSB LSB
            for k in range(DUST_CHANNELS):
                off = 2 + k * 5

                if candidate[off] != PKT_SYNC_CAN:
                    valid = False
                    break

                ch = candidate[off + 1]
                particles = candidate[off + 2]

                # MSB/LSB → 16 bit in complemento a due
                raw = (candidate[off + 3] << 8) | candidate[off + 4]
                if raw & 0x8000:
                    raw -= 0x10000       # ora è signed (-32768 .. 32767)

                adc = abs(raw)           # come hai detto: usi il modulo

                if 0 <= ch < DUST_CHANNELS:
                    adc_values[ch] = adc
                    particles_values[ch] = particles

            if not valid:
                # sync canale non trovato → scarto un byte e riprovo
                del buf[0]
                continue

            # inoltra il frame al resto della GUI
            self._handle_dust_frame(adc_values, particles_values)

            # rimuove il frame dal buffer e, se avanzano byte, ricomincia
            del buf[:FRAME_LEN]

    def _handle_dust_frame(self, adc_values, particles_values):
        """
        Viene chiamata ad ogni frame BLE (es. ogni 16 ms).
        - Aggiorna sempre i valori numerici interni.
        - Ridisegna i grafici solo se è passato abbastanza tempo
        dall'ultimo redraw (throttling).
        """
        now = time.perf_counter()

        # 1) Aggiorno SEMPRE i valori interni per tutti i canali
        for ch in range(min(DUST_CHANNELS, len(adc_values))):
            adc = adc_values[ch]
            particles = particles_values[ch]

            self.channel_values[ch] = adc
            self.channel_particles[ch] = particles

        # Conteggio globale particelle (valore "vero" aggiornato ad ogni frame)
        if particles_values:
            global_particles = sum(particles_values)
            self.global_count = int(global_particles)

        # 2) Decido se è il momento di ridisegnare i grafici
        if now - self._last_draw_time < self._min_draw_interval:
            # Troppo presto → non aggiorno history né grafici
            return

        self._last_draw_time = now

        # 3) SOLO QUI aggiorno la history e i grafici (max ~25 Hz)
        for ch in range(min(DUST_CHANNELS, len(adc_values))):
            adc = self.channel_values[ch]
            particles = self.channel_particles[ch]

            # history per disegnare "la linea"
            self.channel_history[ch].append(adc)

            # mini-grafici + finestra per canale
            self.advanced_tab.update_channel(ch, adc, particles)

        # grafico e label globali (tab Global)
        self.visual_tab.update_global(self.global_count)

    # ---------- REFRESH RATE ----------
    def set_refresh_interval(self, interval_seconds: float):
        """
        Cambia l'intervallo minimo tra un redraw e l'altro dei grafici.
        Usato dalla tab Settings (Refresh Rate).
        """
        try:
            value = float(interval_seconds)
        except (TypeError, ValueError):
            return

        if value <= 0:
            return

        self._min_draw_interval = value

    # ---------- TEMA / ASPETTO ----------
    def on_theme_changed(self):
        """Forza il ridisegno dei grafici quando cambia il tema (Dark/Light)."""

        # grafico globale
        try:
            self.visual_tab.global_graph.redraw()
        except Exception:
            pass

        # anteprime canali (tab Channels)
        try:
            for preview in self.advanced_tab.channel_previews:
                preview.graph.redraw()
        except Exception:
            pass

        # finestre dei singoli canali, se aperte
        try:
            for win in self.advanced_tab.channel_windows.values():
                try:
                    if win.winfo_exists():
                        win.graph.redraw()
                except Exception:
                    pass
        except Exception:
            pass

    # ---------- CHIUSURA ----------
    def on_close(self):
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except Exception:
                pass

        if self.ble_client is not None:
            fut = asyncio.run_coroutine_threadsafe(self._bt_disconnect_async(), self.ble_loop)
            try:
                fut.result(timeout=1.0)
            except Exception:
                pass

        if self.ble_loop.is_running():
            self.ble_loop.call_soon_threadsafe(self.ble_loop.stop)
        self.destroy()
