"""
app_network.py

Main window of the application with the real protein data and the filters.

It reuses the widgets written by Nicolas in app2.py (GrafoVisible,
ListaProteinas, CajaOpciones) WITHOUT changing app2.py: the classes below
inherit from them and only add what was missing:

    NetworkGraph(GrafoVisible)      can receive a new graph after a filter
    ScrollableList(ListaProteinas)  scrolls with the mouse wheel (hundreds of rows)
    FilterPanel(CajaOpciones)       implements the filter methods left empty

Run:
    python scripts/build_network.py   (only the first time, creates datos_app/)
    python scripts/app_network.py
"""

import os
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import app2
    from app2 import CajaOpciones, GrafoVisible, ListaProteinas
except ImportError:
    sys.exit("app2.py (Nicolas) not found in scripts/. Get it from the team repository "
             "(Andrewdmr/DataBioAnalytic) before running this file.")

from graph_algorithms import dfs_components  # noqa: E402
from network_data import (OTHER_COLOR, PATHWAY_COLORS, PATHWAY_LABELS,  # noqa: E402
                          Network, apply_filters)

BG = app2.rgb(app2.FONDO)
TEXT = app2.TEXTO
WHITE = app2.BLANCO
BORDER = app2.BORDE_SUAVE
PANEL_WIDTH = 270
UI_FONT = ("Segoe UI", 10)

ALL_PATHWAYS = "Todas las vias"
EXTRA_GRAVITY = 0.01      # pull to the center for proteins outside the main component

# Default view: neighbours of ESR1 with high confidence (readable on screen)
DEFAULTS = {
    "search": "ESR1",
    "depth": 1,
    "pathway": ALL_PATHWAYS,
    "min_confidence": 0.95,
    "mst_only": False,
    "max_nodes": 80,
}


# ------------------------------------------------------------------
# Graph that can change its content
# ------------------------------------------------------------------
class NetworkGraph(GrafoVisible):

    def __init__(self, master, al_seleccionar=None):
        # GrafoVisible needs at least one node at creation (max() on the degrees),
        # so we start with a hidden placeholder and empty it right away.
        super().__init__(master, {"_": {"nombre": "", "color": BG}}, [], al_seleccionar)
        self.set_graph({}, [])
        # Double click on a node. Tk sends <Double-Button-1> instead of a second
        # <ButtonPress-1>, so the click handlers of app2.py are not disturbed.
        self.on_double = None                       # function(name), set by build_window
        self.bind("<Double-Button-1>", self._on_double)

    def _on_double(self, event):
        name = self._nodo_en(event.x, event.y)
        if name and self.on_double:
            self.arrastrando = None
            self.configure(cursor="")
            self.on_double(name)

    def set_graph(self, nodes, edges):
        """nodes: {id: {"nombre", "color"}}, edges: [(u, v), ...]"""
        self.nodos = nodes
        self.aristas = edges
        degree = {n: 0 for n in nodes}
        for a, b in edges:
            degree[a] += 1
            degree[b] += 1
        self.id_hub = max(nodes, key=degree.get) if nodes else None
        self.seleccionado = None
        self.arrastrando = None
        self.pos, self.vel = {}, {}
        self.delete("grafo")
        # Proteins outside the biggest connected component (isolated ones or
        # small separate groups) get an extra pull to the center, see _paso_fisico
        adj = {n: set() for n in nodes}
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        components = dfs_components(adj)
        self.loose = set().union(*components[1:]) if len(components) > 1 else set()
        self._adapt_scale()
        if nodes and self.zona != (0, 0, 1, 1):   # window already drawn once
            self.agrupar()
        self.sucio = True

    # The physics constants of app2.py were tuned for about 14 proteins.
    # With 100+ proteins the repulsion pushes everything to the borders, so we
    # shrink the scale used by the simulation when there are more nodes.
    # Only self.escala changes, the constants of app2.py stay the same.
    def _adapt_scale(self):
        x0, y0, x1, y1 = self.zona
        base = max(0.5, min(x1 - x0, y1 - y0) / 560.0)
        n = max(len(self.nodos), 1)
        # Dense graphs (many edges per node) are pulled together by the springs,
        # so they get a little more room than sparse ones (like an MST).
        avg_degree = 2.0 * len(self.aristas) / n
        density = max(1.0, (avg_degree / 8.0) ** 0.25)
        self.escala = base * min(1.0, (20.0 / n) ** 0.5) * density

    def _al_redimensionar(self, evento):
        super()._al_redimensionar(evento)
        self._adapt_scale()

    def _paso_fisico(self):
        # In app2.py a protein without links is pushed by all the others and the
        # gravity is too weak to bring it back, so it ends stuck on the border.
        # We add a stronger pull to the center for those proteins only, then run
        # the normal simulation of app2.py.
        cx, cy = self.centro
        for n in getattr(self, "loose", ()):
            if n == self.arrastrando or n not in self.pos:
                continue
            p, v = self.pos[n], self.vel[n]
            v[0] += EXTRA_GRAVITY * (cx - p[0])
            v[1] += EXTRA_GRAVITY * (cy - p[1])
        return super()._paso_fisico()


