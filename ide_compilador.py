import json
import io
import sys
import builtins
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog

from nodo_visual import NodoVisual
from nodos_ast import NodoPrograma, NodoAsignacion, NodoEntrada, NodoImprimir, NodoCondicional
from traductor import Traductor
from semantico import AnalizadorSemantico
from lexico import identificar_tokens


class IDECompilador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IDE Compilador - Diagramas de Flujo")
        self.geometry("1250x820")

        self.nodos = {}
        self.lineas_conexion = []
        self.modo_conexion = False
        self.nodo_origen = None
        self.codigo_python_actual = ""

        self.setup_ui()

    def setup_ui(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuevo", command=self.nuevo_diagrama)
        filemenu.add_command(label="Guardar", command=self.guardar_diagrama)
        filemenu.add_command(label="Cargar", command=self.cargar_diagrama)
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
        ttk.Button(toolbar, text="Ver tokens", command=self.ver_tokens_nodo).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Compilar", command=self.compilar).pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(left_panel, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonRelease-1>", lambda event: self.redibujar_conexiones())

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

        self.tab_tokens = scrolledtext.ScrolledText(notebook, height=10)
        notebook.add(self.tab_tokens, text="Tokens")

        exec_frame = ttk.LabelFrame(right_panel, text="Salida de Ejecución")
        exec_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.output_text = scrolledtext.ScrolledText(exec_frame, height=8, state="disabled", bg="#f0f0f0")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Button(exec_frame, text="Ejecutar Python", command=self.ejecutar_python).pack(pady=5)

    def agregar_nodo(self, tipo):
        x = 130 + (len(self.nodos) % 4) * 170
        y = 100 + (len(self.nodos) // 4) * 110
        nodo = NodoVisual(self.canvas, x, y, tipo)
        self.nodos[nodo.id_unico] = nodo
        self.reasignar_eventos_nodo(nodo)

    def reasignar_eventos_nodo(self, nodo):
        tag = nodo.etiqueta()
        self.canvas.tag_bind(tag, "<Button-1>", lambda event, n=nodo: self.click_nodo(event, n), add="+")
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: self.redibujar_conexiones(), add="+")

    def activar_conexion(self):
        self.modo_conexion = not self.modo_conexion
        self.nodo_origen = None
        texto = "Conectando..." if self.modo_conexion else "Conectar"
        self.btn_conectar.config(text=texto)

    def click_nodo(self, event, nodo):
        if not self.modo_conexion:
            return

        if self.nodo_origen is None:
            self.nodo_origen = nodo
            self.canvas.itemconfig(nodo.id_figura, width=4)
        else:
            if self.nodo_origen.id_unico != nodo.id_unico:
                if nodo.id_unico not in self.nodo_origen.conexiones:
                    self.nodo_origen.conexiones.append(nodo.id_unico)
                self.canvas.itemconfig(self.nodo_origen.id_figura, width=2)
                self.nodo_origen = None
                self.redibujar_conexiones()

    def redibujar_conexiones(self):
        for linea in self.lineas_conexion:
            self.canvas.delete(linea)
        self.lineas_conexion = []

        for nodo in self.nodos.values():
            for id_destino in nodo.conexiones:
                destino = self.nodos.get(id_destino)
                if destino:
                    linea = self.canvas.create_line(
                        nodo.x, nodo.y, destino.x, destino.y,
                        arrow=tk.LAST, width=2, fill="black"
                    )
                    self.lineas_conexion.append(linea)
                    self.canvas.tag_lower(linea)

    def nuevo_diagrama(self):
        self.canvas.delete("all")
        self.nodos = {}
        self.lineas_conexion = []
        self.nodo_origen = None
        NodoVisual.contador = 1
        self.limpiar_tabs()

    def guardar_diagrama(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if not ruta:
            return

        datos = {"nodos": [nodo.a_diccionario() for nodo in self.nodos.values()]}
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=4, ensure_ascii=False)

        messagebox.showinfo("Guardar", "Diagrama guardado correctamente")

    def cargar_diagrama(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
        if not ruta:
            return

        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        self.nuevo_diagrama()
        for item in datos.get("nodos", []):
            nodo = NodoVisual(
                self.canvas,
                item["x"],
                item["y"],
                item["tipo"],
                item["texto"],
                item["id"],
                item.get("conexiones", [])
            )
            self.nodos[nodo.id_unico] = nodo
            self.reasignar_eventos_nodo(nodo)

        self.redibujar_conexiones()

    def buscar_inicio(self):
        for nodo in self.nodos.values():
            if nodo.tipo == "INICIO":
                return nodo
        return None

    def construir_ast_desde_diagrama(self):
        inicio = self.buscar_inicio()
        if inicio is None:
            raise Exception("Debe existir un nodo INICIO")

        visitados = set()
        sentencias = self.recorrer_desde(inicio, visitados, detener_en_fin=True)
        return NodoPrograma(sentencias)

    def recorrer_desde(self, nodo, visitados, detener_en_fin=False):
        sentencias = []
        actual = nodo

        while actual:
            if actual.id_unico in visitados:
                break
            visitados.add(actual.id_unico)

            if actual.tipo == "FIN":
                if detener_en_fin:
                    break
                return sentencias

            if actual.tipo == "PROCESO":
                sentencias.append(NodoAsignacion(actual.texto))
            elif actual.tipo == "ENTRADA":
                sentencias.append(NodoEntrada(actual.texto))
            elif actual.tipo == "SALIDA":
                sentencias.append(NodoImprimir(actual.texto))
            elif actual.tipo == "DECISION":
                cuerpo_si = []
                cuerpo_no = []
                if len(actual.conexiones) >= 1:
                    nodo_si = self.nodos.get(actual.conexiones[0])
                    if nodo_si:
                        cuerpo_si = self.recorrer_desde(nodo_si, set(visitados), detener_en_fin=False)
                if len(actual.conexiones) >= 2:
                    nodo_no = self.nodos.get(actual.conexiones[1])
                    if nodo_no:
                        cuerpo_no = self.recorrer_desde(nodo_no, set(visitados), detener_en_fin=False)
                sentencias.append(NodoCondicional(actual.texto, cuerpo_si, cuerpo_no))
                break

            if actual.conexiones:
                actual = self.nodos.get(actual.conexiones[0])
            else:
                actual = None

        return sentencias

    def compilar(self):
        try:
            programa = self.construir_ast_desde_diagrama()
            semantico = AnalizadorSemantico()
            semantico.analizar_programa(programa)

            traductor = Traductor(programa)
            codigo_py = traductor.traducir_python()
            codigo_c = traductor.traducir_c()
            codigo_asm = traductor.traducir_asm()

            self.codigo_python_actual = codigo_py
            self.escribir_tab(self.tab_py, codigo_py)
            self.escribir_tab(self.tab_c, codigo_c)
            self.escribir_tab(self.tab_asm, codigo_asm)
            self.generar_tokens_diagrama()
            self.mostrar_salida("Compilacion realizada correctamente.")
        except Exception as error:
            self.mostrar_salida(f"Error al compilar:\n{error}")

    def generar_tokens_diagrama(self):
        lineas = []
        for nodo in self.nodos.values():
            if nodo.tipo in ["PROCESO", "DECISION", "ENTRADA", "SALIDA"]:
                try:
                    tokens = identificar_tokens(nodo.texto)
                    lineas.append(f"Nodo {nodo.id_unico} - {nodo.tipo}: {nodo.texto}")
                    for token in tokens:
                        lineas.append(f"  {token}")
                    lineas.append("")
                except Exception as error:
                    lineas.append(f"Nodo {nodo.id_unico}: error lexico {error}")
        self.escribir_tab(self.tab_tokens, "\n".join(lineas))

    def ver_tokens_nodo(self):
        if not self.nodos:
            return
        opciones = [f"{n.id_unico} - {n.tipo}: {n.texto}" for n in self.nodos.values()]
        elegido = simpledialog.askstring("Tokens", "Escriba el ID del nodo:\n" + "\n".join(opciones))
        if not elegido:
            return
        try:
            id_nodo = int(elegido.strip())
            nodo = self.nodos[id_nodo]
            tokens = identificar_tokens(nodo.texto)
            resultado = "\n".join(str(token) for token in tokens)
            self.escribir_tab(self.tab_tokens, resultado)
        except Exception as error:
            self.mostrar_salida(f"Error al obtener tokens: {error}")

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

        stdout_original = sys.stdout
        input_original = builtins.input

        try:
            sys.stdout = salida
            builtins.input = pedir_dato
            entorno = {"__builtins__": builtins.__dict__}
            exec(self.codigo_python_actual, entorno)
            resultado = salida.getvalue()
            if resultado.strip() == "":
                resultado = "El programa no imprimio ninguna salida."
            self.mostrar_salida(resultado)
        except Exception as error:
            self.mostrar_salida(f"Error al ejecutar Python: {error}")
        finally:
            sys.stdout = stdout_original
            builtins.input = input_original

    def escribir_tab(self, tab, texto):
        tab.delete("1.0", tk.END)
        tab.insert(tk.END, texto)

    def mostrar_salida(self, texto):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, texto)
        self.output_text.config(state="disabled")

    def limpiar_tabs(self):
        self.codigo_python_actual = ""
        for tab in [self.tab_py, self.tab_c, self.tab_asm, self.tab_tokens]:
            self.escribir_tab(tab, "")
        self.mostrar_salida("")
