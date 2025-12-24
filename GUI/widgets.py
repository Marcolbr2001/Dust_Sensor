# widgets.py
import tkinter as tk
import customtkinter as ctk
from collections import deque
import math
import time

# -------------------------------------------------------------------------
#                      PALETTE COLORI
# -------------------------------------------------------------------------

def _get_graph_colors():
    """
    Ritorna i colori da usare per sfondo, griglia, linea e testo
    in base a ctk.get_appearance_mode().
    """
    try:
        mode = ctk.get_appearance_mode()
    except Exception:
        mode = "Dark"

    mode = (mode or "Dark").lower()

    if mode == "light":
        return {
            "bg":   "#f5f5f7",
            "grid": "#d0d0d0",
            "line": "#1f6aa5",
            "text": "#222222",
        }
    else:  # "dark" o altro
        return {
            "bg":   "#1c1c1c",
            "grid": "#333333",
            "line": "#33b5ff",
            "text": "#cccccc",
        }


# -------------------------------------------------------------------------
#                        GENERIC TIME-SERIES GRAPH
# -------------------------------------------------------------------------

class TimeSeriesGraph(tk.Canvas):
    """
    Canvas nativo per grafico ADC.
    Versione ottimizzata con autoscale + 1LSB padding + Parity Check.
    """

    MAX_ADC = 32768

    def __init__(self, master, max_points=100, **kwargs):
        # Default: sfondo scuro se non specificato
        if "bg" not in kwargs:
            kwargs["bg"] = "#1c1c1c"

        kwargs.setdefault("width", 100)
        kwargs.setdefault("height", 60)
        kwargs.setdefault("highlightthickness", 0)

        super().__init__(master, **kwargs)

        self.max_points = max_points
        self.values = deque(maxlen=max_points)

        # modalità di visualizzazione: "bit" oppure "voltage"
        self.display_mode = "bit"

        # Limiter FPS (max 60 FPS)
        self._min_draw_interval = 1.0 / 60.0
        self._last_draw_time = 0.0
        
        # Id per gestire il resize debounce
        self._resize_job = None

        self.bind("<Configure>", self._on_resize)

    def set_display_mode(self, mode: str):
        """Imposta la modalità di visualizzazione ('bit' o 'voltage')."""
        if mode not in ("bit", "voltage"):
            return
        self.display_mode = mode
        self.redraw(force=True)

    def _on_resize(self, event):
        # FIX: Non forzare il redraw immediato su resize per evitare lag
        self.redraw(force=False)

    def add_value(self, value: float):
        """Aggiunge un nuovo valore ADC (in bit)."""
        self.values.append(value)
        self.redraw()

    # ------------------------------------------------------------------ utils

    def _y_to_px(self, v, vmin, vmax, top, plot_h):
        """Converte un valore in coordinata y canvas."""
        if vmax <= vmin:
            return top + plot_h / 2.0

        # Clamp
        if v < vmin: v = vmin
        if v > vmax: v = vmax

        frac = (v - vmin) / (vmax - vmin)
        return top + plot_h * (1.0 - frac)

    @staticmethod
    def _snap_line_y(y, width=1):
        """
        Snap per linee.
        Se width=1 (dispari) -> .5 per nitidezza.
        Se width=2 (pari) -> .0 intero.
        """
        if width % 2 != 0:
            return int(round(y)) + 0.5
        else:
            return int(round(y))

    @staticmethod
    def _snap_text_y(y):
        """Snap per testo (stabilità visiva)."""
        return int(round(y))

    # ------------------------------------------------------------------ draw

    def redraw(self, force=False):
        # Throttle (evita carico eccessivo)
        now = time.perf_counter()
        if (not force) and (now - self._last_draw_time) < self._min_draw_interval:
            return
        self._last_draw_time = now

        # FIX: Controlla se il widget esiste ancora
        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except tk.TclError:
            return

        if w < 2 or h < 2:
            return
            
        # FIX CRITICO: Snapshot dei dati.
        data_snapshot = list(self.values)

        self.delete("all")

        # Margini
        left, right, top, bottom = 35, 5, 5, 5
        plot_w = w - left - right
        plot_h = h - top - bottom

        colors = _get_graph_colors()
        bg_color = colors["bg"]
        grid_color = colors["grid"]
        text_color = colors["text"]
        line_color = colors["line"]

        self.configure(bg=bg_color)

        # -----------------------------
        # CALCOLO LIMITI (AUTOSCALE)
        # -----------------------------
        if not data_snapshot:
            curr_min = 0
            curr_max = 100
        else:
            raw_min = min(data_snapshot)
            raw_max = max(data_snapshot)

            # Pad di 1 LSB sopra e sotto
            curr_min = raw_min - 1
            curr_max = raw_max + 1

        # --- FIX PROPORZIONI ---
        # Assicura che lo span (max - min) sia sempre PARI.
        # Questo garantisce che la linea centrale (Grid Mid) sia un numero INTERO.
        # Evita che il valore 90 appaia sotto la riga del 90 (che in realtà era 90.5).
        if (curr_max - curr_min) % 2 != 0:
            curr_max += 1

        # Clamp ai limiti fisici
        if curr_min < 0: curr_min = 0
        if curr_max > self.MAX_ADC: curr_max = self.MAX_ADC
        
        # Se dopo il clamp lo span è tornato dispari o nullo, pazienza, ma proviamo a tenerlo safe
        if curr_max <= curr_min:
            curr_max = curr_min + 2

        # -----------------------------
        # Disegno Griglia
        # -----------------------------
        # Verticale
        for i in range(1, 5):
            x = left + plot_w * i / 5
            x_line = self._snap_line_y(x, width=1)
            self.create_line(x_line, top, x_line, top + plot_h, fill=grid_color)

        # Orizzontale (valori): Max, Mid, Min
        ticks = [curr_max, (curr_max + curr_min) / 2.0, curr_min]

        for val in ticks:
            y_raw = self._y_to_px(val, curr_min, curr_max, top, plot_h)
            y_line = self._snap_line_y(y_raw, width=1)
            y_text = self._snap_text_y(y_raw)

            self.create_line(left, y_line, left + plot_w, y_line, fill=grid_color)

            # Label testo
            if self.display_mode == "voltage":
                volts = val * 3.3 / self.MAX_ADC
                label_text = f"{volts:.2f}V"
            else:
                label_text = f"{int(round(val))}"

            self.create_text(
                left - 4,
                y_text,
                text=label_text,
                anchor="e",
                fill=text_color,
                font=("Segoe UI", 8),
            )

        # -----------------------------
        # Disegno Linea Dati
        # -----------------------------
        if len(data_snapshot) > 1:
            points = []
            n_vals = len(data_snapshot)
            denom = max(1, n_vals - 1)

            for i, v in enumerate(data_snapshot):
                x = left + plot_w * (i / denom)
                x_line = self._snap_line_y(x, width=1) 

                y_raw = self._y_to_px(v, curr_min, curr_max, top, plot_h)
                y_line = self._snap_line_y(y_raw, width=1)

                points.append(x_line)
                points.append(y_line)
            
            self.create_line(points, fill=line_color, width=1.5)


