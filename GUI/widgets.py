import tkinter as tk
import customtkinter as ctk
from collections import deque
import math
import time


# -------------------------------------------------------------------------
#                      PALETTE COLORI PER I GRAFICI
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
    """Canvas per grafico ADC nel tempo (usato nei canali)."""

    MAX_ADC = 32768       # range teorico ADC (0 .. 32768)
    HALF_RANGE = 2000     # finestra visibile: centro ± 2000 (in bit)

    def __init__(self, master, max_points=100, **kwargs):
        kwargs.setdefault("width", 100)
        kwargs.setdefault("height", 60)
        super().__init__(master, **kwargs)
        self.max_points = max_points
        self.values = deque(maxlen=max_points)

        # modalità di visualizzazione: "bit" oppure "voltage"
        self.display_mode = "bit"

        # Profiling locale del grafico
        self._last_redraw_ms = 0.0
        self._max_redraw_ms = 0.0

        self.bind("<Configure>", self._on_resize)

    def set_display_mode(self, mode: str):
        """Imposta la modalità di visualizzazione ('bit' o 'voltage')."""
        if mode not in ("bit", "voltage"):
            return
        self.display_mode = mode
        self.redraw()

    def _on_resize(self, event):
        self.redraw()

    def add_value(self, value: float):
        """Aggiunge un nuovo valore ADC (in bit)."""
        self.values.append(value)
        self.redraw()

    # ------------------------------------------------------------------ utils

    def _map_y(self, v, vmin, vmax, top, plot_h):
        """Converte un valore in coordinata y canvas."""
        if vmax <= vmin:
            return top + plot_h / 2

        frac = (v - vmin) / (vmax - vmin)
        if frac < 0.0:
            frac = 0.0
        elif frac > 1.0:
            frac = 1.0

        return top + plot_h * (1.0 - frac)

    # ------------------------------------------------------------------ draw

    def redraw(self):
        t0 = time.perf_counter()
        self.delete("all")

        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())

        # margine sinistro più largo per le label numeriche
        left, right, top, bottom = 32, 6, 6, 6
        plot_w = max(1, w - left - right)
        plot_h = max(1, h - top - bottom)

        # ⇩⇩⇩  colori in base al tema  ⇩⇩⇩
        colors = _get_graph_colors()
        bg_color = colors["bg"]
        grid_color = colors["grid"]
        text_color = colors["text"]
        line_color = colors["line"]

        # imposta anche il background del canvas
        self.configure(bg=bg_color)

        # sfondo
        self.create_rectangle(0, 0, w, h, fill=bg_color, outline="")

        # nessun dato → solo griglia vuota
        if not self.values:
            for i in range(1, 5):
                x = left + plot_w * i / 5
                y = top + plot_h * i / 5
                self.create_line(x, top, x, top + plot_h, fill=grid_color)
                self.create_line(left, y, left + plot_w, y, fill=grid_color)

            t1 = time.perf_counter()
            dt_ms = (t1 - t0) * 1000.0
            self._last_redraw_ms = dt_ms
            self._max_redraw_ms = max(self._max_redraw_ms, dt_ms)
            return

        # -----------------------------
        # 1) Valori "validi" (escludo 0 e 32768)
        #     → SEMPRE in bit
        # -----------------------------
        valid_vals = [
            abs(int(v))
            for v in self.values
            if 0 < abs(int(v)) < self.MAX_ADC
        ]

        # se TUTTI sono 0 o MAX_ADC, uso comunque qualcosa per non esplodere
        if not valid_vals:
            valid_vals = [abs(int(v)) for v in self.values]

        center = valid_vals[-1]  # centro (in bit) = ultimo valore valido

        # -----------------------------
        # 2) Finestra centrata su center ± HALF_RANGE (in bit)
        # -----------------------------
        vmin = center - self.HALF_RANGE
        vmax = center + self.HALF_RANGE

        if vmin < 0:
            vmin = 0
            vmax = min(self.MAX_ADC, vmin + 2 * self.HALF_RANGE)
        if vmax > self.MAX_ADC:
            vmax = self.MAX_ADC
            vmin = max(0, vmax - 2 * self.HALF_RANGE)

        if vmax <= vmin:
            vmax = vmin + 1.0

        # -----------------------------
        # 3) Griglia verticale
        # -----------------------------
        for i in range(1, 5):
            x = left + plot_w * i / 5
            self.create_line(x, top, x, top + plot_h, fill=grid_color)

        # -----------------------------
        # 4) Tre linee orizzontali (vmax, center, vmin) con label
        # -----------------------------
        tick_values = [vmax, center, vmin]
        for val in tick_values:
            y = self._map_y(val, vmin, vmax, top, plot_h)
            self.create_line(left, y, left + plot_w, y, fill=grid_color)

            # testo in bit o in volt (1 mV di risoluzione)
            if self.display_mode == "voltage":
                volts = val * 3.3 / self.MAX_ADC
                label_text = f"{volts:.3f}"  # 3 decimali → 1 mV
            else:
                label_text = str(int(round(val)))

            self.create_text(
                left - 4,
                y,
                text=label_text,
                anchor="e",
                fill=text_color,
                font=("Segoe UI", 8),
            )

        # -----------------------------
        # 5) Linea dei dati (sempre in bit)
        #    (saltando esplicitamente 0 e MAX_ADC)
        # -----------------------------
        segment = []  # segmento corrente di punti continui

        n = max(1, len(self.values) - 1)
        for i, raw in enumerate(self.values):
            v_raw = abs(int(raw))

            # SCARTO i valori saturi 0 e MAX_ADC → niente linee orizzontali spurie
            if v_raw <= 0 or v_raw >= self.MAX_ADC:
                # se c'è un segmento attivo, lo disegno e lo resetto
                if len(segment) > 1:
                    flat = [coord for xy in segment for coord in xy]
                    self.create_line(*flat, fill=line_color, width=1.8, smooth=True)
                segment = []
                continue

            v = v_raw  # ancora in bit
            x = left + plot_w * (i / n)
            y = self._map_y(v, vmin, vmax, top, plot_h)
            segment.append((x, y))

        # ultimo segmento (se c'è)
        if len(segment) > 1:
            flat = [coord for xy in segment for coord in xy]
            self.create_line(*flat, fill=line_color, width=1.8, smooth=True)

        # fine profiling
        t1 = time.perf_counter()
        dt_ms = (t1 - t0) * 1000.0
        self._last_redraw_ms = dt_ms
        self._max_redraw_ms = max(self._max_redraw_ms, dt_ms)

        if dt_ms > 10.0:
            print(
                "[PROFILE] TimeSeriesGraph.redraw: "
                f"{dt_ms:.2f} ms (max {self._max_redraw_ms:.2f} ms)"
            )



