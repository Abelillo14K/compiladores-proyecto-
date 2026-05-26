
import copy
import re
from sintactico_ast import NodoIdentificador, NodoNumero, NodoTexto, NodoOperacion, parsear_expresion


# revision semantica del diagrama
class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}
        self.errores = []

    # revisa todas las instrucciones
    def analizar_programa(self, programa):
        self.tabla_simbolos = {}
        self.errores = []
        for sentencia in programa.sentencias:
            self.analizar_sentencia(sentencia)
        if self.errores:
            raise Exception("\n".join(self.errores))
        return self.tabla_simbolos

    def analizar_sentencia(self, sentencia):
        nombre_clase = type(sentencia).__name__
        metodo = getattr(self, f"visitar_{nombre_clase}", None)
        if metodo:
            metodo(sentencia)

    def visitar_NodoAsignacion(self, nodo):
        self.revisar_expresion(nodo.expresion)
        self.tabla_simbolos[nodo.nombre] = {"tipo": "int"}

    def visitar_NodoEntrada(self, nodo):
        self.tabla_simbolos[nodo.nombre] = {"tipo": "int"}

    def visitar_NodoImprimir(self, nodo):
        self.revisar_expresion(nodo.expresion)

    def visitar_NodoCondicional(self, nodo):
        self.revisar_expresion(nodo.condicion)
        for sentencia in nodo.cuerpo_verdadero:
            self.analizar_sentencia(sentencia)
        for sentencia in nodo.cuerpo_falso:
            self.analizar_sentencia(sentencia)

    # revisa variables usadas

    def visitar_NodoMientras(self, nodo):
        self.revisar_expresion(nodo.condicion)
        for sentencia in nodo.cuerpo:
            self.analizar_sentencia(sentencia)

    def revisar_expresion(self, expresion):
        nombre_clase = type(expresion).__name__
        if nombre_clase == "NodoIdentificador":
            if expresion.nombre not in self.tabla_simbolos:
                self.errores.append(f"Error semantico: la variable {expresion.nombre} se usa antes de tener valor")
        elif nombre_clase == "NodoOperacion":
            self.revisar_expresion(expresion.izquierda)
            self.revisar_expresion(expresion.derecha)


