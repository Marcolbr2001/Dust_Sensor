import customtkinter as ctk
from widgets import GlobalGraph


class VisualTab(ctk.CTkFrame):
    """Tab 'Visual': numero globale a sinistra, grafico a destra."""

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)   # info sinistra
        main_frame.grid_columnconfigure(1, weight=1)   # grafico destra

        # --- colonna sinistra ---
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)
        # layout verticale: titolo (0), numero (1), spazio (2), controlli in basso (3)
        left_frame.grid_rowconfigure(0, weight=0)
        left_frame.grid_rowconfigure(1, weight=0)
        left_frame.grid_rowconfigure(2, weight=0)  # spazio che spinge i bottoni in basso
        left_frame.grid_rowconfigure(3, weight=1)
        left_frame.grid_rowconfigure(4, weight=0)  # controlli in basso

        section_font = ctk.CTkFont(size=20, weight="bold")

        title = ctk.CTkLabel(
            left_frame,
            text="Global Particle Count",
            font=section_font,
        )
        title.grid(row=0, column=0, padx=(10, 10), pady=(10, 10), sticky="w")

        self.global_count_label = ctk.CTkLabel(
            left_frame,
            text="0",
            font=ctk.CTkFont(size=90, weight="bold"),
        )
        self.global_count_label.grid(row=1, column=0, pady=(30, 10), sticky="n")

        # --- parametri sotto il numero (come nell'Advanced/single channel) ---
        params_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        params_frame.grid(row=2, column=0, sticky="nw", padx=(10, 10), pady=(60, 0))
        params_frame.grid_columnconfigure(0, weight=0)  # label
        params_frame.grid_columnconfigure(1, weight=1)  # valore

        small_font = ctk.CTkFont(size=13)
        self.param_labels = {}

        row_idx = 0
        for name in ["Particle Density", "Events / s", "Noise level"]:
            lab_name = ctk.CTkLabel(
                params_frame,
                text=f"{name}:",
                font=small_font,
            )
            lab_name.grid(row=row_idx, column=0, sticky="w", pady=(0, 2), padx=(0, 4))

            lab_val = ctk.CTkLabel(
                params_frame,
                text="---",
                font=small_font,
            )
            lab_val.grid(row=row_idx, column=1, sticky="e", pady=(0, 2))
            self.param_labels[name] = lab_val
            row_idx += 1


        # --- controlli Start/Stop in basso, centrati ---
        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.grid(row=4, column=0, pady=(10, 0), sticky="swe")
        control_frame.grid_columnconfigure(0, weight=1)

        ctrl_label = ctk.CTkLabel(
            control_frame,
            text="Acquisition:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        ctrl_label.grid(row=0, column=0, pady=(0, 5), sticky="n")

        buttons_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, pady=(0, 5), sticky="n")
        buttons_frame.grid_columnconfigure((0, 1), weight=0)

        start_btn = ctk.CTkButton(
            buttons_frame,
            text="▶",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=60,
            command=self._on_start_pressed,
        )
        start_btn.grid(row=0, column=0, padx=6, pady=5)

        stop_btn = ctk.CTkButton(
            buttons_frame,
            text="■",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=60,
            command=self._on_stop_pressed,
        )
        stop_btn.grid(row=0, column=1, padx=6, pady=5)

        # --- colonna destra: grafico ---
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.global_graph = GlobalGraph(
            right_frame,
            max_points=100,
            highlightthickness=0,
            #bg="#1c1c1c",
        )
        self.global_graph.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def update_global(self, particle_count: int):
        """
        Aggiorna il numero globale di particelle e il grafico.
        (asse X = tempo, asse Y = numero particelle)
        """
        # Aggiorna la label grande
        self.global_count_label.configure(text=str(particle_count))

        # Aggiunge il valore al grafico (in ordinata)
        self.global_graph.add_value(particle_count)

    # callback per i pulsanti della tab Visual
    def _on_start_pressed(self):
        self.controller._on_start_acquisition()

    def _on_stop_pressed(self):
        self.controller._on_stop_acquisition()