# -------------------------------------------------------------------------
#                         GLOBAL GRAPH (custom)
# -------------------------------------------------------------------------

class GlobalGraph(TimeSeriesGraph):
    """
    Grafico della tab Global con:
    - asse Y dinamico a tick interi
    - griglia (orizzontale+verticale) sempre visibile
    - stessa scala usata per linea, griglia e label
    """

    def redraw(self):
        self.delete("all")

        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())
        left, right, top, bottom = 6, 6, 6, 6
        plot_w = max(1, w - left - right)
        plot_h = max(1, h - top - bottom)

        colors = _get_graph_colors()
        bg_color = colors["bg"]
        grid_color = colors["grid"]
        line_color = colors["line"]
        text_color = colors["text"]

        # sfondo canvas
        self.configure(bg=bg_color)
        self.create_rectangle(0, 0, w, h, fill=bg_color, outline="")

        # nessun dato → solo griglia vuota
        if not self.values:
            self._draw_empty_grid(left, top, plot_w, plot_h, grid_color)
            return

        # ------------------------------ 1) range dati -----------------------
        ys = list(self.values)
        data_max = max(ys)

        # vogliamo sempre partire da 0 (mai negativo)
        vmin = 0.0

        if data_max <= 0:
            # tutto zero: range minimo [0, 1]
            vmax = 1.0
        else:
            # padding ~10% sopra il valore massimo
            padding = max(1.0, data_max * 0.1)
            vmax = data_max + padding

        # ------------------------------ 2) tick Y interi --------------------
        min_i = math.floor(vmin)
        max_i = math.ceil(vmax)
        span = max_i - min_i
        if span <= 0:
            span = 1

        approx_ticks = 5
        step = max(1, math.ceil(span / approx_ticks))
        ticks = list(range(min_i, max_i + 1, step))

        # ------------------------------ 3) griglia + label Y ----------------
        for t in ticks:
            frac = (t - vmin) / (vmax - vmin)
            frac = max(0.0, min(1.0, frac))
            y = top + plot_h * (1 - frac)

            self.create_line(left, y, left + plot_w, y, fill=grid_color)
            self.create_text(
                left + 5,
                y,
                text=str(t),
                anchor="w",
                fill=text_color,
                font=("Arial", 11),
            )

        # ------------------------------ 4) griglia verticale ----------------
        num_vlines = 6
        for i in range(1, num_vlines):
            x = left + plot_w * (i / num_vlines)
            self.create_line(x, top, x, top + plot_h, fill=grid_color)

        # ------------------------------ 5) linea dati -----------------------
        points = []
        denom = (vmax - vmin) or 1.0
        for i, v in enumerate(self.values):
            x = left + plot_w * (i / max(1, len(self.values) - 1))
            frac = (v - vmin) / denom
            frac = max(0.0, min(1.0, frac))
            y = top + plot_h * (1 - frac)
            points.append((x, y))

        if len(points) > 1:
            flat = [coord for xy in points for coord in xy]
            self.create_line(*flat, fill=line_color, width=1.8, smooth=True)

    # -----------------------------------------------------------------
    #       Griglia mostrata quando non ci sono dati
    # -----------------------------------------------------------------

    def _draw_empty_grid(self, left, top, plot_w, plot_h, grid_color):
        # 5 righe orizzontali
        for i in range(1, 6):
            y = top + plot_h * (i / 6)
            self.create_line(left, y, left + plot_w, y, fill=grid_color)

        # 5 colonne verticali
        for i in range(1, 6):
            x = left + plot_w * (i / 6)
            self.create_line(x, top, x, top + plot_h, fill=grid_color)


