import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog


class NodoAST:
    def traducirPy(self): raise NotImplementedError

    def traducirC(self, declaraciones): raise NotImplementedError

    def generarCodigo(self): raise NotImplementedError

    def obtenerVars(self, vars_set): pass


class NodoPrograma(NodoAST):
    def __init__(self, sentencias):
        self.sentencias = sentencias


class NodoAsignacion(NodoAST):
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor


class NodoImprimir(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion


class NodoCondicional(NodoAST):
    def __init__(self, condicion, cuerpo_verdadero, cuerpo_falso=None):
        self.condicion = condicion
        self.cuerpo_verdadero = cuerpo_verdadero
        self.cuerpo_falso = cuerpo_falso if cuerpo_falso else []



class NodoVisual:

    def __init__(self, canvas, x, y, tipo, texto=""):
        self.canvas = canvas
        self.id = None
        self.text_id = None
        self.tipo = tipo
        self.texto = texto
        self.x = x
        self.y = y
        self.conexiones = []
        self.draw()

    def draw(self):
        color = "#ffffff"
        if self.tipo == "INICIO":
            color = "#90EE90"
        elif self.tipo == "FIN":
            color = "#FF6B6B"
        elif self.tipo == "PROCESO":
            color = "#87CEFA"
        elif self.tipo == "DECISION":
            color = "#FFD700"
        elif self.tipo == "ENTRADA":
            color = "#DDA0DD"
        elif self.tipo == "SALIDA":
            color = "#F0E68C"

        if self.tipo in ["INICIO", "FIN"]:
            self.id = self.canvas.create_oval(self.x - 40, self.y - 20, self.x + 40, self.y + 20, fill=color,
                                              outline="black", width=2)
        elif self.tipo == "PROCESO" or self.tipo == "ENTRADA":
            self.id = self.canvas.create_rectangle(self.x - 60, self.y - 20, self.x + 60, self.y + 20, fill=color,
                                                   outline="black", width=2)
        elif self.tipo == "DECISION":
            points = [self.x, self.y - 30, self.x + 60, self.y, self.x, self.y + 30, self.x - 60, self.y]
            self.id = self.canvas.create_polygon(points, fill=color, outline="black", width=2)
        elif self.tipo == "SALIDA":
            self.id = self.canvas.create_rectangle(self.x - 60, self.y - 20, self.x + 60, self.y + 20, fill=color,
                                                   outline="black", width=2)

        self.text_id = self.canvas.create_text(self.x, self.y, text=self.texto, font=("Arial", 10, "bold"))

        # Eventos
        self.canvas.tag_bind(self.id, "<Double-Button-1>", self.editar)
        self.canvas.tag_bind(self.text_id, "<Double-Button-1>", self.editar)

    def editar(self, event=None):
        nuevo_texto = simpledialog.askstring("Editar Nodo", f"Texto para {self.tipo}:", initialvalue=self.texto)
        if nuevo_texto is not None:
            self.texto = nuevo_texto
            self.canvas.itemconfig(self.text_id, text=self.texto)




class IDECompilador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IDE Compilador - Diagramas de Flujo")
        self.geometry("1200x800")

        self.nodos = {}
        self.conexiones_lineas = []
        self.modo_conexion = False
        self.nodo_origen = None

        self.setup_ui()

    def setup_ui(self):
        # Menú
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuevo")
        filemenu.add_command(label="Guardar")
        filemenu.add_command(label="Cargar")
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=filemenu)
        self.config(menu=menubar)


        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        toolbar = ttk.Frame(left_panel)
        toolbar.pack(fill=tk.X, pady=5)

        ttk.Label(toolbar, text="Agregar:").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Inicio").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Fin").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Proceso").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Decisión").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Entrada").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Salida").pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.btn_conectar = ttk.Button(toolbar, text="Conectar")
        self.btn_conectar.pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Compilar").pack(side=tk.RIGHT, padx=5)


        self.canvas = tk.Canvas(left_panel, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)


        right_panel = ttk.Frame(main_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)

        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill=tk.BOTH, expand=True)


        self.tab_py = scrolledtext.ScrolledText(notebook, height=10)
        notebook.add(self.tab_py, text="Python")

        self.tab_c = scrolledtext.ScrolledText(notebook, height=10)
        notebook.add(self.tab_c, text="C")

        self.tab_asm = scrolledtext.ScrolledText(notebook, height=10)
        notebook.add(self.tab_asm, text="Ensamblador")


        exec_frame = ttk.LabelFrame(right_panel, text="Salida de Ejecución")
        exec_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = scrolledtext.ScrolledText(exec_frame, height=8, state='disabled', bg='#f0f0f0')
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_run = ttk.Button(exec_frame, text="Ejecutar Python")
        btn_run.pack(pady=5)


if __name__ == "__main__":
    app = IDECompilador()
    app.mainloop()