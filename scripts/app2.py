
import math
import random
import tkinter as tk
from tkinter import font as tkfont

# DATOS
NODOS = {
    "centro": {"nombre": "Proteína central", "color": "#00e5ff"},
    "p1": {"nombre": "Proteína 1", "color": "#ff0090"},
    "p2": {"nombre": "Proteína 2", "color": "#ffee00"},
    "p3": {"nombre": "Proteína 3", "color": "#8000ff"},
    "p4": {"nombre": "Proteína 4", "color": "#aaff00"},
    "p5": {"nombre": "Proteína 5", "color": "#0044ff"},
    "p6": {"nombre": "Proteína 6", "color": "#00e5ff"},
    "p7": {"nombre": "Proteína 7", "color": "#ffbb00"},
    "p8": {"nombre": "Proteína 8", "color": "#ff1a1a"},
    "p9": {"nombre": "Proteína 9", "color": "#00ff55"},
    "p10": {"nombre": "Proteína 10", "color": "#000000"},
    "p11": {"nombre": "Proteína 11", "color": "#ff00aa"},
    "p12": {"nombre": "Proteína 12", "color": "#00ffff"},
    "p13": {"nombre": "Proteína 13", "color": "#ff8800"},
}
ARISTAS = [("centro", f"p{i}") for i in range(1, 10)]
ARISTAS.extend([("p1", "p2"), ("p1", "p3"), ("p2", "p4"), ("p2", "p5"), ("p3", "p6"), ("p4", "p7"), ("p5", "p8"), ("p6", "p9"), ("p7", "p10")])

# ESTILO
FONDO = (0, 8, 20)          # azul casi negro
BRILLO = (6, 28, 56)        # centro del degradado del grafo
BLANCO = "#ffffff"
TEXTO = "#dfe8f5"
BORDE_SUAVE = "#24405f"
ANCHO_PANEL = 205           # ancho de la columna izquierda (caja de opciones + lista)
ALTO_ENCABEZADO = 36
RADIO_NODO = 6
RADIO_HUB = 8               # el nodo con más conexiones se dibuja un poco más grande
FILA_Y0 = 28                # posición vertical del primer elemento de la lista
FILA_ALTO = 38              # separación entre elementos de la lista
MARGEN = 24                 # distancia mínima de los nodos al borde del grafo

# FISICA DEL GRAFO
INTERVALO_MS = 16
LARGO_RESORTE = 150.0
K_RESORTE = 0.020
K_REPULSION = 9000.0
K_GRAVEDAD = 0.0015
AMORTIGUACION = 0.86
VELOCIDAD_MAX = 4.0
DIST_MIN_REPULSION = 45.0
UMBRAL_REPOSO = 0.03
UMBRAL_ARRASTRE = 4


def rgb(c):
    return "#%02x%02x%02x" % c


def mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# GRAFO VISIBLE
class GrafoVisible(tk.Canvas):

    def __init__(self, master, nodos, aristas, al_seleccionar=None):
        super().__init__(master, bg=rgb(FONDO), highlightthickness=0)
        self.nodos = nodos
        self.aristas = aristas
        self.al_seleccionar = al_seleccionar      # función(id_o_None), la conecta principal()

        self.fuente_negrita = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        grado = {n: 0 for n in nodos}
        for a, b in aristas:
            grado[a] += 1
            grado[b] += 1
        self.id_hub = max(nodos, key=grado.get)

        self.rng = random.Random(7)
        self.seleccionado = None
        self.pos = {}          # id -> [x, y]
        self.vel = {}          # id -> [vx, vy]
        self.zona = (0, 0, 1, 1)
        self.centro = (0.0, 0.0)
        self.escala = 1.0
        self.sucio = True      # hay que redibujar

        # Estado del arrastre
        self.arrastrando = None
        self.offset = (0.0, 0.0)
        self.punto_inicial = (0, 0)
        self.movido = False
        self.estaba_seleccionado = False

        self.bind("<Configure>", self._al_redimensionar)
        self.bind("<ButtonPress-1>", self._al_presionar)
        self.bind("<B1-Motion>", self._al_arrastrar)
        self.bind("<ButtonRelease-1>", self._al_soltar)
        self.bind("<Motion>", self._al_mover)
        self.bind("<Key-r>", lambda e: self.agrupar())
        self.bind("<Key-R>", lambda e: self.agrupar())
        self.focus_set()

        self.after(INTERVALO_MS, self._paso)

    # Lo que otras clases pueden pedirle
    def mostrar_seleccion(self, nodo_id):
        self.seleccionado = nodo_id
        self.sucio = True

    def agrupar(self):
        cx, cy = self.centro
        for nodo_id in self.nodos:
            ang = self.rng.uniform(0, 2 * math.pi)
            r = self.rng.uniform(8, 30)
            self.pos[nodo_id] = [cx + r * math.cos(ang), cy + r * math.sin(ang)]
            self.vel[nodo_id] = [0.0, 0.0]
        self.sucio = True

    # Tamaño de la ventana y posiciones iniciales
    def _al_redimensionar(self, evento):
        w, h = evento.width, evento.height
        if w < 50 or h < 50:
            return
        x0, y0, x1, y1 = MARGEN, MARGEN, w - MARGEN, h - MARGEN
        centro_nuevo = ((x0 + x1) / 2, (y0 + y1) / 2)

        if not self.pos:
            self.zona, self.centro = (x0, y0, x1, y1), centro_nuevo
            self.agrupar()
        else:
            dx, dy = centro_nuevo[0] - self.centro[0], centro_nuevo[1] - self.centro[1]
            for p in self.pos.values():
                p[0] += dx
                p[1] += dy
            self.zona, self.centro = (x0, y0, x1, y1), centro_nuevo

        self.escala = max(0.5, min(x1 - x0, y1 - y0) / 560.0)
        self.delete("fondo")
        self._dibujar_fondo(w, h)
        self.tag_lower("fondo")
        self.sucio = True

    # Simulacion de fuerzas
    def _paso_fisico(self):
        s = self.escala
        k_rep = K_REPULSION * s ** 3
        largo = LARGO_RESORTE * s
        dist_min = DIST_MIN_REPULSION * s
        v_max = VELOCIDAD_MAX * s
        ids = list(self.nodos)
        fuerza = {n: [0.0, 0.0] for n in ids}

        #separacion entre todos los pares de nodos
        for i in range(len(ids)):
            a = ids[i]
            xa, ya = self.pos[a]
            for j in range(i + 1, len(ids)):
                b = ids[j]
                dx, dy = xa - self.pos[b][0], ya - self.pos[b][1]
                d2 = dx * dx + dy * dy
                if d2 < 1e-6:                      # superpuestos exactamente: empujón al azar
                    ang = self.rng.uniform(0, 2 * math.pi)
                    dx, dy, d2 = math.cos(ang), math.sin(ang), 1.0
                d = math.sqrt(d2)
                f = k_rep / max(d2, dist_min * dist_min)
                fx, fy = f * dx / d, f * dy / d
                fuerza[a][0] += fx
                fuerza[a][1] += fy
                fuerza[b][0] -= fx
                fuerza[b][1] -= fy

        # 2) Resortes en las aristas
        for a, b in self.aristas:
            dx, dy = self.pos[b][0] - self.pos[a][0], self.pos[b][1] - self.pos[a][1]
            d = math.hypot(dx, dy) or 1e-6
            f = K_RESORTE * (d - largo)
            fx, fy = f * dx / d, f * dy / d
            fuerza[a][0] += fx
            fuerza[a][1] += fy
            fuerza[b][0] -= fx
            fuerza[b][1] -= fy

        # 3) Gravedad suave hacia el centro + integración
        x0, y0, x1, y1 = self.zona
        cx, cy = self.centro
        rapido = 0.0
        for n in ids:
            if n == self.arrastrando:
                self.vel[n] = [0.0, 0.0]          # el nodo agarrado lo controla el mouse
                continue
            p, v, f = self.pos[n], self.vel[n], fuerza[n]
            f[0] += K_GRAVEDAD * (cx - p[0])
            f[1] += K_GRAVEDAD * (cy - p[1])
            v[0] = (v[0] + f[0]) * AMORTIGUACION
            v[1] = (v[1] + f[1]) * AMORTIGUACION
            vel = math.hypot(v[0], v[1])
            if vel > v_max:
                v[0] *= v_max / vel
                v[1] *= v_max / vel
                vel = v_max
            p[0] = min(max(p[0] + v[0], x0), x1)
            p[1] = min(max(p[1] + v[1], y0), y1)
            rapido = max(rapido, vel)
        return rapido

    def _paso(self):
        if self.pos:
            rapido = self._paso_fisico()
            if rapido > UMBRAL_REPOSO * self.escala or self.sucio:
                self._dibujar_grafo()
                self.sucio = False
        self.after(INTERVALO_MS, self._paso)

    # Dibujo
    def _radio(self, nodo_id):
        return RADIO_HUB if nodo_id == self.id_hub else RADIO_NODO

    def _dibujar_fondo(self, w, h):
        cx, cy = w / 2, h / 2
        radio_max = max(w, h) * 0.55
        pasos = 24
        for i in range(pasos):
            r = radio_max * (1 - i / pasos)
            color = rgb(mezclar(FONDO, BRILLO, i / (pasos - 1)))
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                             fill=color, outline="", tags="fondo")

    def _dibujar_grafo(self):
        self.delete("grafo")
        if not self.pos:
            return
        sel = self.seleccionado

        for a, b in self.aristas:
            xa, ya = self.pos[a]
            xb, yb = self.pos[b]
            if sel in (a, b):
                otro = b if sel == a else a
                color = self.nodos[otro]["color"] if sel == a else self.nodos[sel]["color"]
                self.create_line(xa, ya, xb, yb, fill=color, width=3, tags="grafo")
            else:
                self.create_line(xa, ya, xb, yb, fill=BLANCO, width=1.5, tags="grafo")

        for nodo_id, datos in self.nodos.items():
            x, y = self.pos[nodo_id]
            r = self._radio(nodo_id)
            if nodo_id == self.id_hub:
                self.create_oval(x - r - 4, y - r - 4, x + r + 4, y + r + 4,
                                 outline=datos["color"], dash=(2, 2), width=1, tags="grafo")
            if nodo_id == sel:
                self.create_oval(x - r - 7, y - r - 7, x + r + 7, y + r + 7,
                                 outline=BLANCO, width=2, tags="grafo")
            self.create_oval(x - r, y - r, x + r, y + r, fill=datos["color"],
                             outline="", tags="grafo")
            if nodo_id == sel:
                self.create_text(x + r + 12, y - r - 8, anchor="w", fill=BLANCO,
                                 font=self.fuente_negrita, text=datos["nombre"], tags="grafo")

    # Mouse
    def _nodo_en(self, x, y):
        for nodo_id in reversed(list(self.nodos)):
            nx_, ny_ = self.pos.get(nodo_id, (-999, -999))
            r = self._radio(nodo_id) + 6
            if (x - nx_) ** 2 + (y - ny_) ** 2 <= r * r:
                return nodo_id
        return None

    def _cambiar_seleccion(self, nodo_id):
        self.seleccionado = nodo_id
        self.sucio = True
        if self.al_seleccionar:
            self.al_seleccionar(nodo_id)

    def _al_presionar(self, evento):
        self.focus_set()
        nodo = self._nodo_en(evento.x, evento.y)
        if nodo is None:
            if self.seleccionado is not None:
                self._cambiar_seleccion(None)
            return
        # Mantener el clic sobre un nodo: se selecciona y empieza a seguir al mouse
        self.estaba_seleccionado = (nodo == self.seleccionado)
        self.arrastrando = nodo
        px, py = self.pos[nodo]
        self.offset = (px - evento.x, py - evento.y)
        self.punto_inicial = (evento.x, evento.y)
        self.movido = False
        self.configure(cursor="fleur")
        if not self.estaba_seleccionado:
            self._cambiar_seleccion(nodo)

    def _al_arrastrar(self, evento):
        if self.arrastrando is None:
            return
        if not self.movido:
            if math.hypot(evento.x - self.punto_inicial[0],
                          evento.y - self.punto_inicial[1]) < UMBRAL_ARRASTRE:
                return
            self.movido = True
        x0, y0, x1, y1 = self.zona
        p = self.pos[self.arrastrando]
        p[0] = min(max(evento.x + self.offset[0], x0), x1)
        p[1] = min(max(evento.y + self.offset[1], y0), y1)
        self.sucio = True

    def _al_soltar(self, _evento):
        if self.arrastrando is None:
            return
        if not self.movido and self.estaba_seleccionado:
            self._cambiar_seleccion(None)
        self.arrastrando = None
        self.configure(cursor="")

    def _al_mover(self, evento):
        if self.arrastrando is not None:
            return
        self.configure(cursor="hand2" if self._nodo_en(evento.x, evento.y) else "")