# ------------------------------------------------------------------
# Protein list with scroll
# ------------------------------------------------------------------
class ScrollableList(ListaProteinas):

    def __init__(self, master, nodes, al_seleccionar=None):
        super().__init__(master, nodes, al_seleccionar)
        self.offset = 0
        self.bind("<MouseWheel>", self._on_wheel)                       # Windows, macOS
        self.bind("<Button-4>", lambda e: self._scroll(-1))             # Linux
        self.bind("<Button-5>", lambda e: self._scroll(1))
        self.bind("<Enter>", lambda e: self.focus_set())
        self.on_double = None                       # function(name), set by build_window
        self.bind("<Double-Button-1>", self._on_double)

    def _on_double(self, event):
        name = self._nodo_en(event.y)
        if name and self.on_double:
            self.on_double(name)

    def set_nodes(self, nodes):
        self.nodos = nodes
        self.seleccionado = None
        self.offset = 0
        self._dibujar()

    def _visible_rows(self):
        return max(1, int((self.winfo_height() - app2.FILA_Y0) / app2.FILA_ALTO) + 1)

    def _scroll(self, step):
        last = max(0, len(self.nodos) - self._visible_rows() + 1)
        self.offset = min(max(self.offset + step, 0), last)
        self._dibujar()

    def _on_wheel(self, event):
        # macOS gives small deltas (1, 2...), Windows gives multiples of 120
        step = -event.delta // 120 if abs(event.delta) >= 120 else -event.delta
        self._scroll(int(step) or (1 if event.delta < 0 else -1))

    def mostrar_seleccion(self, nodo_id):
        # Scroll so that a protein selected in the graph is visible in the list
        self.seleccionado = nodo_id
        if nodo_id in self.nodos:
            i = list(self.nodos).index(nodo_id)
            rows = self._visible_rows()
            if i < self.offset or i >= self.offset + rows - 1:
                self.offset = max(0, i - rows // 2)
        self._dibujar()

    def _dibujar(self):
        self.delete("all")
        ids = list(self.nodos)
        y = app2.FILA_Y0
        for nodo_id in ids[self.offset:self.offset + self._visible_rows()]:
            datos = self.nodos[nodo_id]
            active = nodo_id == self.seleccionado
            self.create_oval(13, y - 4, 21, y + 4, fill=datos["color"], outline="")
            self.create_text(30, y, anchor="w",
                             fill=datos["color"] if active else TEXT,
                             font=self.fuente_negrita if active else self.fuente,
                             text=datos["nombre"])
            y += app2.FILA_ALTO
        if len(ids) > self._visible_rows():
            self.create_text(self.winfo_width() - 8, 10, anchor="e", fill=BORDER,
                             font=("Segoe UI", 8),
                             text=f"{self.offset + 1}-{min(len(ids), self.offset + self._visible_rows())}"
                                  f" / {len(ids)}")

    def _nodo_en(self, y):
        i = round((y - app2.FILA_Y0) / app2.FILA_ALTO)
        if abs(y - (app2.FILA_Y0 + i * app2.FILA_ALTO)) > app2.FILA_ALTO / 2:
            return None
        i += self.offset
        if 0 <= i < len(self.nodos):
            return list(self.nodos)[i]
        return None


# ------------------------------------------------------------------
# Filter panel
# ------------------------------------------------------------------
class FilterPanel(CajaOpciones):

    def __init__(self, master, network, on_result):
        super().__init__(master)
        self.pack_propagate(True)   # grow with the widgets (CajaOpciones fixes 110 px)
        self.net = network
        self.on_result = on_result          # function(FilterResult, focus_name)

        self.search = tk.StringVar(value=DEFAULTS["search"])
        self.depth = tk.IntVar(value=DEFAULTS["depth"])
        self.pathway = tk.StringVar(value=DEFAULTS["pathway"])
        self.min_conf = tk.DoubleVar(value=DEFAULTS["min_confidence"])
        self.mst_only = tk.BooleanVar(value=DEFAULTS["mst_only"])
        self.max_nodes = tk.IntVar(value=DEFAULTS["max_nodes"])

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=10)

        # Search + neighbourhood
        self._label(body, "Proteina central (vacio = ninguna)")
        row = tk.Frame(body, bg=BG)
        row.pack(fill="x")
        entry = tk.Entry(row, textvariable=self.search, width=10, bg="#0b1a30", fg=WHITE,
                         insertbackground=WHITE, relief="flat", highlightthickness=1,
                         highlightbackground=BORDER)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.filtrar_por_proteina_conectada())
        tk.Label(row, text=" vecinos:", bg=BG, fg=TEXT, font=UI_FONT).pack(side="left")
        tk.Spinbox(row, from_=1, to=3, width=2, textvariable=self.depth,
                   command=self.filtrar_por_proteina_conectada).pack(side="left")
        self.hint = tk.Label(body, text="", bg=BG, fg="#ff6b6b", font=("Segoe UI", 9),
                             anchor="w", justify="left", wraplength=PANEL_WIDTH - 60)
        self.hint.pack(fill="x")

        # Pathway
        self._label(body, "Via biologica")
        options = [ALL_PATHWAYS] + list(PATHWAY_LABELS.values())
        # ttk.Combobox is drawn correctly on macOS (tk.OptionMenu text was unreadable)
        menu = ttk.Combobox(body, textvariable=self.pathway, values=options,
                            state="readonly", width=24)
        menu.bind("<<ComboboxSelected>>", lambda e: self.filtrar_por_via())
        menu.pack(fill="x")

        # Confidence
        self._label(body, "Confianza minima STRING")
        tk.Scale(body, from_=0.70, to=0.99, resolution=0.01, orient="horizontal",
                 variable=self.min_conf, bg=BG, fg=TEXT, troughcolor="#0b1a30",
                 highlightthickness=0, length=PANEL_WIDTH - 40,
                 command=lambda _v: None).pack(fill="x")
        # Apply only when the mouse is released, not on every pixel
        body.winfo_children()[-1].bind("<ButtonRelease-1>",
                                       lambda e: self.filtrar_por_umbral_confianza())

        # MST + display limit
        tk.Checkbutton(body, text="Solo MST (Kruskal)", variable=self.mst_only,
                       command=self.mostrar_solo_mst, bg=BG, fg=TEXT, selectcolor=BG,
                       activebackground=BG, activeforeground=TEXT, anchor="w",
                       font=UI_FONT).pack(fill="x", pady=(4, 0))
        row2 = tk.Frame(body, bg=BG)
        row2.pack(fill="x")
        tk.Label(row2, text="Max. proteinas en pantalla", bg=BG, fg=TEXT,
                 font=("Segoe UI", 9)).pack(side="left")
        spin = tk.Spinbox(row2, from_=10, to=300, increment=10, width=5,
                          textvariable=self.max_nodes, command=self.aplicar)
        spin.pack(side="right")
        spin.bind("<Return>", lambda e: self.aplicar())

        # Buttons
        row3 = tk.Frame(body, bg=BG)
        row3.pack(fill="x", pady=6)
        tk.Button(row3, text="Aplicar", command=self.aplicar).pack(side="left")
        tk.Button(row3, text="Limpiar filtros", command=self.limpiar_filtros).pack(side="right")

        # Result summary
        self.status = tk.Label(body, text="", bg=BG, fg=TEXT, font=("Segoe UI", 9),
                               anchor="w", justify="left", wraplength=PANEL_WIDTH - 60)
        self.status.pack(fill="x")

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=TEXT,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(6, 0))

    # ----- methods expected by app2.CajaOpciones -----
    def buscar_proteina(self):
        """Return the exact protein name typed in the box, or None."""
        text = self.search.get()
        if not text.strip():
            return None
        name = self.net.find(text)
        if name is None:
            near = self.net.suggestions(text)
            self.hint.configure(text=f"'{text}' no esta en la red."
                                + (f" Quizas: {', '.join(near)}" if near else ""))
        return name

    def filtrar_por_proteina_conectada(self):
        self.aplicar()

    def filtrar_por_umbral_confianza(self):
        self.aplicar()

    def filtrar_por_via(self):
        self.aplicar()

    def mostrar_solo_mst(self):
        self.aplicar()

    def limpiar_filtros(self):
        self.search.set("")
        self.depth.set(1)
        self.pathway.set(ALL_PATHWAYS)
        self.min_conf.set(0.70)
        self.mst_only.set(False)
        self.aplicar()

    # ----- run all the filters together -----
    def selected_pathway(self):
        label = self.pathway.get()
        for key, value in PATHWAY_LABELS.items():
            if value == label:
                return key
        return None

    def aplicar(self):
        self.hint.configure(text="")
        center = self.buscar_proteina()
        if self.search.get().strip() and center is None:
            return          # unknown protein: keep the current view
        try:
            max_nodes = int(self.max_nodes.get())
        except (tk.TclError, ValueError):
            max_nodes = DEFAULTS["max_nodes"]
        result = apply_filters(self.net,
                               pathway=self.selected_pathway(),
                               min_confidence=round(self.min_conf.get(), 2),
                               center=center,
                               depth=int(self.depth.get()),
                               mst_only=self.mst_only.get(),
                               max_nodes=max_nodes)
        if result.message:
            self.hint.configure(text=result.message)
            return
        text = (f"Mostrando {len(result.nodes)} proteinas y {len(result.edges)} interacciones"
                f"\nCumplen los filtros: {result.total_nodes} proteinas, {result.total_edges} interacciones"
                f"\nComponentes conexas (DFS): {result.components}")
        if result.truncated:
            if center:
                text += (f"\nLimite de {max_nodes}: vecinos mas cercanos y con mayor"
                         f" confianza primero")
            else:
                text += (f"\nLimite de {max_nodes}: proteinas mas asociadas al cancer"
                         f" de mama (Open Targets) primero")
        self.status.configure(text=text)
        self.on_result(result, center)


