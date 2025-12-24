# settings_tab.py
import customtkinter as ctk


class SettingsTab(ctk.CTkFrame):
    """
    Tab 'Settings'

    - DUST Clock: tre radio button (50 / 200 / 400 kHz) che inviano
      '5', '20', '40' via BT.
    - Channel Read Mode: switch Manual/Auto che invia 'M' o 'A' via BT.
    - Custom Value (V): spinbox numerico con freccette che invia 'V<number>'.
    - Appearance Mode: selettore Dark / Light / System.
    """

    def __init__(self, master, controller=None):
        super().__init__(master)

        # controller (App) usato per chiamare _bt_send_command(...)
        self.controller = controller

        # Font per le descrizioni in corsivo
        self._desc_font = ctk.CTkFont(size=11, slant="italic")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)
        # riga 0: tre card principali
        # riga 1: card unica Display (refresh + appearance)
        # riga 2: spazio riempitivo
        content.grid_rowconfigure(0, weight=0)
        content.grid_rowconfigure(1, weight=0)
        content.grid_rowconfigure(2, weight=1)

        # ------------------------------------------------------------------ #
        # 1) RIGA SUPERIORE: DUST CLOCK / READ MODE / AVERAGING WINDOW
        # ------------------------------------------------------------------ #
        top_frame = ctk.CTkFrame(content)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(0, weight=1)  # DUST Clock
        top_frame.grid_columnconfigure(1, weight=1)  # Channel Read Mode
        top_frame.grid_columnconfigure(2, weight=1)  # Averaging Window

        # --- card Dust Clock (sinistra) ----------------------------------- #
        clock_card = ctk.CTkFrame(top_frame)
        clock_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        clock_card.grid_columnconfigure(0, weight=1)

        lbl_clock = ctk.CTkLabel(
            clock_card,
            text="DUST Clock",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        lbl_clock.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.clock_var = ctk.StringVar(value="200")  # default 200 kHz

        rb_50 = ctk.CTkRadioButton(
            clock_card,
            text="50 kHz",
            value="50",
            variable=self.clock_var,
            command=self._on_clock_changed,
        )
        rb_50.grid(row=1, column=0, sticky="w", padx=25, pady=(0, 2))

        rb_200 = ctk.CTkRadioButton(
            clock_card,
            text="200 kHz",
            value="200",
            variable=self.clock_var,
            command=self._on_clock_changed,
        )
        rb_200.grid(row=2, column=0, sticky="w", padx=25, pady=(0, 2))

        rb_400 = ctk.CTkRadioButton(
            clock_card,
            text="400 kHz",
            value="400",
            variable=self.clock_var,
            command=self._on_clock_changed,
        )
        rb_400.grid(row=3, column=0, sticky="w", padx=25, pady=(0, 4))

        # descrizione in corsivo sotto i radio button
        lbl_clock_desc = ctk.CTkLabel(
            clock_card,
            text="Select the clock used by DUST sensor.",
            font=self._desc_font,
        )
        lbl_clock_desc.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 10))

        # --- card Channel Read Mode (centro) ------------------------------ #
        read_card = ctk.CTkFrame(top_frame)
        read_card.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        read_card.grid_columnconfigure(0, weight=1)

        lbl_read = ctk.CTkLabel(
            read_card,
            text="Channel Read Mode",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        lbl_read.grid(row=0, column=0, sticky="n", padx=15, pady=(10, 5))

        # piccolo frame orizzontale per Manual [switch] Auto (molto vicini)
        inner_read = ctk.CTkFrame(read_card, fg_color="transparent")
        inner_read.grid(row=1, column=0, sticky="n", padx=15, pady=(0, 4))

        lbl_manual = ctk.CTkLabel(inner_read, text="Manual")
        lbl_manual.pack(side="left")

        self.read_auto_var = ctk.BooleanVar(value=True)  # default Auto

        switch = ctk.CTkSwitch(
            inner_read,
            text="",
            variable=self.read_auto_var,
            command=self._on_read_mode_changed,
        )
        switch.pack(side="left", padx=(4, 4))

        lbl_auto = ctk.CTkLabel(inner_read, text="Auto")
        lbl_auto.pack(side="left")

        # descrizione in corsivo
        lbl_read_desc = ctk.CTkLabel(
            read_card,
            text="Choose between manual requests and automatic cyclic readout.",
            font=self._desc_font,
        )
        lbl_read_desc.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))

        # --- card Averaging Window (destra) ------------------------------- #
        value_card = ctk.CTkFrame(top_frame)
        value_card.grid(row=0, column=2, sticky="nsew", padx=(10, 0), pady=10)
        value_card.grid_columnconfigure(0, weight=1)
        value_card.grid_columnconfigure(1, weight=0)
        value_card.grid_columnconfigure(2, weight=0)

        lbl_val = ctk.CTkLabel(
            value_card,
            text="Averaging Window",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        lbl_val.grid(row=0, column=0, sticky="n", padx=15, pady=(10, 5), columnspan=3)

        inner = ctk.CTkFrame(value_card, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="n", padx=15, pady=(0, 4), columnspan=3)

        self.v_value = ctk.IntVar(value=4)

        self.v_entry = ctk.CTkEntry(
            inner,
            width=70,
            justify="center",
            textvariable=self.v_value,
        )
        self.v_entry.grid(row=0, column=0, pady=0)
        # invio comando quando l'utente conferma a mano
        self.v_entry.bind("<Return>", self._on_v_entry_commit)
        self.v_entry.bind("<FocusOut>", self._on_v_entry_commit)

        btn_up = ctk.CTkButton(
            inner,
            width=30,
            height=24,
            text="▲",
            command=self._on_v_inc,
        )
        btn_up.grid(row=0, column=1, padx=(5, 2))

        btn_down = ctk.CTkButton(
            inner,
            width=30,
            height=24,
            text="▼",
            command=self._on_v_dec,
        )
        btn_down.grid(row=0, column=2, padx=(2, 0))

        # descrizione in corsivo
        lbl_val_desc = ctk.CTkLabel(
            value_card,
            text="Samples used for the moving-average on particle counts.",
            font=self._desc_font,
        )
        lbl_val_desc.grid(row=2, column=0, sticky="w", padx=15, pady=(30, 0), columnspan=3)

        # ------------------------------------------------------------------ #
        # 2) RIGA INFERIORE: REFRESH RATE + APPEARANCE MODE in un'unica card
        # ------------------------------------------------------------------ #
        display_card = ctk.CTkFrame(
            content,
            fg_color=clock_card.cget("fg_color"),         # stesso colore delle card sopra
            corner_radius=clock_card.cget("corner_radius")
        )
        display_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        display_card.grid_columnconfigure(0, weight=0)
        display_card.grid_columnconfigure(1, weight=0)
        display_card.grid_columnconfigure(2, weight=0)
        display_card.grid_columnconfigure(3, weight=0)
        display_card.grid_columnconfigure(4, weight=1)

        # --- Refresh Rate -------------------------------------------------- #
        lbl_refresh = ctk.CTkLabel(
            display_card,
            text="Refresh Rate",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        lbl_refresh.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        self.refresh_option = ctk.CTkOptionMenu(
            display_card,
            values=["10 Hz", "20 Hz", "30 Hz", "40 Hz", "50 Hz", "60 Hz"],
            command=self._on_refresh_changed,
            width=110,
        )
        self.refresh_option.grid(row=0, column=1, padx=(10, 40), pady=10, sticky="w")

        # --- Appearance Mode ---------------------------------------------- #
        lbl_appearance = ctk.CTkLabel(
            display_card,
            text="Appearance Mode",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        lbl_appearance.grid(row=0, column=2, sticky="w", padx=(0, 10), pady=10)

        self.appearance_option = ctk.CTkOptionMenu(
            display_card,
            values=["Dark", "Light", "System"],
            command=self._on_appearance_changed,
            width=110,
        )
        self.appearance_option.grid(row=0, column=3, padx=(0, 15), pady=10, sticky="w")

        # allinea la combo-box al tema corrente
        try:
            current_mode = ctk.get_appearance_mode()
        except Exception:
            current_mode = "Dark"

        if current_mode in ("Dark", "Light", "System"):
            self.appearance_option.set(current_mode)
        else:
            self.appearance_option.set("Dark")

    # ====================================================================== #
    # Helper per inviare comandi BT
    # ====================================================================== #
    def _send_bt(self, payload: bytes):
        """
        Invia i bytes via Bluetooth usando il controller, se presente.
        Il controller deve avere un metodo `_bt_send_command(payload: bytes)`.
        """
        if self.controller is not None and hasattr(self.controller, "_bt_send_command"):
            try:
                self.controller._bt_send_command(payload)
            except Exception:
                # Non solleviamo errori verso la GUI
                pass

    # ====================================================================== #
    # Callbacks
    # ====================================================================== #
    def _on_clock_changed(self):
        """Invia '5', '20' o '40' a seconda del radio selezionato."""
        val = self.clock_var.get()
        if val == "50":
            self._send_bt(b"5")
        elif val == "200":
            self._send_bt(b"20")
        elif val == "400":
            self._send_bt(b"40")

    def _on_read_mode_changed(self):
        """Invia 'A' se Auto, 'M' se Manual."""
        if self.read_auto_var.get():
            self._send_bt(b"A")
        else:
            self._send_bt(b"M")

    def _on_refresh_changed(self, selection: str):
        """
        Cambia la frequenza di refresh dei grafici aggiornando
        l'intervallo minimo di redraw nel controller.
        """
        if self.controller is None:
            return

        try:
            hz_str = selection.replace("Hz", "").strip()
            hz = float(hz_str)
        except Exception:
            return

        if hz <= 0:
            return

        interval = 1.0 / hz

        # Se il controller ha un metodo dedicato usalo, altrimenti
        # prova a impostare direttamente l'attributo.
        if hasattr(self.controller, "set_refresh_interval"):
            try:
                self.controller.set_refresh_interval(interval)
                return
            except Exception:
                pass

        if hasattr(self.controller, "_min_draw_interval"):
            try:
                self.controller._min_draw_interval = interval
            except Exception:
                pass


    def _on_v_inc(self):
        """Aumenta il valore e invia comando 'V<number>'."""
        value = self._clamp_v(self.v_value.get() + 1)
        self.v_value.set(value)
        self._send_v_command()

    def _on_v_dec(self):
        """Diminuisce il valore e invia comando 'V<number>'."""
        value = self._clamp_v(self.v_value.get() - 1)
        self.v_value.set(value)
        self._send_v_command()

    def _on_v_entry_commit(self, event=None):
        """
        Quando l'utente modifica il numero nell'entry e preme Invio
        o esce dal campo.
        """
        try:
            value = int(self.v_entry.get())
        except ValueError:
            value = self.v_value.get()

        value = self._clamp_v(value)
        self.v_value.set(value)
        self._send_v_command()

    def _clamp_v(self, value: int) -> int:
        """Limita il valore in un range ragionevole (1–99)."""
        if value < 1:
            return 1
        if value > 99:
            return 99
        return value

    def _send_v_command(self):
        """Costruisce e invia il comando 'V<number>'."""
        value = self.v_value.get()
        cmd_str = f"V{value}"
        self._send_bt(cmd_str.encode("ascii"))

    def _on_appearance_changed(self, mode: str):
        """Cambia l'aspetto dell'app (Dark/Light/System)."""
        ctk.set_appearance_mode(mode)

        # Chiede al controller (App) di ridisegnare i grafici personalizzati
        if self.controller is not None and hasattr(self.controller, "on_theme_changed"):
            try:
                self.controller.on_theme_changed()
            except Exception:
                pass

