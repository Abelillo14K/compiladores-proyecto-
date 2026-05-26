
from sintactico_ast import parsear_asignacion, parsear_expresion, NodoTexto


# base para los nodos del ast
class NodoAST:
    def traducir_py(self, nivel=0):
        raise NotImplementedError

    def traducir_c(self, nivel=1):
        raise NotImplementedError

    def obtener_vars(self, variables):
        pass

    def a_diccionario(self):
        return {"tipo": type(self).__name__}


# nodo principal del programa
class NodoPrograma(NodoAST):
    def __init__(self, sentencias):
        self.sentencias = sentencias

    def traducir_py(self, nivel=0):
        lineas = []
        for sentencia in self.sentencias:
            lineas.append(sentencia.traducir_py(nivel))
        return "\n".join(lineas)

    def traducir_c(self, nivel=1):
        variables = set()
        self.obtener_vars(variables)

        lineas = ["#include <stdio.h>", "", "int main() {"]
        for variable in sorted(variables):
            lineas.append(f"    int {variable} = 0;")
        if variables:
            lineas.append("")
        for sentencia in self.sentencias:
            codigo = sentencia.traducir_c(nivel)
            if codigo:
                lineas.append(codigo)
        lineas.append("    return 0;")
        lineas.append("}")
        return "\n".join(lineas)

    def obtener_vars(self, variables):
        for sentencia in self.sentencias:
            sentencia.obtener_vars(variables)

    def a_diccionario(self):
        return {"tipo": "Programa", "sentencias": [s.a_diccionario() for s in self.sentencias]}


# nodo de asignacion
class NodoAsignacion(NodoAST):
    def __init__(self, texto):
        self.texto_original = texto
        self.nombre, self.expresion = parsear_asignacion(texto)

    def traducir_py(self, nivel=0):
        espacio = "    " * nivel
        return f"{espacio}{self.nombre} = {self.expresion.traducir_py()}"

    def traducir_c(self, nivel=1):
        espacio = "    " * nivel
        return f"{espacio}{self.nombre} = {self.expresion.traducir_c()};"

    def obtener_vars(self, variables):
        variables.add(self.nombre)
        self.expresion.obtener_vars(variables)

    def a_diccionario(self):
        return {"tipo": "Asignacion", "variable": self.nombre, "expresion": self.expresion.a_diccionario()}


# nodo de entrada
class NodoEntrada(NodoAST):
    def __init__(self, texto):
        self.nombre = texto.strip()
        if not self.nombre:
            raise Exception("Error: el nodo de entrada necesita el nombre de una variable")

    def traducir_py(self, nivel=0):
        espacio = "    " * nivel
        return f'{espacio}{self.nombre} = int(input("Ingrese {self.nombre}: "))'

    def traducir_c(self, nivel=1):
        espacio = "    " * nivel
        return f'{espacio}printf("Ingrese {self.nombre}: ");\n{espacio}scanf("%d", &{self.nombre});'

    def obtener_vars(self, variables):
        variables.add(self.nombre)

    def a_diccionario(self):
        return {"tipo": "Entrada", "variable": self.nombre}


# nodo de salida
class NodoImprimir(NodoAST):
    def __init__(self, texto):
        self.texto_original = texto.strip()
        self.expresion = parsear_expresion(self.texto_original)

    def traducir_py(self, nivel=0):
        espacio = "    " * nivel
        return f"{espacio}print({self.expresion.traducir_py()})"

    def traducir_c(self, nivel=1):
        espacio = "    " * nivel
        if isinstance(self.expresion, NodoTexto):
            texto = self.expresion.valor.strip('"')
            return f'{espacio}printf("{texto}\\n");'
        return f'{espacio}printf("%d\\n", {self.expresion.traducir_c()});'

    def obtener_vars(self, variables):
        self.expresion.obtener_vars(variables)

    def a_diccionario(self):
        return {"tipo": "Imprimir", "expresion": self.expresion.a_diccionario()}