# -------------------------------------------------------------------------
#                         GLOBAL GRAPH (custom)
# -------------------------------------------------------------------------

class GlobalGraph(TimeSeriesGraph):
    """
    Grafico della tab Global.
    Qui l'autoscale parte preferibilmente da 0.
    """

    def redraw(self, force=False):
        now = time.perf_counter()
        if (not force) and (now - self._last_draw_time) < self._min_draw_interval:
            return
        self._last_draw_time = now

        try:
            w = self.winfo_width()
            h = self.winfo_height()
        except tk.TclError:
            return

        if w < 2 or h < 2:
            return

        # FIX: Snapshot
        data_snapshot = list(self.values)

        self.delete("all")

        left, right, top, bottom = 40, 10, 10, 10
        plot_w = w - left - right
        plot_h = h - top - bottom

        colors = _get_graph_colors()
        self.configure(bg=colors["bg"])
        grid_color = colors["grid"]
        text_color = colors["text"]
        line_color = colors["line"]

        # --- Autoscale ---
        if not data_snapshot:
            curr_min, curr_max = 0, 10
        else:
            raw_max = max(data_snapshot)
            curr_min = 0
            if raw_max <= 0:
                curr_max = 10
            else:
                curr_max = raw_max + (raw_max * 0.1)

        if curr_max <= curr_min:
            curr_max = curr_min + 1

        # --- Griglia Orizzontale (interi) ---
        span = curr_max - curr_min
        step = max(1, math.ceil(span / 5))

        ticks = []
        val = int(math.floor(curr_min))
        # Limite di sicurezza per evitare loop infiniti
        loop_safe = 0
        while val <= curr_max and loop_safe < 50:
            ticks.append(val)
            val += step
            loop_safe += 1

        for t in ticks:
            # Evita di disegnare fuori dal top se l'arrotondamento sfora
            if t > curr_max: 
                continue

            y_raw = self._y_to_px(t, curr_min, curr_max, top, plot_h)
            y_line = self._snap_line_y(y_raw, width=1)
            y_text = self._snap_text_y(y_raw)

            self.create_line(left, y_line, left + plot_w, y_line, fill=grid_color)
            self.create_text(
                left - 5, y_text,
                text=str(int(t)),
                anchor="e",
                fill=text_color,
                font=("Arial", 10)
            )

        # Griglia Verticale
        for i in range(1, 6):
            x = left + plot_w * (i / 6)
            x_line = self._snap_line_y(x, width=1)
            self.create_line(x_line, top, x_line, top + plot_h, fill=grid_color)

        # --- Linea ---
        if len(data_snapshot) > 1:
            points = []
            n_vals = len(data_snapshot)
            denom = max(1, n_vals - 1)
            
            line_width = 2

            for i, v in enumerate(data_snapshot):
                x = left + plot_w * (i / denom)
                # FIX: usa lo snap corretto per width=2
                x_line = self._snap_line_y(x, width=line_width)

                y_raw = self._y_to_px(v, curr_min, curr_max, top, plot_h)
                y_line = self._snap_line_y(y_raw, width=line_width)

                points.append(x_line)
                points.append(y_line)

            self.create_line(points, fill=line_color, width=line_width, smooth=True)