# ------------------------------------------------------------------
# Window
# ------------------------------------------------------------------
def build_window(window, network):
    window.title("Red de proteinas - cancer de mama")
    window.geometry("1150x720")
    window.minsize(900, 600)
    window.configure(bg=BG)

    header = tk.Frame(window, bg=BG, height=app2.ALTO_ENCABEZADO)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text=f"Red de proteinas - cancer de mama  ({len(network.info)} proteinas,"
                          f" {len(network.edges)} interacciones)",
             bg=BG, fg=TEXT, font=UI_FONT).pack(side="left", padx=17)
    short = {"reparacion_adn": "Semilla ADN", "senalizacion_hormonal": "Semilla hormonal",
             "ciclo_celular": "Semilla ciclo celular"}
    legend = [(short[k], c) for k, c in PATHWAY_COLORS.items()] + [("Otra proteina", OTHER_COLOR)]
    for label, color in reversed(legend):
        tk.Label(header, text=label, bg=BG, fg=TEXT, font=("Segoe UI", 9)).pack(side="right", padx=(2, 12))
        dot = tk.Canvas(header, width=10, height=10, bg=BG, highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        dot.pack(side="right")
    tk.Frame(window, bg=WHITE, height=2).pack(fill="x")

    body = tk.Frame(window, bg=BG)
    body.pack(fill="both", expand=True)
    panel = tk.Frame(body, bg=BG, width=PANEL_WIDTH)
    panel.pack(side="left", fill="y")
    panel.pack_propagate(False)
    tk.Frame(body, bg=WHITE, width=2).pack(side="left", fill="y", pady=(22, 20))

    info = tk.Label(panel, text="", bg=BG, fg=TEXT, font=("Segoe UI", 9), anchor="w",
                    justify="left", wraplength=PANEL_WIDTH - 30)
    protein_list = ScrollableList(panel, {})
    graph = NetworkGraph(body)

    def show_info(name):
        if not name or name not in network.info:
            info.configure(text="Clic en una proteina para ver sus datos")
            return
        d = network.info[name]
        lines = [name,
                 "Vias: " + ", ".join(PATHWAY_LABELS[p] for p in d["pathways"]),
                 f"Interacciones en la red completa: {len(network.adj[name])}",
                 f"Open Targets (globalScore): {d['ot_score']:.3f}"]
        if d["seed_of"]:
            lines.insert(1, "Gen semilla de: " + ", ".join(PATHWAY_LABELS[p] for p in d["seed_of"]))
        info.configure(text="\n".join(lines))

    def on_result(result, focus):
        nodes = {n: {"nombre": n + (" *" if network.is_seed(n) else ""),
                     "color": network.color(n)} for n in result.nodes}
        graph.set_graph(nodes, [(u, v) for u, v, _c in result.edges])
        protein_list.set_nodes(nodes)
        if focus in nodes:
            graph.mostrar_seleccion(focus)
            protein_list.mostrar_seleccion(focus)
        show_info(focus)

    def from_list(name):
        graph.mostrar_seleccion(name)
        show_info(name)

    def from_graph(name):
        protein_list.mostrar_seleccion(name)
        show_info(name)

    panel_filters = FilterPanel(panel, network, on_result)
    panel_filters.pack(fill="x", padx=14, pady=(14, 4))
    info.pack(fill="x", padx=16, pady=(4, 4))
    tk.Label(panel, text="* = gen semilla\ndoble clic = centrar en la proteina", justify="left", bg=BG, fg=TEXT, font=("Segoe UI", 8),
             anchor="w").pack(fill="x", padx=16)
    protein_list.pack(fill="both", expand=True)
    graph.pack(side="left", fill="both", expand=True)

    def recenter(name):
        # Double click (list or graph): the protein becomes the center of the view
        panel_filters.search.set(name)
        panel_filters.filtrar_por_proteina_conectada()

    protein_list.al_seleccionar = from_list
    graph.al_seleccionar = from_graph
    protein_list.on_double = recenter
    graph.on_double = recenter

    # First view once the window has its real size
    window.after(150, panel_filters.aplicar)
    return panel_filters, protein_list, graph


def main():
    try:
        network = Network()
    except FileNotFoundError as error:
        sys.exit(str(error))
    window = tk.Tk()
    build_window(window, network)
    window.mainloop()


if __name__ == "__main__":
    main()
