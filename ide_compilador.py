import json
import io
import sys
import builtins
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog

from nodo_visual import NodoVisual
from traductor import TraductorDiagrama


class IDECompilador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IDE Compilador - Diagramas de Flujo")
        self.geometry("1250x820")

        self.nodos = {}
        self.conexiones = []
        self.conexiones_lineas = []
        self.contador_nodos = 0
        self.modo_conexion = False
        self.nodo_origen = None
        self.codigo_python_actual = ""

        self.setup_ui()

    def setup_ui(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuevo", command=self.nuevo)
        filemenu.add_command(label="Guardar", command=self.guardar)
        filemenu.add_command(label="Cargar", command=self.cargar)
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
        ttk.Button(toolbar, text="Inicio", command=lambda: self.agregar_nodo("INICIO")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Fin", command=lambda: self.agregar_nodo("FIN")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Proceso", command=lambda: self.agregar_nodo("PROCESO")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Decisión", command=lambda: self.agregar_nodo("DECISION")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Entrada", command=lambda: self.agregar_nodo("ENTRADA")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Salida", command=lambda: self.agregar_nodo("SALIDA")).pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.btn_conectar = ttk.Button(toolbar, text="Conectar", command=self.activar_conexion)
        self.btn_conectar.pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Eliminar todo", command=self.nuevo).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Compilar", command=self.compilar).pack(side=tk.RIGHT, padx=5)

        ayuda = ttk.Label(left_panel, text="Doble clic para editar | Arrastrar para mover | Conectar: clic en origen y luego destino")
        ayuda.pack(fill=tk.X)

        self.canvas = tk.Canvas(left_panel, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.click_canvas)

        right_panel = ttk.Frame(main_frame, width=430)
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

        self.output_text = scrolledtext.ScrolledText(exec_frame, height=8, state="disabled", bg="#f0f0f0")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_run = ttk.Button(exec_frame, text="Ejecutar Python", command=self.ejecutar_python)
        btn_run.pack(pady=5)

    def agregar_nodo(self, tipo):
        self.contador_nodos += 1
        x = 120 + (self.contador_nodos % 5) * 150
        y = 90 + (self.contador_nodos // 5) * 90

        texto = self.texto_inicial(tipo)
        nodo = NodoVisual(self.canvas, self.contador_nodos, x, y, tipo, texto)
        self.nodos[self.contador_nodos] = nodo
        self.reasignar_eventos_nodo(nodo)

    def texto_inicial(self, tipo):
        if tipo == "INICIO":
            return "inicio"
        if tipo == "FIN":
            return "fin"
        if tipo == "PROCESO":
            return "x = 10"
        if tipo == "DECISION":
            return "x > 5"
        if tipo == "ENTRADA":
            return "x"
        if tipo == "SALIDA":
            return "x"
        return tipo

    def reasignar_eventos_nodo(self, nodo):
        tag = nodo.etiqueta()
        self.canvas.tag_bind(tag, "<Button-1>", lambda event, n=nodo: self.click_nodo(event, n), add="+")
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: self.redibujar_conexiones(), add="+")

    def activar_conexion(self):
        self.modo_conexion = not self.modo_conexion
        self.nodo_origen = None
        if self.modo_conexion:
            self.btn_conectar.config(text="Conectando...")
        else:
            self.btn_conectar.config(text="Conectar")

    def click_nodo(self, event, nodo):
        if not self.modo_conexion:
            return

        if self.nodo_origen is None:
            self.nodo_origen = nodo
            self.canvas.itemconfig(nodo.figura_id, width=4)
        else:
            if self.nodo_origen.id_nodo != nodo.id_nodo:
                self.conectar_nodos(self.nodo_origen.id_nodo, nodo.id_nodo)
            self.canvas.itemconfig(self.nodo_origen.figura_id, width=2)
            self.nodo_origen = None
            self.modo_conexion = False
            self.btn_conectar.config(text="Conectar")

    def click_canvas(self, event):
        pass

    def conectar_nodos(self, origen, destino):
        for conexion in self.conexiones:
            if conexion["origen"] == origen and conexion["destino"] == destino:
                return

        etiqueta = ""
        salidas_origen = [c for c in self.conexiones if c["origen"] == origen]
        if self.nodos[origen].tipo == "DECISION":
            etiqueta = "SI" if len(salidas_origen) == 0 else "NO"

        self.conexiones.append({"origen": origen, "destino": destino, "etiqueta": etiqueta})
        self.redibujar_conexiones()

    def redibujar_conexiones(self):
        for item in self.conexiones_lineas:
            self.canvas.delete(item)
        self.conexiones_lineas.clear()

        for conexion in self.conexiones:
            if conexion["origen"] not in self.nodos or conexion["destino"] not in self.nodos:
                continue
            origen = self.nodos[conexion["origen"]]
            destino = self.nodos[conexion["destino"]]
            linea = self.canvas.create_line(origen.x, origen.y + 30, destino.x, destino.y - 30, arrow=tk.LAST, width=2)
            self.conexiones_lineas.append(linea)

            if conexion.get("etiqueta"):
                tx = (origen.x + destino.x) / 2
                ty = (origen.y + destino.y) / 2
                texto = self.canvas.create_text(tx, ty, text=conexion["etiqueta"], font=("Arial", 9, "bold"), fill="blue")
                self.conexiones_lineas.append(texto)

        for nodo in self.nodos.values():
            self.canvas.tag_raise(nodo.etiqueta())

    def compilar(self):
        try:
            traductor = TraductorDiagrama(self.nodos, self.conexiones)
            ast = traductor.construir_ast()

            codigo_py = ast.traducirPy()
            codigo_c = ast.traducirC()
            codigo_asm = ast.generarCodigo()

            self.codigo_python_actual = codigo_py
            self.poner_texto(self.tab_py, codigo_py)
            self.poner_texto(self.tab_c, codigo_c)
            self.poner_texto(self.tab_asm, codigo_asm)
            self.mostrar_salida("Compilación terminada correctamente.")
        except Exception as error:
            self.mostrar_salida(f"Error: {error}")

    def ejecutar_python(self):
        if not self.codigo_python_actual.strip():
            self.compilar()

        if not self.codigo_python_actual.strip():
            return

        salida = io.StringIO()

        def pedir_dato(mensaje=""):
            valor = simpledialog.askstring("Entrada", mensaje if mensaje else "Ingrese un valor:")
            if valor is None:
                return "0"
            return valor

        sys_stdout_original = sys.stdout
        entrada_original = builtins.input

        try:
            sys.stdout = salida
            builtins.input = pedir_dato
            entorno = {"__builtins__": builtins.__dict__}
            exec(self.codigo_python_actual, entorno)
            resultado = salida.getvalue()
            if resultado.strip() == "":
                resultado = "El programa no imprimió ninguna salida."
            self.mostrar_salida(resultado)
        except Exception as error:
            self.mostrar_salida(f"Error al ejecutar Python: {error}")
        finally:
            sys.stdout = sys_stdout_original
            builtins.input = entrada_original

    def poner_texto(self, widget, texto):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, texto)

    def mostrar_salida(self, texto):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, texto)
        self.output_text.config(state="disabled")

    def nuevo(self):
        self.canvas.delete("all")
        self.nodos.clear()
        self.conexiones.clear()
        self.conexiones_lineas.clear()
        self.contador_nodos = 0
        self.codigo_python_actual = ""
        self.poner_texto(self.tab_py, "")
        self.poner_texto(self.tab_c, "")
        self.poner_texto(self.tab_asm, "")
        self.mostrar_salida("")

    def guardar(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Diagrama JSON", "*.json"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        datos = {
            "contador_nodos": self.contador_nodos,
            "nodos": [nodo.datos() for nodo in self.nodos.values()],
            "conexiones": self.conexiones
        }

        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

        self.mostrar_salida(f"Diagrama guardado en:\n{ruta}")

    def cargar(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Diagrama JSON", "*.json"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            self.nuevo()
            self.contador_nodos = datos.get("contador_nodos", 0)

            for item in datos.get("nodos", []):
                nodo = NodoVisual(
                    self.canvas,
                    item["id"],
                    item["x"],
                    item["y"],
                    item["tipo"],
                    item.get("texto", "")
                )
                self.nodos[item["id"]] = nodo
                self.reasignar_eventos_nodo(nodo)

            self.conexiones = datos.get("conexiones", [])
            self.redibujar_conexiones()
            self.mostrar_salida(f"Diagrama cargado desde:\n{ruta}")
        except Exception as error:
            messagebox.showerror("Error", str(error))
