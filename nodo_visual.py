from tkinter import simpledialog


# nodo que se dibuja en pantalla
class NodoVisual:
    contador = 1

    def __init__(self, canvas, x, y, tipo, texto="", id_unico=None, conexiones=None):
        self.canvas = canvas
        if id_unico is None:
            self.id_unico = NodoVisual.contador
            NodoVisual.contador += 1
        else:
            self.id_unico = id_unico
            NodoVisual.contador = max(NodoVisual.contador, id_unico + 1)

        self.x = x
        self.y = y
        self.tipo = tipo
        self.texto = texto if texto else self.texto_inicial(tipo)
        self.conexiones = conexiones if conexiones else []
        self.id_figura = None
        self.id_texto = None
        self.mouse_x = 0
        self.mouse_y = 0
        self.dibujar()
        self.asignar_eventos()

    # texto inicial del nodo
    def texto_inicial(self, tipo):
        textos = {
            "INICIO": "Inicio",
            "FIN": "Fin",
            "PROCESO": "x = 10",
            "DECISION": "x > 5",
            "ENTRADA": "x",
            "SALIDA": "x",
        }
        return textos.get(tipo, tipo)

    def etiqueta(self):
        return f"nodo_{self.id_unico}"

    # color por tipo de nodo
    def color(self):
        colores = {
            "INICIO": "#90EE90",
            "FIN": "#FF6B6B",
            "PROCESO": "#87CEFA",
            "DECISION": "#FFD700",
            "ENTRADA": "#DDA0DD",
            "SALIDA": "#F0E68C",
        }
        return colores.get(self.tipo, "#FFFFFF")

    # dibuja la figura
    def dibujar(self):
        tag = self.etiqueta()
        color = self.color()

        if self.tipo in ["INICIO", "FIN"]:
            self.id_figura = self.canvas.create_oval(
                self.x - 50, self.y - 25, self.x + 50, self.y + 25,
                fill=color, outline="black", width=2, tags=(tag,)
            )
        elif self.tipo == "DECISION":
            puntos = [
                self.x, self.y - 40,
                self.x + 75, self.y,
                self.x, self.y + 40,
                self.x - 75, self.y,
            ]
            self.id_figura = self.canvas.create_polygon(
                puntos, fill=color, outline="black", width=2, tags=(tag,)
            )
        elif self.tipo in ["ENTRADA", "SALIDA"]:
            puntos = [
                self.x - 60, self.y - 25,
                self.x + 70, self.y - 25,
                self.x + 60, self.y + 25,
                self.x - 70, self.y + 25,
            ]
            self.id_figura = self.canvas.create_polygon(
                puntos, fill=color, outline="black", width=2, tags=(tag,)
            )
        else:
            self.id_figura = self.canvas.create_rectangle(
                self.x - 70, self.y - 25, self.x + 70, self.y + 25,
                fill=color, outline="black", width=2, tags=(tag,)
            )

        self.id_texto = self.canvas.create_text(
            self.x, self.y, text=self.texto, font=("Arial", 10, "bold"),
            width=120, tags=(tag,)
        )

    # asignar eventos del mouse
    def asignar_eventos(self):
        tag = self.etiqueta()
        self.canvas.tag_bind(tag, "<Button-1>", self.iniciar_movimiento, add="+")
        self.canvas.tag_bind(tag, "<B1-Motion>", self.mover, add="+")
        self.canvas.tag_bind(tag, "<Double-Button-1>", self.editar, add="+")

    def iniciar_movimiento(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    # mueve el nodo
    def mover(self, event):
        dx = event.x - self.mouse_x
        dy = event.y - self.mouse_y
        self.canvas.move(self.etiqueta(), dx, dy)
        self.x += dx
        self.y += dy
        self.mouse_x = event.x
        self.mouse_y = event.y

    # tamaño usado para conectar flechas
    def tamanio(self):
        if self.tipo in ["INICIO", "FIN"]:
            return 50, 25
        if self.tipo == "DECISION":
            return 75, 40
        if self.tipo in ["ENTRADA", "SALIDA"]:
            return 70, 25
        return 70, 25

    # punto donde sale la linea
    def punto_salida_hacia(self, otro):
        return self.punto_en_borde(otro.x, otro.y)

    # punto donde entra la linea
    def punto_entrada_desde(self, otro):
        return self.punto_en_borde(otro.x, otro.y)

    def punto_en_borde(self, x_objetivo, y_objetivo):
        dx = x_objetivo - self.x
        dy = y_objetivo - self.y
        if dx == 0 and dy == 0:
            return self.x, self.y
        ancho, alto = self.tamanio()
        escala_x = ancho / abs(dx) if dx != 0 else 9999
        escala_y = alto / abs(dy) if dy != 0 else 9999
        escala = min(escala_x, escala_y)
        return self.x + dx * escala, self.y + dy * escala

    # cambia el texto del nodo
    def editar(self, event=None):
        nuevo_texto = simpledialog.askstring(
            "Editar Nodo",
            f"Texto para {self.tipo}:",
            initialvalue=self.texto
        )
        if nuevo_texto is not None:
            self.texto = nuevo_texto
            self.canvas.itemconfig(self.id_texto, text=self.texto)

    def eliminar(self):
        self.canvas.delete(self.etiqueta())

    # datos para guardar el nodo
    def a_diccionario(self):
        return {
            "id": self.id_unico,
            "x": self.x,
            "y": self.y,
            "tipo": self.tipo,
            "texto": self.texto,
            "conexiones": self.conexiones,
        }