# -------------------------------------------------------------------------
#                            CHANNEL PREVIEW
# -------------------------------------------------------------------------

class ChannelPreview(ctk.CTkFrame):
    """
    Piccolo riquadro per ogni canale nella tab Channels.
    """

    def __init__(self, master, channel_id: int, *args, click_callback=None, **kwargs):
        # FIX: rimosso pop inutile, click_callback è già un argomento esplicito
        super().__init__(master, *args, **kwargs)

        self.channel_id = channel_id
        self._click_callback = click_callback

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="we", padx=6, pady=(2, 1))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        self.ch_label = ctk.CTkLabel(
            header,
            text=f"CH {channel_id}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        )
        self.ch_label.grid(row=0, column=0, sticky="w")

        self.particles_label = ctk.CTkLabel(
            header,
            text="Pt: 0",
            font=ctk.CTkFont(size=10),
            anchor="e",
        )
        self.particles_label.grid(row=0, column=1, sticky="e", padx=(4, 0))

        # Grafico
        self.graph = TimeSeriesGraph(
            self,
            max_points=100,
            highlightthickness=0,
            height=30,
        )
        self.graph.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))

        if self._click_callback is not None:
            self._make_clickable(self)
            self._set_hand_cursor(self)

    def _make_clickable(self, widget):
        # Binds ricorsivi
        widget.bind("<Button-1>", self._on_click, add="+")
        for child in widget.winfo_children():
            self._make_clickable(child)

    def _set_hand_cursor(self, widget):
        try:
            widget.configure(cursor="hand2")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_hand_cursor(child)

    def _on_click(self, event):
        if self._click_callback is not None:
            self._click_callback(self.channel_id)

    def update_from_value(self, value: int):
        self.graph.add_value(value)

    def add_value(self, value: int):
        self.update_from_value(value)

    def set_display_mode(self, mode: str):
        if hasattr(self, "graph"):
            self.graph.set_display_mode(mode)

    def set_particles(self, particles: int):
        self.particles_label.configure(text=f"Pt: {particles}")


# -------------------------------------------------------------------------
#                            CHANNEL WINDOW
# -------------------------------------------------------------------------

class ChannelWindow(ctk.CTkToplevel):
    """Finestra dettagliata singolo canale."""

    def __init__(self, master, channel_id: int, history=None, initial_particles=None):
        super().__init__(master)
        self.title(f"Channel {channel_id}")
        self.geometry("650x400")
        self.minsize(500, 320)

        self.channel_id = channel_id

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsw", padx=(10, 10), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            left_frame,
            text=f"Channel {channel_id}",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.grid(row=0, column=0, pady=(0, 10), sticky="w")

        start_text = "0" if initial_particles is None else str(initial_particles)
        self.value_label = ctk.CTkLabel(
            left_frame,
            text=start_text,
            font=ctk.CTkFont(size=40, weight="bold"),
        )
        self.value_label.grid(row=1, column=0, pady=(0, 15), sticky="w")

        small_font = ctk.CTkFont(size=13)
        self.param_labels = {}
        row_idx = 2
        for name in ["Particle Count", "Events / s", "Noise level"]:
            lab = ctk.CTkLabel(left_frame, text=f"{name}: ---", font=small_font)
            lab.grid(row=row_idx, column=0, sticky="w", pady=(0, 4))
            self.param_labels[name] = lab
            row_idx += 1

        if initial_particles is not None:
            self.param_labels["Particle Count"].configure(
                text=f"Particle Count: {initial_particles}"
            )

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=10)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.graph = TimeSeriesGraph(
            right_frame,
            max_points=100,
            highlightthickness=0,
        )
        self.graph.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # FIX: Caricamento efficiente della history
        if history:
            # Estendi la deque direttamente senza triggerare redraw N volte
            self.graph.values.extend(history)
            # Forza un redraw finale
            self.graph.redraw(force=True)

    def update_from_value(self, adc_value: int, particles=None):
        self.graph.add_value(adc_value)

        if particles is not None:
            self.value_label.configure(text=str(particles))
            self.param_labels["Particle Count"].configure(
                text=f"Particle Count: {particles}"
            )