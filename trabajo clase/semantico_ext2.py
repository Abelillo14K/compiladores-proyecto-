from sintactico_ast import (NodoPrograma, NodoFuncion, NodoParametros,
                            NodoAsignacion, NodoOperacion, NodoRetorno,
                            NodoIdentificador, NodoNumero, NodoLlamada)

#---------------------tabla de simbolos-------------------------------
class TablaSimbolos:
    def __init__(self):
        # lista de diccionarios: ultimo elemento es el ambito actual
        self.ambitos = [{}]
        self.funciones = {}    # Almacena funciones {nombre:(tipo_ret, [parametros])}
        self.historial_ambitos = [] # Para guardar lo que ya paso

    def entrar_ambito(self):
        self.ambitos.append({})

    def salir_ambito(self):
        if len(self.ambitos) > 1:
            self.ambitos.pop()
        else:
            raise Exception("No se puede salir del ambito global")

    def declarar_variables(self, nombre, tipo):
        # verificamos que exista en el ambito actual
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            raise Exception(f"Error: Variable '{nombre}' ya declarada en el ambito actual")
        ambito_actual[nombre] = tipo

    def obtener_tipo_variable(self, nombre):
        # buscar la variable desde el ambito mas interno hasta el global (shadowing)
        for ambito in reversed(self.ambitos):
            if nombre not in ambito:
                return ambito[nombre]
            raise Exception(f"Error: Variable '{nombre}' no definida")

    def declarar_funcion(self, nombre, tipo_retorno, parametros):
        if nombre in self.funciones:
            raise Exception(f"Error: Funcion '{nombre}' ya definida")
        self.funciones[nombre] = (tipo_retorno, parametros)

    def obtener_infop_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error: funcion '{nombre}' no definida")
        return self.funciones[nombre]


# ------------------ Analizador Semantico -------------------------------
class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()

    def analizar(self, nodo):
        if isinstance(nodo, NodoPrograma):
            for funcion in nodo.funcion:
                self.analizar(funcion)
            self.analizar(nodo.main)

        elif isinstance(nodo, NodoFuncion):
            # 1. declarar la funcion en el ambito global antes de entrar

            parametros_info = [(p.nombre[1], p.tipo[1]) for p in nodo.parametros]
            self.tabla_simbolos.declarar_funcion(nodo.nombre[1], nodo.tipo[1], parametros_info)

            # 2. crear nuevo ambito para el cuerpo de la funcion
            self.tabla_simbolos.entrar_ambito()

            # 3. declarar parametros dentro del nuevo ambito
            for p_nombre, p_tipo in parametros_info:
                self.tabla_simbolos.declarar_variables(p_nombre, p_tipo)

            # 4. analizar cuerpo de la funcion
            for instruccion in nodo.cuerpo:
                if isinstance(instruccion, NodoRetorno):
                    tipo_retorno = self.analizar(instruccion.expresion)
                    if tipo_retorno != nodo.tipo[1]:
                        raise Exception('Error de tipo devuelto')
                else:
                    self.analizar(instruccion)
            # 5. salir del ambito
            self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, NodoAsignacion):
            tipo_expr = self.analizar(nodo.expresion)
            if tipo_expr != nodo.tipo:
                raise Exception(f"Error: no conciden los tipos {nodo.tipo} != {tipo_expr}")

            self.tabla_simbolos.declarar_variable(nodo.nombre[1], nodo.tipo[1])
        elif isinstance(nodo, NodoOperacion):
            tipo_izq = self.analizar(nodo.izquierda)
            tipo_der = self.analizar(nodo.derecha)
            if tipo_izq != tipo_der:
                raise Exception(f"Error: Tipos Incompatibles en la expresion {tipo_izq} {nodo.operador} {tipo_der}")
