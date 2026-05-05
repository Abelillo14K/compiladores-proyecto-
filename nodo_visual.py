from tkinter import simpledialog


class NodoVisual:
    def __init__(self, canvas, id_nodo, x, y, tipo, texto=""):
        self.canvas = canvas
        self.id_nodo = id_nodo
        self.x = x
        self.y = y
        self.tipo = tipo
        self.texto = texto
        self.figura_id = None
        self.texto_id = None
        self.conexiones = []
        self._drag_x = 0
        self._drag_y = 0
        self.dibujar()

    def color(self):
        colores = {
            "INICIO": "#90EE90",
            "FIN": "#FF6B6B",
            "PROCESO": "#87CEFA",
            "DECISION": "#FFD700",
            "ENTRADA": "#DDA0DD",
            "SALIDA": "#F0E68C"
        }
        return colores.get(self.tipo, "#ffffff")

    def etiqueta(self):
        return f"nodo_{self.id_nodo}"

    def dibujar(self):
        tag = self.etiqueta()
        color = self.color()

        if self.tipo in ["INICIO", "FIN"]:
            self.figura_id = self.canvas.create_oval(
                self.x - 45, self.y - 25, self.x + 45, self.y + 25,
                fill=color, outline="black", width=2, tags=(tag, "nodo")
            )
        elif self.tipo == "DECISION":
            puntos = [self.x, self.y - 35, self.x + 70, self.y, self.x, self.y + 35, self.x - 70, self.y]
            self.figura_id = self.canvas.create_polygon(
                puntos, fill=color, outline="black", width=2, tags=(tag, "nodo")
            )
        elif self.tipo in ["ENTRADA", "SALIDA"]:
            puntos = [self.x - 65, self.y - 25, self.x + 75, self.y - 25,
                      self.x + 55, self.y + 25, self.x - 85, self.y + 25]
            self.figura_id = self.canvas.create_polygon(
                puntos, fill=color, outline="black", width=2, tags=(tag, "nodo")
            )
        else:
            self.figura_id = self.canvas.create_rectangle(
                self.x - 70, self.y - 25, self.x + 70, self.y + 25,
                fill=color, outline="black", width=2, tags=(tag, "nodo")
            )

        texto_mostrar = self.texto if self.texto else self.tipo
        self.texto_id = self.canvas.create_text(
            self.x, self.y, text=texto_mostrar, font=("Arial", 9, "bold"), width=120, tags=(tag, "nodo")
        )

        self.canvas.tag_bind(tag, "<Double-Button-1>", self.editar)
        self.canvas.tag_bind(tag, "<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.tag_bind(tag, "<B1-Motion>", self.arrastrar)

    def editar(self, event=None):
        nuevo_texto = simpledialog.askstring(
            "Editar Nodo",
            f"Texto para {self.tipo}:",
            initialvalue=self.texto
        )
        if nuevo_texto is not None:
            self.texto = nuevo_texto
            self.canvas.itemconfig(self.texto_id, text=self.texto if self.texto else self.tipo)

    def iniciar_arrastre(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def arrastrar(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        self.mover(dx, dy)
        self._drag_x = event.x
        self._drag_y = event.y

    def mover(self, dx, dy):
        self.x += dx
        self.y += dy
        self.canvas.move(self.etiqueta(), dx, dy)

    def eliminar(self):
        self.canvas.delete(self.etiqueta())

    def datos(self):
        return {
            "id": self.id_nodo,
            "tipo": self.tipo,
            "texto": self.texto,
            "x": self.x,
            "y": self.y
        }
