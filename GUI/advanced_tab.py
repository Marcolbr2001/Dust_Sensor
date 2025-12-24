import tkinter as tk
import customtkinter as ctk
from widgets import ChannelPreview, ChannelWindow


class AdvancedTab(ctk.CTkFrame):
    """Tab 'Advanced': griglia 4x8 di anteprime canali + controlli Start/Stop + SD."""

    def __init__(self, master, controller, num_channels: int = 32):
        super().__init__(master)
        self.controller = controller
        self.num_channels = num_channels

        # riga 0: controlli, riga 1: griglia
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # barra controlli in alto
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 0))
        
        # DEFINIZIONE COLONNE AGGIORNATA:
        # 0: Label
        # 1: Start
        # 2: Stop
        # 3: Save to File Switch (PC)
        # 4: Save to SD Switch (MCU)  <-- NUOVO
        # 5: Spazio vuoto (Weight=1)  <-- SPOSTATO
        # 6: Switch voltage (Destra)  <-- SPOSTATO
        control_frame.grid_columnconfigure(0, weight=0)
        control_frame.grid_columnconfigure(1, weight=0)
        control_frame.grid_columnconfigure(2, weight=0)
        control_frame.grid_columnconfigure(3, weight=0)
        control_frame.grid_columnconfigure(4, weight=0) # Colonna per SD
        control_frame.grid_columnconfigure(5, weight=1) # Spazio elastico
        control_frame.grid_columnconfigure(6, weight=0)

        label = ctk.CTkLabel(
            control_frame,
            text="Acquisition:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        label.grid(row=0, column=0, padx=(0, 8), pady=5, sticky="w")

        start_btn = ctk.CTkButton(
            control_frame,
            text="▶",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=60,
            command=self._on_start_pressed,
        )
        start_btn.grid(row=0, column=1, padx=(0, 6), pady=5, sticky="w")

        stop_btn = ctk.CTkButton(
            control_frame,
            text="■",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=60,
            command=self._on_stop_pressed,
        )
        stop_btn.grid(row=0, column=2, padx=(0, 15), pady=5, sticky="w")
        
        # --- Switch per LOGGING SU PC ---
        self.log_switch = ctk.CTkSwitch(
            control_frame,
            text="Save to file",
            command=self._on_log_switch_toggle
        )
        self.log_switch.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # --- NUOVO SWITCH PER LOGGING SU SD ---
        self.sd_switch = ctk.CTkSwitch(
            control_frame,
            text="Save to SD",
            command=self._on_sd_switch_toggle
        )
        self.sd_switch.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        # Pulsante Switch bit/voltage (ora a colonna 6)
        self.display_mode = ctk.StringVar(value="bit")
        self.btn_switch_mode = ctk.CTkButton(
            control_frame,
            text="Switch to voltage",
            width=150,
            command=self._toggle_display_mode,
        )
        # Nota: aggiornato index colonna a 6
        self.btn_switch_mode.grid(row=0, column=6, padx=(0, 15), pady=10, sticky="e")

        # --- griglia 4x8 di anteprime canali ---
        grid_frame = ctk.CTkFrame(self)
        grid_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)

        for col in range(8):
            grid_frame.grid_columnconfigure(col, weight=1, minsize=150)
        for row in range(4):
            grid_frame.grid_rowconfigure(row, weight=1, minsize=60)

        self.channel_previews = []

        for ch in range(num_channels):
            row = ch // 8
            col = ch % 8
            preview = ChannelPreview(
                grid_frame,
                channel_id=ch + 1,
                click_callback=self._open_channel_window,
            )
            preview.grid(row=row, column=col, padx=8, pady=4, sticky="nsew")
            self.channel_previews.append(preview)

        self.channel_windows = {}

    def update_channel(self, ch_index: int, value: int, particles: int | None = None):
        if 0 <= ch_index < len(self.channel_previews):
            preview = self.channel_previews[ch_index]
            preview.update_from_value(value)
            if particles is not None:
                preview.set_particles(particles)

        channel_id = ch_index + 1
        win = self.channel_windows.get(channel_id)

        if win is not None:
            try:
                if win.winfo_exists():
                    win.update_from_value(value, particles=particles)
                else:
                    del self.channel_windows[channel_id]
            except tk.TclError:
                if channel_id in self.channel_windows:
                    del self.channel_windows[channel_id]

    def _open_channel_window(self, channel_id: int):
        if channel_id in self.channel_windows:
            try:
                win = self.channel_windows[channel_id]
                win.focus()
                return
            except Exception:
                pass

        history = None
        if hasattr(self.controller, "channel_history"):
            history = list(self.controller.channel_history[channel_id - 1])

        initial_particles = None
        if hasattr(self.controller, "channel_particles"):
            try:
                initial_particles = self.controller.channel_particles[channel_id - 1]
            except Exception:
                initial_particles = None

        win = ChannelWindow(
            self,
            channel_id,
            history=history,
            initial_particles=initial_particles
        )
        self.channel_windows[channel_id] = win

    def _on_start_pressed(self):
        self.controller._on_start_acquisition()

    def _on_stop_pressed(self):
        self.controller._on_stop_acquisition()
        
    def _on_log_switch_toggle(self):
        is_active = bool(self.log_switch.get())
        if self.controller:
            self.controller.set_logging_state(is_active)

    def _on_sd_switch_toggle(self):
        """
        Callback per lo switch SD.
        Invia 'S' se attivato via Bluetooth.
        """
        is_active = bool(self.sd_switch.get())
        
        # Se lo switch viene attivato (ON)
        if is_active:
            # Usiamo il metodo _bt_send_command che è già definito in app.py
            if hasattr(self.controller, "_bt_send_command"):
                print("DEBUG: Sending 'S' to SD card via BLE...")
                # Invio 'S' come bytes
                self.controller._bt_send_command(b'S')
            else:
                print("Error: Controller method _bt_send_command not found.")
        else:
            # Qui gestisci cosa succede quando lo switch viene spento (OFF).
            # Dato che lato STM32 'S' scrive un singolo file e poi si ferma, 
            # potresti voler inviare un comando per fermare o semplicemente nulla.
            # Se vuoi mandare '0' o altro quando spegni:
            # self.controller._bt_send_command(b'0')
            pass

    def _toggle_display_mode(self):
        if self.display_mode.get() == "bit":
            self.display_mode.set("voltage")
            self.btn_switch_mode.configure(text="Switch to bit")
        else:
            self.display_mode.set("bit")
            self.btn_switch_mode.configure(text="Switch to voltage")

        for preview in self.channel_previews:
            preview.set_display_mode(self.display_mode.get())