# -------------------------------------------------------------------------
#                            CHANNEL PREVIEW
# -------------------------------------------------------------------------

class ChannelPreview(ctk.CTkFrame):
    """
    Piccolo riquadro per ogni canale nella tab Channels.
    Riga unica con "CH X" e "Particles: Y" sopra al mini-grafico.
    Cliccabile con cursore a mano.
    """

    def __init__(self, master, channel_id: int, *args, click_callback=None, **kwargs):
        # rimuovo il parametro personalizzato dai kwargs prima di passare a CTkFrame
        kwargs.pop("click_callback", None)
        super().__init__(master, *args, **kwargs)

        self.channel_id = channel_id
        self._click_callback = click_callback

        # layout interno: riga 0 header (CH + Particles), riga 1 grafico
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ------------------------------ header: "CH X" + "Particles: 0"
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
            text="Particles: 0",
            font=ctk.CTkFont(size=10),
            anchor="e",
        )
        self.particles_label.grid(row=0, column=1, sticky="e", padx=(4, 0))

        # ------------------------------ mini-grafico
        self.graph = TimeSeriesGraph(
            self,
            max_points=100,
            highlightthickness=0,
            height=28,   # altezza parte grafico
        )
        self.graph.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))

        # Rendo il riquadro cliccabile e con cursore "mano"
        if self._click_callback is not None:
            self._make_clickable(self)
            self._set_hand_cursor(self)

    # ------------------------------------------------------------------ click
    def _make_clickable(self, widget):
        """Applica il binding del click al widget e a tutti i figli."""
        widget.bind("<Button-1>", self._on_click, add="+")
        for child in widget.winfo_children():
            self._make_clickable(child)

    def _set_hand_cursor(self, widget):
        """Forza il cursore a 'hand2' su questo widget e su tutti i figli."""
        try:
            widget.configure(cursor="hand2")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_hand_cursor(child)

    def _on_click(self, event):
        if self._click_callback is not None:
            self._click_callback(self.channel_id)

    # ------------------------------------------------------------------ dati
    def update_from_value(self, value: int):
        """Aggiorna il mini-grafico."""
        self.graph.add_value(value)

    def add_value(self, value: int):
        """Alias per compatibilità col resto del codice."""
        self.update_from_value(value)

    def set_display_mode(self, mode: str):
        """Propaga la modalità di visualizzazione (bits/voltage) al mini-grafico."""
        # il TimeSeriesGraph interno è in self.graph
        if hasattr(self, "graph"):
            self.graph.set_display_mode(mode)

    def set_particles(self, particles: int):
        """Aggiorna 'Particles: X' nella riga di intestazione."""
        self.particles_label.configure(text=f"Particles: {particles}")


# -------------------------------------------------------------------------
#                            CHANNEL WINDOW
# -------------------------------------------------------------------------

class ChannelWindow(ctk.CTkToplevel):
    """Finestra per il singolo canale (ADC + particelle)."""

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

        if history:
            for v in history:
                self.graph.add_value(v)

    def update_from_value(self, adc_value: int, particles=None):
        self.graph.add_value(adc_value)

        if particles is not None:
            self.value_label.configure(text=str(particles))
            self.param_labels["Particle Count"].configure(
                text=f"Particle Count: {particles}"
            )
