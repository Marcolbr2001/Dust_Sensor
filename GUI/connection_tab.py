import customtkinter as ctk


class ConnectionTab(ctk.CTkFrame):
    """
    Tab 'Connection': gestione UI per Bluetooth, Serial e log,
    la logica viene gestita dal controller (App).
    """

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- riga superiore (BT + Serial) ---
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Bluetooth
        bt_label = ctk.CTkLabel(top_frame, text="Bluetooth devices (BLE)")
        bt_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.bt_combo = ctk.CTkComboBox(
            top_frame,
            values=["Press Scan"],
        )
        self.bt_combo.set("Press Scan")
        self.bt_combo.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        bt_scan_button = ctk.CTkButton(
            top_frame, text="Scan BT", command=self._on_bt_scan_pressed
        )
        bt_scan_button.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        bt_button = ctk.CTkButton(
            top_frame, text="BT Connect", command=self._on_bt_connect_pressed
        )
        bt_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Serial
        serial_label = ctk.CTkLabel(top_frame, text="Serial port")
        serial_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        self.serial_combo = ctk.CTkComboBox(
            top_frame,
            values=["No ports found"],
        )
        self.serial_combo.set("No ports found")
        self.serial_combo.grid(row=1, column=2, padx=10, pady=5, sticky="ew")

        refresh_button = ctk.CTkButton(
            top_frame, text="Refresh", command=self._on_serial_refresh_pressed
        )
        refresh_button.grid(row=1, column=3, padx=10, pady=5, sticky="ew")

        serial_button = ctk.CTkButton(
            top_frame, text="Serial Connect", command=self._on_serial_connect_pressed
        )
        serial_button.grid(row=2, column=2, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- riga centrale: text-box + pulsante Send ---
        cmd_frame = ctk.CTkFrame(self)
        cmd_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        cmd_frame.grid_columnconfigure(0, weight=1)
        cmd_frame.grid_columnconfigure(1, weight=0)

        self.command_entry = ctk.CTkEntry(
            cmd_frame,
            placeholder_text="Type command to send…",
        )
        self.command_entry.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")

        send_button = ctk.CTkButton(
            cmd_frame,
            text="Send",
            width=100,
            command=self._on_send_pressed,
        )
        send_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="e")

        # --- riga inferiore (log + controlli) ---
        terminal_frame = ctk.CTkFrame(self)
        terminal_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        terminal_frame.grid_rowconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(1, weight=0)
        terminal_frame.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_columnconfigure(1, weight=0)

        # Textbox del monitor
        self.terminal = ctk.CTkTextbox(terminal_frame)
        self.terminal.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Autoscroll checkbox (in basso a sinistra)
        self.autoscroll_var = ctk.BooleanVar(value=True)
        self.autoscroll_check = ctk.CTkCheckBox(
            terminal_frame,
            text="Autoscroll",
            variable=self.autoscroll_var,
        )
        self.autoscroll_check.grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))

        # Clear Monitor (in basso a destra)
        self.clear_button = ctk.CTkButton(
            terminal_frame,
            text="Clear Monitor",
            command=self.clear_log,
            width=120,
        )
        self.clear_button.grid(row=1, column=1, sticky="e", padx=5, pady=(0, 5))

    # --------- metodi helper usati dal controller ---------

    def log(self, text: str):
        self.terminal.insert("end", text + "\n")
        # autoscroll solo se la checkbox è attiva
        if self.autoscroll_var.get():
            self.terminal.see("end")

    def get_bt_selection(self) -> str:
        return self.bt_combo.get()

    def set_bt_devices(self, names):
        if not names:
            self.bt_combo.configure(values=["No DUST_ devices found"])
            self.bt_combo.set("No DUST_ devices found")
        else:
            self.bt_combo.configure(values=names)
            self.bt_combo.set(names[0])

    def set_bt_selection(self, name: str):
        self.bt_combo.set(name)

    def get_serial_selection(self) -> str:
        return self.serial_combo.get()

    def set_serial_ports(self, ports):
        if not ports:
            self.serial_combo.configure(values=["No ports found"])
            self.serial_combo.set("No ports found")
        else:
            self.serial_combo.configure(values=ports)
            self.serial_combo.set(ports[0])

    # --------- callback dei pulsanti (chiamano il controller) ---------

    def _on_bt_scan_pressed(self):
        self.controller._on_bt_scan()

    def _on_bt_connect_pressed(self):
        self.controller._on_bt_connect()

    def _on_serial_refresh_pressed(self):
        self.controller._refresh_serial_ports()

    def _on_serial_connect_pressed(self):
        self.controller._on_serial_connect()

    def _on_send_pressed(self):
        """Legge il testo e chiede al controller di inviarlo via BLE."""
        text = self.command_entry.get().strip()
        self.controller._on_send_text(text)

    def clear_log(self):
        """Cancella il contenuto del monitor/log."""
        self.terminal.delete("1.0", "end")