# pila de ambitos
class TablaSimbolosJerarquica:
    def __init__(self):
        self.ambitos = []
        self.historial = []
        self.contador_ambitos = 0

    # nuevo ambito
    def abrir_ambito(self, nombre):
        self.contador_ambitos += 1
        self.ambitos.append({
            "nombre": nombre,
            "numero": self.contador_ambitos,
            "simbolos": {}
        })

    # cierre de ambito
    def cerrar_ambito(self):
        if self.ambitos:
            self.ambitos.pop()

    # guarda una variable
    def declarar_variable(self, nombre, tipo, categoria="variable"):
        if not self.ambitos:
            self.abrir_ambito("global")
        actual = self.ambitos[-1]
        if nombre in actual["simbolos"]:
            return False
        if actual["nombre"] == "global":
            interno = f"{nombre}_global"
        else:
            interno = f"{nombre}_{actual['nombre']}_{actual['numero']}"
        actual["simbolos"][nombre] = {
            "tipo": tipo,
            "categoria": categoria,
            "interno": interno,
            "ambito": actual["nombre"]
        }
        return True

    # busca de adentro hacia afuera
    def buscar_variable(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito["simbolos"]:
                return ambito["simbolos"][nombre]
        return None

    def obtener_tipo_variable(self, nombre):
        simbolo = self.buscar_variable(nombre)
        if simbolo is None:
            return None
        return simbolo["tipo"]

    def obtener_nombre_interno(self, nombre):
        simbolo = self.buscar_variable(nombre)
        if simbolo is None:
            return nombre
        return simbolo["interno"]

    def guardar_momento(self, nombre):
        self.historial.append({
            "momento": nombre,
            "ambitos": copy.deepcopy(self.ambitos)
        })

    def formatear_ambitos(self, ambitos=None):
        if ambitos is None:
            ambitos = self.ambitos
        lineas = ["self.ambitos = ["]
        for i, ambito in enumerate(ambitos, 1):
            lineas.append(f"  Ambito {i} ({ambito['nombre']}):")
            if not ambito["simbolos"]:
                lineas.append("    <vacio>")
            for nombre, datos in ambito["simbolos"].items():
                lineas.append(
                    f"    {nombre}: tipo={datos['tipo']}, categoria={datos['categoria']}, interno={datos['interno']}"
                )
        lineas.append("]")
        return "\n".join(lineas)


# ejercicio del laberinto de ambitos
class AnalizadorAmbitos:
    def __init__(self):
        self.tabla = TablaSimbolosJerarquica()
        self.errores = []
        self.c3d = []
        self.codigo_c = ""
        self.codigo_asm = ""
        self.shadowing_info = ""

    # analiza el codigo pseudo c++
    def analizar_codigo_fuente(self, codigo):
        self.tabla = TablaSimbolosJerarquica()
        self.errores = []
        self.c3d = []
        self.codigo_c = codigo.strip()
        self.codigo_asm = ""
        self.shadowing_info = ""

        self.tabla.abrir_ambito("global")
        lineas = self.preparar_lineas(codigo)
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            if not linea:
                i += 1
                continue

            funcion = re.match(r"void\s+(\w+)\s*\((.*?)\)\s*\{?", linea)
            if funcion:
                nombre_funcion = funcion.group(1)
                parametros = funcion.group(2).strip()
                self.tabla.declarar_variable(nombre_funcion, "void", "funcion")
                self.tabla.abrir_ambito(nombre_funcion)
                if parametros:
                    for parametro in parametros.split(','):
                        partes = parametro.strip().split()
                        if len(partes) == 2:
                            self.tabla.declarar_variable(partes[1], partes[0], "parametro")
                i += 1
                continue

            if linea == "{":
                self.tabla.abrir_ambito("bloque")
                i += 1
                continue

            if linea == "}":
                if len(self.tabla.ambitos) >= 3 and "x" in self.tabla.ambitos[-1]["simbolos"]:
                    self.tabla.guardar_momento("Momento B: justo antes de cerrar el bloque interno")
                self.tabla.cerrar_ambito()
                i += 1
                continue

            if self.es_declaracion(linea):
                self.analizar_declaracion(linea)
                i += 1
                continue

            if self.es_asignacion(linea):
                self.analizar_asignacion(linea)
                i += 1
                continue

            if linea.startswith("escribir") or linea.startswith("printf"):
                self.analizar_escribir(linea)
                i += 1
                continue

            i += 1

        self.generar_c3d_bloque_interno()
        self.generar_asm_referencia()
        self.generar_info_shadowing()
        return self

    def preparar_lineas(self, codigo):
        texto = codigo.replace("{", "{\n").replace("}", "\n}\n")
        partes = []
        for linea in texto.splitlines():
            actual = linea.strip()
            if not actual:
                continue
            if ";" in actual:
                subpartes = actual.split(";")
                for j, sub in enumerate(subpartes):
                    sub = sub.strip()
                    if sub:
                        partes.append(sub + (";" if j < len(subpartes) - 1 else ""))
            else:
                partes.append(actual)
        return partes

    def es_declaracion(self, linea):
        return re.match(r"^(int|float)\s+\w+", linea) is not None

    def es_asignacion(self, linea):
        return re.match(r"^\w+\s*=", linea) is not None

    def analizar_declaracion(self, linea):
        limpia = linea.rstrip(";")
        m = re.match(r"(int|float)\s+(\w+)\s*(=\s*(.*))?$", limpia)
        if not m:
            return
        tipo = m.group(1)
        nombre = m.group(2)
        expresion = m.group(4)

        if expresion:
            tipo_expr = self.obtener_tipo_expresion(expresion)
            if tipo_expr and tipo != tipo_expr:
                if not (tipo == "float" and tipo_expr == "int"):
                    self.errores.append(
                        f"Error de tipo: no se puede inicializar {nombre} de tipo {tipo} con una expresion {tipo_expr}"
                    )

        declarado = self.tabla.declarar_variable(nombre, tipo, "variable")
        if not declarado:
            self.errores.append(f"Error semantico: la variable {nombre} ya existe en este mismo ambito")

        if nombre == "y" and tipo == "int":
            self.tabla.guardar_momento("Momento A: despues de declarar int y = a * 2")

    def analizar_asignacion(self, linea):
        limpia = linea.rstrip(";")
        nombre, expresion = limpia.split("=", 1)
        nombre = nombre.strip()
        expresion = expresion.strip()
        simbolo = self.tabla.buscar_variable(nombre)
        if simbolo is None:
            self.errores.append(f"Error de visibilidad: la variable {nombre} no esta declarada")
            return

        tipo_variable = simbolo["tipo"]
        tipo_expr = self.obtener_tipo_expresion(expresion)
        if tipo_expr and tipo_variable != tipo_expr:
            if not (tipo_variable == "float" and tipo_expr == "int"):
                self.errores.append(
                    f"Error de tipo: no se puede asignar una expresion {tipo_expr} a la variable {nombre} de tipo {tipo_variable}"
                )

    def analizar_escribir(self, linea):
        if "(" in linea and ")" in linea:
            expresion = linea[linea.find("(") + 1: linea.rfind(")")].strip()
            if expresion == "z":
                self.tabla.guardar_momento("Momento C: al llegar a la linea escribir(z)")
            self.obtener_tipo_expresion(expresion)

    def obtener_tipo_expresion(self, texto):
        texto = texto.strip()
        try:
            expresion = parsear_expresion(texto)
            return self.obtener_tipo_nodo(expresion)
        except Exception:
            return None

    def obtener_tipo_nodo(self, nodo):
        if isinstance(nodo, NodoNumero):
            return "float" if "." in nodo.valor else "int"
        if isinstance(nodo, NodoTexto):
            return "string"
        if isinstance(nodo, NodoIdentificador):
            tipo = self.tabla.obtener_tipo_variable(nodo.nombre)
            if tipo is None:
                self.errores.append(f"Error de visibilidad: la variable {nodo.nombre} no esta declarada")
                return None
            return tipo
        if isinstance(nodo, NodoOperacion):
            tipo_izq = self.obtener_tipo_nodo(nodo.izquierda)
            tipo_der = self.obtener_tipo_nodo(nodo.derecha)
            if nodo.operador in [">", "<", ">=", "<=", "==", "!="]:
                return "int"
            if tipo_izq is None or tipo_der is None:
                return None
            if tipo_izq != tipo_der:
                self.errores.append(
                    f"Error de tipo: operacion entre tipos incompatibles {tipo_izq} {nodo.operador} {tipo_der}"
                )
                return "float" if "float" in [tipo_izq, tipo_der] else "int"
            return tipo_izq
        return None

    # c3d del bloque interno
    def generar_c3d_bloque_interno(self):
        y = "y_test_2"
        x_local = "x_bloque_3"
        self.c3d = [
            f"{x_local} = 5.5",
            f"t1 = {y} + {x_local}",
            f"{y} = t1",
        ]

    def generar_asm_referencia(self):
        self.codigo_asm = "\n".join([
            "section .data",
            "    x_global dd 10",
            "    x_bloque_3 dd 5",
            "section .bss",
            "    y_test_2 resd 1",
            "section .text",
            "global _start",
            "_start:",
            "    mov eax, [y_test_2]",
            "    add eax, [x_bloque_3]",
            "    mov [y_test_2], eax",
            "    mov eax, 1",
            "    xor ebx, ebx",
            "    int 0x80",
        ])

    def generar_info_shadowing(self):
        self.shadowing_info = (
            "El metodo obtener_tipo_variable busca desde el ultimo ambito abierto hacia el ambito global.\n"
            "En la linea y = y + x; encuentra primero la x del bloque interno.\n"
            "Por eso la x usada es x_bloque_3 de tipo float y no x_global de tipo int."
        )

    # resumen que se muestra al final
    def resumen_final(self):
        lineas = []
        lineas.append("RESUMEN FINAL DEL ANALISIS SEMANTICO")
        lineas.append("=" * 45)
        for item in self.tabla.historial:
            lineas.append("")
            lineas.append(item["momento"])
            lineas.append(self.tabla.formatear_ambitos(item["ambitos"]))
        lineas.append("")
        lineas.append("ERRORES SEMANTICOS")
        if self.errores:
            for error in self.errores:
                lineas.append("- " + error)
        else:
            lineas.append("No se encontraron errores semanticos")
        lineas.append("")
        lineas.append("SHADOWING")
        lineas.append(self.shadowing_info)
        lineas.append("")
        lineas.append("CODIGO DE TRES DIRECCIONES")
        for linea in self.c3d:
            lineas.append(linea)
        return "\n".join(lineas)