# LISTA DE PROTEÍNAS
class ListaProteinas(tk.Canvas):

    def __init__(self, master, nodos, al_seleccionar=None):
        super().__init__(master, bg=rgb(FONDO), highlightthickness=0)
        self.nodos = nodos
        self.al_seleccionar = al_seleccionar      # función(id_o_None), la conecta principal()
        self.seleccionado = None

        self.fuente = tkfont.Font(family="Segoe UI", size=11)
        self.fuente_negrita = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        self.bind("<Configure>", lambda e: self._dibujar())
        self.bind("<ButtonPress-1>", self._al_presionar)
        self.bind("<Motion>", self._al_mover)

    # Lo que otras clases pueden pedirle
    def mostrar_seleccion(self, nodo_id):
        self.seleccionado = nodo_id
        self._dibujar()

    def _dibujar(self):
        self.delete("all")
        y = FILA_Y0
        for nodo_id, datos in self.nodos.items():
            activo = nodo_id == self.seleccionado
            if activo:
                self.create_oval(13, y - 4, 21, y + 4, fill=datos["color"], outline="")
            self.create_text(30 if activo else 17, y, anchor="w",
                             fill=datos["color"] if activo else TEXTO,
                             font=self.fuente_negrita if activo else self.fuente,
                             text=datos["nombre"])
            y += FILA_ALTO

    def _nodo_en(self, y):
        i = round((y - FILA_Y0) / FILA_ALTO)
        if 0 <= i < len(self.nodos) and abs(y - (FILA_Y0 + i * FILA_ALTO)) <= FILA_ALTO / 2:
            return list(self.nodos)[i]
        return None

    def _al_presionar(self, evento):
        nodo = self._nodo_en(evento.y)
        nuevo = None if nodo in (None, self.seleccionado) else nodo
        self.seleccionado = nuevo
        self._dibujar()
        if self.al_seleccionar:
            self.al_seleccionar(nuevo)

    def _al_mover(self, evento):
        self.configure(cursor="hand2" if self._nodo_en(evento.y) else "")


