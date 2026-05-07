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

    def declarar_variable(self, nombre, tipo):
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

    def obtener_info_funcion(self, nombre):
        if nombre not in self.funciones:
            raise Exception(f"Error: funcion '{nombre}' no definida")
        return self.funciones[nombre]

        for var, tipo in self.ambitos[0].items():
            print(f"        {var:12} : {tipo}")

        # 2. variables locales recuperadas del historial
        print("\n[historial de Ambitos locales finalizados]:")
        for i, h in enumerate(self.historial_ambitos):
            print(f"    Bloque finalizado #{i} -{h['bloque']} (Nivel {h['nivel']}):")
            for var, tipo in h['variables'].items():
                print(f"        {var:12} : {tipo}")


#------------------- Sistema de tipos ----------------------------------
class SistemaTipos:

    @staticmethod
    def es_compatible(t1, t2):
        return t1==t2 or (t1 == 'int' and t2 == 'float') or (t2 == 'int' and t1 == 'float')

    @staticmethod
    def tipo_resultante(t1, t2, operador):
        # Promocion de tipos
        if t1 == 'float' or t2 == 'float':
            return 'float'
        return 'int'


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
                self.tabla_simbolos.declarar_variable(p_nombre, p_tipo)

            # 4. analizar cuerpo de la funcion
            for instruccion in nodo.cuerpo:
                if isinstance(instruccion, NodoRetorno):
                    tipo_retorno = self.analizar(instruccion.expresion)
                    if tipo_retorno != nodo.tipo[1]:
                        raise Exception('Error de tipo devuelto')
                else:
                    self.analizar(instruccion)
            # 5. salir del ambito
            self.tabla_simbolos.salir_ambito(nodo.nombre[1])

        elif isinstance(nodo, NodoAsignacion):
            tipo_expr = self.analizar(nodo.expresion)
            if tipo_expr != nodo.tipo[1]:
                raise Exception(f"Error: no conciden los tipos {nodo.tipo[1]} != {tipo_expr}")

            self.tabla_simbolos.declarar_variable(nodo.nombre[1], nodo.tipo[1])

        elif isinstance(nodo, NodoOperacion):
            tipo_izq = self.analizar(nodo.izquierda)
            tipo_der = self.analizar(nodo.derecha)
            if not SistemaTipos.es_compatible(tipo_izq, tipo_der):
                raise Exception(f"Error: Tipos Incompatibles en la expresion {tipo_izq} {nodo.operador} {tipo_der}")
            return SistemaTipos.tipo_resultante(tipo_izq, tipo_der, nodo.operador[1])

        elif isinstance(nodo, NodoIdentificador):
            return self.tabla_simbolos.obtener_tipo_variable(nodo.nombre[1])

        elif isinstance(nodo, NodoNumero):
            return 'int' if '.' not in nodo.valor[1] else 'float'

        elif isinstance(nodo, NodoLlamada):
            tipo, parametros = self.tabla_simbolos.obtener_info_funcion((nodo.nombre))
            if len(parametros) != len(nodo.argumentos):
                raise Exception(f"Error: La funcion '{nodo.nombre}' espera {len(parametros)} argumentos, pero recibio {len(nodo.argumentos)}")
            i = 0
            for argumento in nodo.argumentos:
                arg_tipo = self.analizar(argumento)
                param_tipo = parametros[i][1]
                if not SistemaTipos.es_compatible(arg_tipo, param_tipo):
                    raise Exception(f"Error: No coinciden los tipos")
                i+=1
            return tipo