# nodo de decision
class NodoCondicional(NodoAST):
    def __init__(self, texto, cuerpo_verdadero=None, cuerpo_falso=None):
        self.texto_original = texto.strip()
        self.condicion = parsear_expresion(self.texto_original)
        self.cuerpo_verdadero = cuerpo_verdadero if cuerpo_verdadero else []
        self.cuerpo_falso = cuerpo_falso if cuerpo_falso else []

    def traducir_py(self, nivel=0):
        espacio = "    " * nivel
        lineas = [f"{espacio}if {self.condicion.traducir_py()}:"]
        if self.cuerpo_verdadero:
            for sentencia in self.cuerpo_verdadero:
                lineas.append(sentencia.traducir_py(nivel + 1))
        else:
            lineas.append(f"{espacio}    pass")

        if self.cuerpo_falso:
            lineas.append(f"{espacio}else:")
            for sentencia in self.cuerpo_falso:
                lineas.append(sentencia.traducir_py(nivel + 1))
        return "\n".join(lineas)

    def traducir_c(self, nivel=1):
        espacio = "    " * nivel
        lineas = [f"{espacio}if {self.condicion.traducir_c()} {{"]
        for sentencia in self.cuerpo_verdadero:
            lineas.append(sentencia.traducir_c(nivel + 1))
        lineas.append(f"{espacio}}}")
        if self.cuerpo_falso:
            lineas[-1] = f"{espacio}}} else {{"
            for sentencia in self.cuerpo_falso:
                lineas.append(sentencia.traducir_c(nivel + 1))
            lineas.append(f"{espacio}}}")
        return "\n".join(lineas)

    def obtener_vars(self, variables):
        self.condicion.obtener_vars(variables)
        for sentencia in self.cuerpo_verdadero:
            sentencia.obtener_vars(variables)
        for sentencia in self.cuerpo_falso:
            sentencia.obtener_vars(variables)

    def a_diccionario(self):
        return {
            "tipo": "Condicional",
            "condicion": self.condicion.a_diccionario(),
            "verdadero": [s.a_diccionario() for s in self.cuerpo_verdadero],
            "falso": [s.a_diccionario() for s in self.cuerpo_falso],
        }


# nodo para ciclos mientras
class NodoMientras(NodoAST):
    def __init__(self, texto, cuerpo=None, negar=False):
        self.texto_original = texto.strip()
        self.condicion = parsear_expresion(self.texto_original)
        self.cuerpo = cuerpo if cuerpo else []
        self.negar = negar

    def traducir_py(self, nivel=0):
        espacio = "    " * nivel
        condicion = self.condicion.traducir_py()
        if self.negar:
            condicion = f"not ({condicion})"
        lineas = [f"{espacio}while {condicion}:"]
        if self.cuerpo:
            for sentencia in self.cuerpo:
                lineas.append(sentencia.traducir_py(nivel + 1))
        else:
            lineas.append(f"{espacio}    pass")
        return "\n".join(lineas)

    def traducir_c(self, nivel=1):
        espacio = "    " * nivel
        condicion = self.condicion.traducir_c()
        if self.negar:
            condicion = f"!({condicion})"
        lineas = [f"{espacio}while {condicion} {{"]
        for sentencia in self.cuerpo:
            lineas.append(sentencia.traducir_c(nivel + 1))
        lineas.append(f"{espacio}}}")
        return "\n".join(lineas)

    def obtener_vars(self, variables):
        self.condicion.obtener_vars(variables)
        for sentencia in self.cuerpo:
            sentencia.obtener_vars(variables)

    def a_diccionario(self):
        return {
            "tipo": "Mientras",
            "condicion": self.condicion.a_diccionario(),
            "negar": self.negar,
            "cuerpo": [s.a_diccionario() for s in self.cuerpo],
        }
