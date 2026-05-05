from nodos_ast import NodoPrograma, NodoAsignacion, NodoImprimir, NodoEntrada, NodoCondicional


class TraductorDiagrama:
    def __init__(self, nodos, conexiones):
        self.nodos = nodos
        self.conexiones = conexiones

    def construir_ast(self):
        inicio = self.buscar_tipo("INICIO")
        if inicio is None:
            raise Exception("El diagrama necesita un nodo INICIO")

        siguientes = self.obtener_siguientes(inicio)
        if not siguientes:
            return NodoPrograma([])

        sentencias = self.recorrer(siguientes[0], set())
        return NodoPrograma(sentencias)

    def buscar_tipo(self, tipo):
        for id_nodo, nodo in self.nodos.items():
            if nodo.tipo == tipo:
                return id_nodo
        return None

    def obtener_siguientes(self, id_nodo):
        salida = []
        for conexion in self.conexiones:
            if conexion["origen"] == id_nodo:
                salida.append(conexion["destino"])
        return salida

    def recorrer(self, id_actual, visitados):
        if id_actual in visitados:
            return []

        if id_actual not in self.nodos:
            return []

        nodo = self.nodos[id_actual]
        if nodo.tipo == "FIN":
            return []

        visitados.add(id_actual)
        sentencia = self.convertir_nodo(nodo, visitados)
        siguientes = self.obtener_siguientes(id_actual)

        sentencias = []
        if sentencia is not None:
            sentencias.append(sentencia)

        if nodo.tipo != "DECISION" and siguientes:
            sentencias.extend(self.recorrer(siguientes[0], visitados))

        return sentencias

    def convertir_nodo(self, nodo, visitados):
        texto = nodo.texto.strip()

        if nodo.tipo == "PROCESO":
            if "=" not in texto:
                raise Exception(f"El proceso '{texto}' debe tener formato variable = valor")
            nombre, valor = texto.split("=", 1)
            return NodoAsignacion(nombre, valor)

        if nodo.tipo == "ENTRADA":
            if not texto:
                raise Exception("El nodo de entrada necesita el nombre de una variable")
            return NodoEntrada(texto)

        if nodo.tipo == "SALIDA":
            if not texto:
                raise Exception("El nodo de salida necesita una expresión")
            return NodoImprimir(texto)

        if nodo.tipo == "DECISION":
            if not texto:
                raise Exception("El nodo de decisión necesita una condición")

            siguientes = self.obtener_siguientes(nodo.id_nodo)
            cuerpo_verdadero = []
            cuerpo_falso = []

            if len(siguientes) >= 1:
                cuerpo_verdadero = self.recorrer(siguientes[0], set(visitados))
            if len(siguientes) >= 2:
                cuerpo_falso = self.recorrer(siguientes[1], set(visitados))

            return NodoCondicional(texto, cuerpo_verdadero, cuerpo_falso)

        return None
