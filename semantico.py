class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}
        self.errores = []

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

    def revisar_expresion(self, expresion):
        nombre_clase = type(expresion).__name__
        if nombre_clase == "NodoIdentificador":
            if expresion.nombre not in self.tabla_simbolos:
                self.errores.append(f"Error semantico: la variable {expresion.nombre} se usa antes de tener valor")
        elif nombre_clase == "NodoOperacion":
            self.revisar_expresion(expresion.izquierda)
            self.revisar_expresion(expresion.derecha)
