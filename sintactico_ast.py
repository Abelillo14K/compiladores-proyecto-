from lexico import identificar_tokens


# base de las expresiones
class NodoExpresion:
    def traducir_py(self):
        raise NotImplementedError

    def traducir_c(self):
        raise NotImplementedError

    def obtener_vars(self, variables):
        pass

    def a_diccionario(self):
        return {"tipo": type(self).__name__}


# numero del ast
class NodoNumero(NodoExpresion):
    def __init__(self, valor):
        self.valor = valor

    def traducir_py(self):
        return self.valor

    def traducir_c(self):
        return self.valor

    def a_diccionario(self):
        return {"tipo": "Numero", "valor": self.valor}


# texto del ast
class NodoTexto(NodoExpresion):
    def __init__(self, valor):
        self.valor = valor

    def traducir_py(self):
        return self.valor

    def traducir_c(self):
        return self.valor

    def a_diccionario(self):
        return {"tipo": "Texto", "valor": self.valor}


# variable del ast
class NodoIdentificador(NodoExpresion):
    def __init__(self, nombre):
        self.nombre = nombre

    def traducir_py(self):
        return self.nombre

    def traducir_c(self):
        return self.nombre

    def obtener_vars(self, variables):
        variables.add(self.nombre)

    def a_diccionario(self):
        return {"tipo": "Identificador", "nombre": self.nombre}


# operacion del ast
class NodoOperacion(NodoExpresion):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def traducir_py(self):
        return f"({self.izquierda.traducir_py()} {self.operador} {self.derecha.traducir_py()})"

    def traducir_c(self):
        return f"({self.izquierda.traducir_c()} {self.operador} {self.derecha.traducir_c()})"

    def obtener_vars(self, variables):
        self.izquierda.obtener_vars(variables)
        self.derecha.obtener_vars(variables)

    def a_diccionario(self):
        return {
            "tipo": "Operacion",
            "operador": self.operador,
            "izquierda": self.izquierda.a_diccionario(),
            "derecha": self.derecha.a_diccionario(),
        }


# parser de expresiones
class ParserExpresiones:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0

    def actual(self):
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None

    def avanzar(self):
        token = self.actual()
        self.posicion += 1
        return token

    def coincidir(self, tipo, valor=None):
        token = self.actual()
        if token is None:
            raise Exception("Error sintactico: se esperaba otro token")
        if token[0] != tipo:
            raise Exception(f"Error sintactico: se esperaba {tipo} y se obtuvo {token}")
        if valor is not None and token[1] != valor:
            raise Exception(f"Error sintactico: se esperaba {valor} y se obtuvo {token[1]}")
        self.posicion += 1
        return token

    def parsear(self):
        if len(self.tokens) == 0:
            raise Exception("Error sintactico: expresion vacia")
        resultado = self.comparacion()
        if self.actual() is not None:
            raise Exception(f"Error sintactico: token inesperado {self.actual()}")
        return resultado

    def comparacion(self):
        izquierda = self.expresion()
        token = self.actual()
        if token and token[0] == "OPERATOR" and token[1] in [">", "<", ">=", "<=", "==", "!="]:
            operador = self.avanzar()[1]
            derecha = self.expresion()
            izquierda = NodoOperacion(izquierda, operador, derecha)
        return izquierda

    def expresion(self):
        izquierda = self.termino()
        while self.actual() and self.actual()[0] == "OPERATOR" and self.actual()[1] in ["+", "-"]:
            operador = self.avanzar()[1]
            derecha = self.termino()
            izquierda = NodoOperacion(izquierda, operador, derecha)
        return izquierda

    def termino(self):
        izquierda = self.factor()
        while self.actual() and self.actual()[0] == "OPERATOR" and self.actual()[1] in ["*", "/"]:
            operador = self.avanzar()[1]
            derecha = self.factor()
            izquierda = NodoOperacion(izquierda, operador, derecha)
        return izquierda

    def factor(self):
        token = self.actual()
        if token is None:
            raise Exception("Error sintactico: factor incompleto")

        if token[0] == "NUMBER":
            return NodoNumero(self.avanzar()[1])

        if token[0] == "STRING":
            return NodoTexto(self.avanzar()[1])

        if token[0] == "IDENTIFIER":
            return NodoIdentificador(self.avanzar()[1])

        if token[0] == "OPERATOR" and token[1] == "-":
            self.avanzar()
            valor = self.factor()
            return NodoOperacion(NodoNumero("0"), "-", valor)

        if token[0] == "DELIMITER" and token[1] == "(":
            self.avanzar()
            expresion = self.comparacion()
            self.coincidir("DELIMITER", ")")
            return expresion

        raise Exception(f"Error sintactico: factor invalido {token}")


# convierte texto a expresion
def parsear_expresion(texto):
    tokens = identificar_tokens(texto)
    parser = ParserExpresiones(tokens)
    return parser.parsear()


# separa variable y expresion
def parsear_asignacion(texto):
    tokens = identificar_tokens(texto)
    if len(tokens) < 3:
        raise Exception("Error sintactico: asignacion incompleta")
    if tokens[0][0] != "IDENTIFIER":
        raise Exception("Error sintactico: la asignacion debe iniciar con un identificador")
    if tokens[1] != ("OPERATOR", "="):
        raise Exception("Error sintactico: se esperaba el operador =")

    nombre = tokens[0][1]
    expresion_tokens = tokens[2:]
    expresion = ParserExpresiones(expresion_tokens).parsear()
    return nombre, expresion
