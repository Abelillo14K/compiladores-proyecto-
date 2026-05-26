
import json
import io
import os
import sys
import builtins
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog

from nodo_visual import NodoVisual
from nodos_ast import NodoPrograma, NodoAsignacion, NodoEntrada, NodoImprimir, NodoCondicional, NodoMientras
from traductor import Traductor
from semantico import AnalizadorSemantico, AnalizadorAmbitos
from lexico import identificar_tokens


CODIGO_AMBITOS = """int x = 10;
void test(int a) {
    int y = a * 2;
    {
        float x = 5.5;
        y = y + x;
    }
    x = y + 1;
    escribir(z);
}"""


# ventana principal del proyecto
class IDECompilador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("proyec_compiladores - IDE Compilador")
        self.geometry("1380x850")

        self.nodos = {}
        self.lineas_conexion = []
        self.modo_conexion = False
        self.nodo_origen = None
        self.nodo_seleccionado = None
        self.codigo_python_actual = ""
        self.codigo_c_actual = ""
        self.codigo_asm_actual = ""
        self.analizador_ambitos = None

        self.setup_ui()

    # botones y pestañas de la interfaz
    def setup_ui(self):
        self.configure(bg="#e9edf3")
        self.minsize(1180, 720)

        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except Exception:
            pass

        estilo.configure("TFrame", background="#e9edf3")
        estilo.configure("Panel.TFrame", background="#ffffff")
        estilo.configure("TLabel", background="#e9edf3", font=("Segoe UI", 10))
        estilo.configure("TButton", font=("Segoe UI", 9), padding=(7, 4))
        estilo.configure("Accion.TButton", font=("Segoe UI", 9, "bold"), padding=(8, 5))
        estilo.configure("TLabelframe", background="#e9edf3")
        estilo.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))
        estilo.configure("TNotebook", background="#e9edf3", borderwidth=0)
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 9), padding=(10, 5))

        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Nuevo", command=self.nuevo_diagrama)
        filemenu.add_command(label="Guardar diagrama", command=self.guardar_diagrama)
        filemenu.add_command(label="Cargar diagrama", command=self.cargar_diagrama)
        filemenu.add_command(label="Guardar salidas", command=self.guardar_salidas)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=filemenu)
        self.config(menu=menubar)

        contenedor = ttk.Frame(self)
        contenedor.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        main_frame = ttk.PanedWindow(contenedor, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, style="Panel.TFrame")
        right_panel = ttk.Frame(main_frame, style="Panel.TFrame", width=540)
        main_frame.add(left_panel, weight=3)
        main_frame.add(right_panel, weight=2)

        barra_superior = ttk.Frame(left_panel, style="Panel.TFrame")
        barra_superior.pack(fill=tk.X, padx=8, pady=(8, 4))

        grupo_figuras = ttk.LabelFrame(barra_superior, text="Figuras")
        grupo_figuras.pack(side=tk.LEFT, fill=tk.X, padx=(0, 8), anchor="n")
        ttk.Button(grupo_figuras, text="Inicio", width=12, command=lambda: self.agregar_nodo("INICIO")).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(grupo_figuras, text="Proceso", width=12, command=lambda: self.agregar_nodo("PROCESO")).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(grupo_figuras, text="Decision", width=12, command=lambda: self.agregar_nodo("DECISION")).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(grupo_figuras, text="Entrada", width=12, command=lambda: self.agregar_nodo("ENTRADA")).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(grupo_figuras, text="Salida", width=12, command=lambda: self.agregar_nodo("SALIDA")).grid(row=1, column=1, padx=4, pady=4)
        ttk.Button(grupo_figuras, text="Fin", width=12, command=lambda: self.agregar_nodo("FIN")).grid(row=1, column=2, padx=4, pady=4)

        grupo_diagrama = ttk.LabelFrame(barra_superior, text="Diagrama")
        grupo_diagrama.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="n")
        self.btn_conectar = ttk.Button(grupo_diagrama, text="Conectar", width=16, command=self.activar_conexion)
        self.btn_conectar.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(grupo_diagrama, text="Desconectar", width=16, command=self.desconectar_lineas).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(grupo_diagrama, text="Eliminar figura", width=16, command=self.eliminar_figura_seleccionada).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(grupo_diagrama, text="Validar", width=16, command=self.validar_y_mostrar).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(grupo_diagrama, text="Tokens nodo", width=16, command=self.ver_tokens_nodo).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(grupo_diagrama, text="Compilar", width=16, style="Accion.TButton", command=self.compilar).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        for columna in range(3):
            grupo_diagrama.columnconfigure(columna, weight=1)

        marco_canvas = ttk.LabelFrame(left_panel, text="Diagrama de flujo")
        marco_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.canvas = tk.Canvas(marco_canvas, bg="#fbfbfb", highlightthickness=1, highlightbackground="#b7c3cf")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.canvas.bind("<ButtonRelease-1>", lambda event: self.redibujar_conexiones())
        self.bind("<Delete>", lambda event: self.eliminar_figura_seleccionada())

        panel_codigo = ttk.LabelFrame(right_panel, text="Codigo generado y analisis")
        panel_codigo.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        notebook = ttk.Notebook(panel_codigo)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_codigo = self.crear_editor(notebook)
        self.tab_codigo.insert(tk.END, CODIGO_AMBITOS)
        notebook.add(self.tab_codigo, text="Pseudo-C++")

        self.tab_py = self.crear_editor(notebook)
        notebook.add(self.tab_py, text="Python")

        self.tab_c = self.crear_editor(notebook)
        notebook.add(self.tab_c, text="C")

        self.tab_asm = self.crear_editor(notebook)
        notebook.add(self.tab_asm, text="Ensamblador")

        self.tab_tokens = self.crear_editor(notebook)
        notebook.add(self.tab_tokens, text="Tokens")

        self.tab_semantico = self.crear_editor(notebook)
        notebook.add(self.tab_semantico, text="Semantico")

        self.tab_c3d = self.crear_editor(notebook)
        notebook.add(self.tab_c3d, text="C3D")

        exec_frame = ttk.LabelFrame(right_panel, text="Salida y acciones")
        exec_frame.pack(fill=tk.BOTH, expand=False, padx=8, pady=(4, 8))

        botones = ttk.Frame(exec_frame)
        botones.pack(fill=tk.X, padx=5, pady=(6, 3))
        ttk.Button(botones, text="Ejecutar Python", width=18, command=self.ejecutar_python).grid(row=0, column=0, padx=4, pady=3, sticky="ew")
        ttk.Button(botones, text="Analizar Ambitos", width=18, command=self.analizar_ambitos).grid(row=0, column=1, padx=4, pady=3, sticky="ew")
        ttk.Button(botones, text="Compilar C", width=18, command=self.compilar_c).grid(row=0, column=2, padx=4, pady=3, sticky="ew")
        ttk.Button(botones, text="Compilar ASM", width=18, command=self.compilar_asm).grid(row=1, column=0, padx=4, pady=3, sticky="ew")
        ttk.Button(botones, text="Guardar salidas", width=18, command=self.guardar_salidas).grid(row=1, column=1, padx=4, pady=3, sticky="ew")
        for columna in range(3):
            botones.columnconfigure(columna, weight=1)

        self.output_text = scrolledtext.ScrolledText(exec_frame, height=7, state="disabled", bg="#f8fafc", fg="#1c1c1c", font=("Consolas", 10), relief=tk.FLAT)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(3, 6))

        self.estado = tk.StringVar(value="Listo")
        barra_estado = tk.Label(self, textvariable=self.estado, bg="#d7dee8", fg="#24394c", anchor="w", font=("Segoe UI", 9))
        barra_estado.pack(fill=tk.X, side=tk.BOTTOM)

    def crear_editor(self, padre):
        editor = scrolledtext.ScrolledText(
            padre,
            height=10,
            bg="#ffffff",
            fg="#1c1c1c",
            insertbackground="#1c1c1c",
            font=("Consolas", 10),
            relief=tk.FLAT,
            wrap=tk.NONE,
            padx=8,
            pady=8,
        )
        return editor

    # agrega una figura al canvas
    def agregar_nodo(self, tipo):
        x = 130 + (len(self.nodos) % 4) * 170
        y = 100 + (len(self.nodos) // 4) * 110
        nodo = NodoVisual(self.canvas, x, y, tipo)
        self.nodos[nodo.id_unico] = nodo
        self.reasignar_eventos_nodo(nodo)
        self.seleccionar_nodo(nodo)

    def reasignar_eventos_nodo(self, nodo):
        tag = nodo.etiqueta()
        self.canvas.tag_bind(tag, "<Button-1>", lambda event, n=nodo: self.click_nodo(event, n), add="+")
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: self.redibujar_conexiones(), add="+")

    # marca el nodo que esta seleccionado
    def seleccionar_nodo(self, nodo):
        if self.nodo_seleccionado and self.nodo_seleccionado.id_unico in self.nodos:
            self.canvas.itemconfig(self.nodo_seleccionado.id_figura, width=2)
        self.nodo_seleccionado = nodo
        self.canvas.itemconfig(nodo.id_figura, width=4)

    # elimina la figura seleccionada
    def eliminar_figura_seleccionada(self):
        if self.nodo_seleccionado is None:
            self.mostrar_salida("Seleccione una figura para eliminar.")
            return

        id_borrar = self.nodo_seleccionado.id_unico
        nodo = self.nodos.get(id_borrar)
        if nodo is None:
            self.nodo_seleccionado = None
            return

        for otro in self.nodos.values():
            if id_borrar in otro.conexiones:
                otro.conexiones = [id_nodo for id_nodo in otro.conexiones if id_nodo != id_borrar]

        if self.nodo_origen and self.nodo_origen.id_unico == id_borrar:
            self.nodo_origen = None
            self.modo_conexion = False
            self.btn_conectar.config(text="Conectar")

        nodo.eliminar()
        del self.nodos[id_borrar]
        self.nodo_seleccionado = None
        self.redibujar_conexiones()
        self.mostrar_salida("Figura eliminada correctamente.")

    # activa la coneccion de nodos
    def activar_conexion(self):
        self.modo_conexion = not self.modo_conexion
        self.nodo_origen = None
        texto = "Conectando..." if self.modo_conexion else "Conectar"
        self.btn_conectar.config(text=texto)

    # coneccion de nodo a nodo
    def click_nodo(self, event, nodo):
        self.seleccionar_nodo(nodo)
        if not self.modo_conexion:
            return

        if self.nodo_origen is None:
            if nodo.tipo == "FIN":
                self.mostrar_salida("El nodo FIN no debe tener salida.")
                return
            self.nodo_origen = nodo
            self.canvas.itemconfig(nodo.id_figura, width=4)
            return

        origen = self.nodo_origen
        if origen.id_unico == nodo.id_unico:
            self.mostrar_salida("No se puede conectar un nodo consigo mismo.")
            self.canvas.itemconfig(origen.id_figura, width=2)
            self.nodo_origen = None
            return

        if nodo.tipo == "INICIO":
            self.mostrar_salida("No se debe conectar hacia el nodo INICIO.")
            self.canvas.itemconfig(origen.id_figura, width=2)
            self.nodo_origen = None
            return

        maximo = 2 if origen.tipo == "DECISION" else 1
        if len(origen.conexiones) >= maximo and nodo.id_unico not in origen.conexiones:
            self.mostrar_salida("Este nodo ya tiene las salidas necesarias.")
            self.canvas.itemconfig(origen.id_figura, width=2)
            self.nodo_origen = None
            return

        if nodo.id_unico not in origen.conexiones:
            origen.conexiones.append(nodo.id_unico)
        self.canvas.itemconfig(origen.id_figura, width=2)
        self.nodo_origen = None
        self.redibujar_conexiones()

    # borra las conecciones del diagrama
    def desconectar_lineas(self):
        for nodo in self.nodos.values():
            nodo.conexiones = []
        self.nodo_origen = None
        self.modo_conexion = False
        self.btn_conectar.config(text="Conectar")
        self.redibujar_conexiones()
        self.mostrar_salida("Todas las lineas fueron desconectadas.")

    # vuelve a pintar las lineas
    def redibujar_conexiones(self):
        for linea in self.lineas_conexion:
            self.canvas.delete(linea)
        self.lineas_conexion = []

        for nodo in self.nodos.values():
            for posicion, id_destino in enumerate(nodo.conexiones):
                destino = self.nodos.get(id_destino)
                if destino:
                    x1, y1 = nodo.punto_salida_hacia(destino)
                    x2, y2 = destino.punto_entrada_desde(nodo)
                    linea = self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, width=2, fill="black")
                    self.lineas_conexion.append(linea)
                    self.canvas.tag_lower(linea)
                    if nodo.tipo == "DECISION":
                        texto = "SI" if posicion == 0 else "NO"
                        tx = (x1 + x2) / 2
                        ty = (y1 + y2) / 2 - 10
                        etiqueta = self.canvas.create_text(tx, ty, text=texto, font=("Arial", 9, "bold"), fill="blue")
                        self.lineas_conexion.append(etiqueta)

    def nuevo_diagrama(self):
        self.canvas.delete("all")
        self.nodos = {}
        self.lineas_conexion = []
        self.nodo_origen = None
        self.nodo_seleccionado = None
        NodoVisual.contador = 1
        self.limpiar_tabs()

    # guarda el diagrama en json
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

    # carga el diagrama guardado
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

    # revisa que el diagrama tenga buen orden
    def validar_diagrama(self):
        errores = []
        inicios = [n for n in self.nodos.values() if n.tipo == "INICIO"]
        fines = [n for n in self.nodos.values() if n.tipo == "FIN"]

        if len(inicios) != 1:
            errores.append("Debe existir un solo nodo INICIO.")
        if len(fines) != 1:
            errores.append("Debe existir un solo nodo FIN.")

        for nodo in self.nodos.values():
            if nodo.id_unico in nodo.conexiones:
                errores.append(f"El nodo {nodo.id_unico} no puede conectarse consigo mismo.")
            for id_destino in nodo.conexiones:
                if id_destino not in self.nodos:
                    errores.append(f"El nodo {nodo.id_unico} tiene una coneccion perdida.")
            if nodo.tipo == "FIN" and nodo.conexiones:
                errores.append("El nodo FIN no debe tener salida.")
            elif nodo.tipo == "DECISION" and len(nodo.conexiones) not in [1, 2]:
                errores.append(f"La decision {nodo.id_unico} debe tener una salida SI y puede tener una NO.")
            elif nodo.tipo != "FIN" and nodo.tipo != "DECISION" and len(nodo.conexiones) != 1:
                errores.append(f"El nodo {nodo.id_unico} de tipo {nodo.tipo} debe tener una sola salida.")

        if len(inicios) == 1:
            visitados = self.obtener_visitados(inicios[0])
            for nodo in self.nodos.values():
                if nodo.id_unico not in visitados:
                    errores.append(f"El nodo {nodo.id_unico} no esta conectado al flujo principal.")
            if len(fines) == 1 and fines[0].id_unico not in visitados:
                errores.append("El nodo FIN no es alcanzable desde INICIO.")

        return errores

    def obtener_visitados(self, inicio):
        pendientes = [inicio]
        visitados = set()
        while pendientes:
            actual = pendientes.pop()
            if actual.id_unico in visitados:
                continue
            visitados.add(actual.id_unico)
            for id_destino in actual.conexiones:
                destino = self.nodos.get(id_destino)
                if destino:
                    pendientes.append(destino)
        return visitados

    def validar_y_mostrar(self):
        errores = self.validar_diagrama()
        if errores:
            self.mostrar_salida("Errores en el diagrama:\n" + "\n".join(errores))
        else:
            self.mostrar_salida("El diagrama esta bien estructurado.")

    def buscar_inicio(self):
        for nodo in self.nodos.values():
            if nodo.tipo == "INICIO":
                return nodo
        return None

    # arma el ast desde los nodos
    def construir_ast_desde_diagrama(self):
        inicio = self.buscar_inicio()
        if inicio is None:
            raise Exception("Debe existir un nodo INICIO")

        visitados = set()
        sentencias = self.recorrer_desde(inicio, visitados, detener_en_fin=True)
        return NodoPrograma(sentencias)

    # recorre las flechas del diagrama
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
                resultado = self.procesar_decision(actual, visitados)
                sentencias.append(resultado["nodo_ast"])

                if resultado["siguiente"] is not None:
                    actual = resultado["siguiente"]
                    continue
                break

            if actual.conexiones:
                actual = self.nodos.get(actual.conexiones[0])
            else:
                actual = None

        return sentencias

    # revisa si una rama vuelve a la misma decision
    def rama_regresa_a_decision(self, inicio, id_decision):
        pendientes = [inicio]
        visitados = set()

        while pendientes:
            actual = pendientes.pop()
            if actual is None:
                continue
            if actual.id_unico == id_decision:
                return True
            if actual.id_unico in visitados:
                continue
            visitados.add(actual.id_unico)
            for id_destino in actual.conexiones:
                destino = self.nodos.get(id_destino)
                if destino:
                    pendientes.append(destino)
        return False

    # convierte una decision en if o while segun las flechas
    def procesar_decision(self, decision, visitados):
        ramas = []
        for id_destino in decision.conexiones:
            destino = self.nodos.get(id_destino)
            if destino:
                ramas.append(destino)

        ramas_con_retorno = []
        for posicion, rama in enumerate(ramas):
            if self.rama_regresa_a_decision(rama, decision.id_unico):
                ramas_con_retorno.append((posicion, rama))

        if ramas_con_retorno:
            posicion_bucle, nodo_bucle = ramas_con_retorno[0]
            negar = posicion_bucle == 1
            cuerpo = self.recorrer_rama_hasta_retorno(nodo_bucle, decision.id_unico, set(visitados))

            siguiente = None
            for posicion, rama in enumerate(ramas):
                if posicion != posicion_bucle:
                    siguiente = rama
                    break

            return {
                "nodo_ast": NodoMientras(decision.texto, cuerpo, negar),
                "siguiente": siguiente,
            }

        cuerpo_si = []
        cuerpo_no = []
        if len(ramas) >= 1:
            cuerpo_si = self.recorrer_desde(ramas[0], set(visitados), detener_en_fin=False)
        if len(ramas) >= 2:
            cuerpo_no = self.recorrer_desde(ramas[1], set(visitados), detener_en_fin=False)

        return {
            "nodo_ast": NodoCondicional(decision.texto, cuerpo_si, cuerpo_no),
            "siguiente": None,
        }

    # lee el cuerpo del ciclo hasta regresar a la decision
    def recorrer_rama_hasta_retorno(self, nodo, id_decision, visitados):
        sentencias = []
        actual = nodo

        while actual:
            if actual.id_unico == id_decision:
                break
            if actual.id_unico in visitados:
                break
            visitados.add(actual.id_unico)

            if actual.tipo == "FIN":
                break
            if actual.tipo == "PROCESO":
                sentencias.append(NodoAsignacion(actual.texto))
            elif actual.tipo == "ENTRADA":
                sentencias.append(NodoEntrada(actual.texto))
            elif actual.tipo == "SALIDA":
                sentencias.append(NodoImprimir(actual.texto))
            elif actual.tipo == "DECISION":
                resultado = self.procesar_decision(actual, visitados)
                sentencias.append(resultado["nodo_ast"])
                if resultado["siguiente"] is not None:
                    actual = resultado["siguiente"]
                    continue
                break

            if actual.conexiones:
                siguiente = self.nodos.get(actual.conexiones[0])
                if siguiente and siguiente.id_unico == id_decision:
                    break
                actual = siguiente
            else:
                actual = None

        return sentencias

    # compila el diagrama a los lenguajes
    def compilar(self):
        try:
            errores_diagrama = self.validar_diagrama()
            if errores_diagrama:
                raise Exception("Errores en el diagrama:\n" + "\n".join(errores_diagrama))
            programa = self.construir_ast_desde_diagrama()
            semantico = AnalizadorSemantico()
            semantico.analizar_programa(programa)

            traductor = Traductor(programa)
            codigo_py = traductor.traducir_python()
            codigo_c = traductor.traducir_c()
            codigo_asm = traductor.traducir_asm()

            self.codigo_python_actual = codigo_py
            self.codigo_c_actual = codigo_c
            self.codigo_asm_actual = codigo_asm
            self.escribir_tab(self.tab_py, codigo_py)
            self.escribir_tab(self.tab_c, codigo_c)
            self.escribir_tab(self.tab_asm, codigo_asm)
            self.generar_tokens_diagrama()
            self.escribir_tab(self.tab_semantico, self.formatear_tabla_simple(semantico.tabla_simbolos))
            self.escribir_tab(self.tab_c3d, self.generar_c3d_diagrama(programa))
            self.mostrar_salida("Compilacion del diagrama realizada correctamente.")
        except Exception as error:
            self.mostrar_salida(f"Error al compilar:\n{error}")

    def generar_c3d_diagrama(self, programa):
        lineas = []
        contador = {"t": 1, "l": 1}
        self.generar_c3d_sentencias(programa.sentencias, lineas, contador)
        return "\n".join(lineas)

    # genera codigo de tres direcciones sencillo
    def generar_c3d_sentencias(self, sentencias, lineas, contador):
        for sentencia in sentencias:
            nombre = type(sentencia).__name__
            if nombre == "NodoAsignacion":
                temp = f"t{contador['t']}"
                contador["t"] += 1
                lineas.append(f"{temp} = {sentencia.expresion.traducir_py()}")
                lineas.append(f"{sentencia.nombre} = {temp}")
            elif nombre == "NodoEntrada":
                lineas.append(f"leer {sentencia.nombre}")
            elif nombre == "NodoImprimir":
                lineas.append(f"imprimir {sentencia.expresion.traducir_py()}")
            elif nombre == "NodoCondicional":
                l_si = f"L{contador['l']}"
                l_fin = f"L{contador['l'] + 1}"
                contador["l"] += 2
                lineas.append(f"if {sentencia.condicion.traducir_py()} goto {l_si}")
                lineas.append(f"goto {l_fin}")
                lineas.append(f"{l_si}:")
                self.generar_c3d_sentencias(sentencia.cuerpo_verdadero, lineas, contador)
                lineas.append(f"{l_fin}:")
                if sentencia.cuerpo_falso:
                    self.generar_c3d_sentencias(sentencia.cuerpo_falso, lineas, contador)
            elif nombre == "NodoMientras":
                l_inicio = f"L{contador['l']}"
                l_fin = f"L{contador['l'] + 1}"
                contador["l"] += 2
                condicion = sentencia.condicion.traducir_py()
                if sentencia.negar:
                    condicion = f"not ({condicion})"
                lineas.append(f"{l_inicio}:")
                lineas.append(f"if not {condicion} goto {l_fin}")
                self.generar_c3d_sentencias(sentencia.cuerpo, lineas, contador)
                lineas.append(f"goto {l_inicio}")
                lineas.append(f"{l_fin}:")

    # analiza el ejemplo de ambitos
    def analizar_ambitos(self):
        try:
            codigo = self.tab_codigo.get("1.0", tk.END)
            tokens = identificar_tokens(codigo)
            self.escribir_tab(self.tab_tokens, "\n".join(str(token) for token in tokens))
            analizador = AnalizadorAmbitos()
            analizador.analizar_codigo_fuente(codigo)
            self.analizador_ambitos = analizador
            self.codigo_c_actual = analizador.codigo_c
            self.codigo_asm_actual = analizador.codigo_asm
            self.escribir_tab(self.tab_c, analizador.codigo_c)
            self.escribir_tab(self.tab_asm, analizador.codigo_asm)
            self.escribir_tab(self.tab_c3d, "\n".join(analizador.c3d))
            self.escribir_tab(self.tab_semantico, analizador.resumen_final())
            self.mostrar_salida("Analisis de ambitos completado. Revise las pestanas Semantico y C3D.")
        except Exception as error:
            self.mostrar_salida(f"Error al analizar ambitos:\n{error}")

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
            self.mostrar_salida("No hay nodos para analizar.")
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

    # ejecuta el codigo python generado
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

    # compila el diagrama a los lenguajes
    def compilar_c(self):
        if not self.codigo_c_actual.strip():
            self.compilar()
        ruta = self.guardar_archivo_salida("codigo_traducido.c", self.codigo_c_actual)
        if ruta is None:
            return
        exe = os.path.join(os.path.dirname(ruta), "programa_c")
        try:
            proceso = subprocess.run(["gcc", ruta, "-o", exe], capture_output=True, text=True, timeout=15)
            if proceso.returncode == 0:
                self.mostrar_salida(f"Codigo C generado y compilado correctamente:\n{ruta}")
            else:
                self.mostrar_salida("Codigo C generado, pero gcc encontro errores:\n" + proceso.stderr)
        except FileNotFoundError:
            self.mostrar_salida(f"Codigo C guardado en:\n{ruta}\nNo se encontro gcc en el sistema.")
        except Exception as error:
            self.mostrar_salida(f"No se pudo compilar C:\n{error}")

    # compila el diagrama a los lenguajes
    def compilar_asm(self):
        if not self.codigo_asm_actual.strip():
            self.compilar()
        ruta = self.guardar_archivo_salida("salida.asm", self.codigo_asm_actual)
        if ruta is None:
            return
        carpeta = os.path.dirname(ruta)
        objeto = os.path.join(carpeta, "salida.o")
        exe = os.path.join(carpeta, "programa_asm")
        try:
            p1 = subprocess.run(["nasm", "-f", "elf32", ruta, "-o", objeto], capture_output=True, text=True, timeout=15)
            if p1.returncode != 0:
                self.mostrar_salida("ASM generado, pero NASM encontro errores:\n" + p1.stderr)
                return
            p2 = subprocess.run(["ld", "-m", "elf_i386", objeto, "-o", exe], capture_output=True, text=True, timeout=15)
            if p2.returncode == 0:
                self.mostrar_salida(f"Ensamblador generado y enlazado correctamente:\n{ruta}")
            else:
                self.mostrar_salida("NASM genero el objeto, pero ld encontro errores:\n" + p2.stderr)
        except FileNotFoundError:
            self.mostrar_salida(f"ASM guardado en:\n{ruta}\nNo se encontro nasm o ld en el sistema.")
        except Exception as error:
            self.mostrar_salida(f"No se pudo compilar ASM:\n{error}")

    def guardar_archivo_salida(self, nombre, contenido):
        if not contenido.strip():
            self.mostrar_salida("No hay codigo generado para guardar.")
            return None
        carpeta = os.path.join(os.getcwd(), "salidas")
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, nombre)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return ruta

    # guarda los resultados generados
    def guardar_salidas(self):
        try:
            carpeta = os.path.join(os.getcwd(), "salidas")
            os.makedirs(carpeta, exist_ok=True)
            archivos = {
                "codigo_python.py": self.tab_py.get("1.0", tk.END),
                "codigo_traducido.c": self.tab_c.get("1.0", tk.END),
                "salida.asm": self.tab_asm.get("1.0", tk.END),
                "tokens.txt": self.tab_tokens.get("1.0", tk.END),
                "analisis_semantico.txt": self.tab_semantico.get("1.0", tk.END),
                "c3d.txt": self.tab_c3d.get("1.0", tk.END),
            }
            for nombre, contenido in archivos.items():
                with open(os.path.join(carpeta, nombre), "w", encoding="utf-8") as archivo:
                    archivo.write(contenido)
            self.mostrar_salida(f"Salidas guardadas en la carpeta:\n{carpeta}")
        except Exception as error:
            self.mostrar_salida(f"Error al guardar salidas:\n{error}")

    def formatear_tabla_simple(self, tabla):
        lineas = ["TABLA DE SIMBOLOS"]
        for nombre, datos in tabla.items():
            lineas.append(f"{nombre}: {datos}")
        return "\n".join(lineas)

    def escribir_tab(self, tab, texto):
        tab.delete("1.0", tk.END)
        tab.insert(tk.END, texto)

    def mostrar_salida(self, texto):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, texto)
        self.output_text.config(state="disabled")
        if hasattr(self, "estado"):
            primera_linea = texto.strip().split("\n")[0] if texto.strip() else "Listo"
            self.estado.set(primera_linea)

    def limpiar_tabs(self):
        self.codigo_python_actual = ""
        self.codigo_c_actual = ""
        self.codigo_asm_actual = ""
        for tab in [self.tab_py, self.tab_c, self.tab_asm, self.tab_tokens, self.tab_semantico, self.tab_c3d]:
            self.escribir_tab(tab, "")
        self.mostrar_salida("")
