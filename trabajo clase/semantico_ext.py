from sintactico_ast import (NodoPrograma, NodoFuncion, NodoParametro,
                  NodoAsignacion, NodoOperacion, NodoRetorno,
                  NodoIdentificador, NodoNumero, NodoLlamadaFuncion)

class TablaSimbolos:
    def __init__(self):
        self.variables = {}    #Almacena variables {nombre:tipo}
        self.funciones = {}    # Almacena funciones {nombre:(tipo_ret, [parametros])}

    def declarar_variables(self, nombre, tipo):
        if nombre in self.variables:
            raise Exception(f"Error: Variable '{nombre}' ya declarada")
        self.variables[nombre] = tipo

    def obtener_tipo_variable(self, nombre):
        if nombre not in self.variables:
            raise Exception(f"Error: Variable '{nombre}' no definida")
        return self.variables[nombre]

    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: Funcion '{nombre}' ya definida")
        self.funciones[nombre] = (tipo_retorno, parametros)

    def obtener_infop_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error: funcion '{nombre}' no definida")
        return self.funciones[nombre]

    #------------------ Analizador Semantico -------------------------------
class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()

    def analizar(self, nodo):
        if isinstance(nodo, NodoPrograma):
            for funcion in nodo.funciones:
                self.analizar(funcion)
            self.analizar(main)
        elif isinstance(nodo, NodoFuncion):
            self.tabla_simbolos.declarar_funcion(nodo.nombre, nodo.tipo, nodo.parametros)
            for instruccion in nodo.cuerpo:
                self.analizar(instruccion)
        elif isinstance(nodo, NodoAsignacion):
            tipo_expr = self.analizar(nodo.expresion)
            if tipo_expr != nodo.tipo:
                raise Exception(f"Error: no conciden los tipos {nodo.tipo} != {tipo_expr}")

            self.tabla_simbolos.declarar_variable(nodo.nombre, nodo.tipo)
        elif isinstance(nodo, NodoOperacion):
            tipo_izq = self.analizar(nodo.izquierda)
            tipo_der = self.analizar(nodo.derecha)
            if tipo_izq != tipo_der:
                raise Exception(f"Error: Tipos Incompatibles en la expresion {tipo_izq} {nodo.operador} {tipo_der}")
    