# CAJA DE OPCIONES
class CajaOpciones(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bg=rgb(FONDO), height=110,
                         highlightthickness=1, highlightbackground=BORDE_SUAVE)
        self.pack_propagate(False)
        tk.Label(self, text="Filtros", bg=rgb(FONDO), fg=TEXTO,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=8)

    def buscar_proteina(self):
        pass

    def filtrar_por_proteina_conectada(self):
        pass

    def filtrar_por_umbral_confianza(self):
        pass

    def filtrar_por_via(self):
        pass

    def mostrar_solo_mst(self):
        pass

    def limpiar_filtros(self):
        pass


# ARMADO DE LA VENTANA
def construir(ventana):
    ventana.title("Red de proteínas - cáncer de mama (demo)")
    ventana.geometry("1000x600")
    ventana.minsize(700, 450)
    ventana.configure(bg=rgb(FONDO))

    encabezado = tk.Frame(ventana, bg=rgb(FONDO), height=ALTO_ENCABEZADO)
    encabezado.pack(fill="x")
    encabezado.pack_propagate(False)
    tk.Label(encabezado, text="Red de proteínas · cáncer de mama (demo)", bg=rgb(FONDO),
             fg=TEXTO, font=("Segoe UI", 10)).pack(side="left", padx=17)
    tk.Frame(ventana, bg=BLANCO, height=2).pack(fill="x")

    cuerpo = tk.Frame(ventana, bg=rgb(FONDO))
    cuerpo.pack(fill="both", expand=True)

    panel = tk.Frame(cuerpo, bg=rgb(FONDO), width=ANCHO_PANEL)
    panel.pack(side="left", fill="y")
    panel.pack_propagate(False)

    tk.Frame(cuerpo, bg=BLANCO, width=2).pack(side="left", fill="y", pady=(22, 20))

    caja = CajaOpciones(panel)
    caja.pack(fill="x", padx=14, pady=(14, 4))
    lista = ListaProteinas(panel, NODOS)
    lista.pack(fill="both", expand=True)

    grafo = GrafoVisible(cuerpo, NODOS, ARISTAS)
    grafo.pack(side="left", fill="both", expand=True)

    lista.al_seleccionar = grafo.mostrar_seleccion
    grafo.al_seleccionar = lista.mostrar_seleccion
    return caja, lista, grafo


def principal():
    ventana = tk.Tk()
    construir(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    principal()
