class NodoAST:
    def traducirPy(self): 
        raise NotImplementedError('Metodo traducirPy() no implementado en este Nodo')
    def traducirCPP(self): 
        raise NotImplementedError('Metodo traducirCPP() no implementado en este Nodo')
    def traducirGo(self): 
        raise NotImplementedError('Metodo traducirGO() no implementado en este Nodo')
    def generarCodigo(self):
        raise NotImplementedError('Metodo generarCodigo() no implementado en este Nodo')

class NodoPrograma(NodoAST):
    def __init__(self, funcion):
        self.variables = []
        self.funcion = funcion

    def generarCodigo(self):
        codigo = ["section .text", "global _start"]
        data = ["section .bss"]

        main_func = next((f for f in self.funcion if f.nombre[1] == 'main'), None)

        # Recolectar variables
        for func in self.funcion:
            print(func.generarCodigo())

        # Punto de entrada
        codigo.append("_start:")
        if main_func:
            codigo.append("    call main")

        codigo.append("    mov eax, 1    ; syscall exit")
        codigo.append("    xor ebx, ebx  ; Codigo de Salida 0")
        codigo.append("    int 0x80")

        # Subrutinas
        rutinas_print = """
print_newline:
    pushad              
    mov eax, 4          
    mov ebx, 1          
    mov ecx, salto_linea
    mov edx, 1          
    int 0x80
    popad               
    ret

print_int:
    pushad              
    mov ecx, buffer
    add ecx, 15          
    mov byte [ecx], 0   
    mov ebx, 10         
.convert_loop:
    xor edx, edx        
    div ebx             
    add dl, '0'         
    dec ecx             
    mov [ecx], dl       
    test eax, eax       
    jnz .convert_loop

    mov eax, buffer
    add eax, 15
    sub eax, ecx        
    mov edx, eax        
    mov eax, 4          
    mov ebx, 1          
    int 0x80
    popad               
    ret
"""
        codigo.append(rutinas_print)

        for variable in self.variables:
            if variable[0] == 'int':
                data.append(f'    {variable[1]}:    resd 1')      
        return '\n'.join(data) + '\n\n' + '\n'.join(codigo)

class NodoLlamada(NodoAST):
    def __init__(self, nombre, argumentos):
        self.nombre = nombre
        self.argumentos = argumentos

    def generarCodigo(self):
        codigo = []
        for arg in reversed (self.argumentos): # Apilamos argumentos en orden inverso
            codigo.append(arg.generarCodigo())
            codigo.append("    push eax  ; Pasar argumento a la pila")

        codigo.append(f"    call {self.nombre}  : Lamar a la funcion {self.nombre}")
        codigo.append(f"    add esp, {len(self.argumentos) * 4}  ; Limpiar pila de argumentos")
        return "\n".join(codigo)



class NodoString(NodoAST):
    def __init__(self, valor): self.valor = valor

class NodoPrint(NodoAST):
    def __init__(self, expresiones, nueva_linea=False): 
        self.expresiones = expresiones
        self.nueva_linea = nueva_linea

    def generarCodigo(self):
        codigo = []
        for exp in self.expresiones:
            codigo.append(exp.generarCodigo())
            codigo.append("    call print_int")
        if self.nueva_linea:
            codigo.append("    call print_newline")
        return '\n'.join(codigo)

class NodoFuncion(NodoAST):
    def __init__(self, tipo, nombre, parametros, cuerpo):
        self.tipo = tipo 
        self.nombre = nombre 
        self.parametros = parametros 
        self.cuerpo = cuerpo

    def generarCodigo(self):
        codigo = f'{self.nombre[1]}:\n'
        if len(self.parametros) > 0:
            for parametro in self.parametros:
                codigo += '\n    pop    eax'
                codigo += f'\n    mov [{parametro.nombre[1]}], eax'
        codigo += '\n'.join(c.generarCodigo() for c in self.cuerpo)
        codigo += '\n    ret'
        codigo += '\n'
        return codigo

class NodoParametros(NodoAST):
    def __init__(self, tipo, nombre): 
        self.tipo = tipo
        self.nombre = nombre

class NodoAsignacion(NodoAST):
    def __init__(self, tipo, nombre, expresion): 
        self.tipo = tipo; self.nombre = nombre; self.expresion = expresion

    def generarCodigo(self):
        codigo = self.expresion.generarCodigo()
        codigo += f'\n    mov [{self.nombre[1]}], eax'
        return codigo

class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha): 
        self.izquierda = izquierda; self.operador = operador; self.derecha = derecha

    def generarCodigo(self):
        codigo = []
        codigo.append(self.izquierda.generarCodigo())
        codigo.append('    push    eax')
        codigo.append(self.derecha.generarCodigo())
        codigo.append('    mov    ebx, eax')
        codigo.append('    pop    eax')
        if self.operador[1] == '+':
            codigo.append('    add    eax, ebx')
        return '\n'.join(codigo)

    def optimizar(self):
        if isinstance(self.izquierda, NodoOperacion):
            self.izquierda.optimizar()
        else:
            izquierda = self.izquierda

        if isinstance(self.derecha, NodoOperacion):
            self.derecha.optimizar()
        else:
            derecha = self.derecha

        # Si ambos nodos son numneros realizamos la operacion de manera directa
        if isinstance(izquierda, NodoNumero) and isinstance(derecha, NodoNumero):
            izq = int(izquierda.valor[1])
            der = int(derecha.valor[1])
            if self.operador[1] == '+':
                valor = izq + der
            elif self.operador[1] == '-':
                valor = izq - der
            elif self.operador[1] == '*':
                valor = izq * der
            elif self.operador[1] == '/':
                valor = izq / der
            return NodoNumero(('NUMBER', str(valor)))

        # Simplificacion algebraica (valores neutros)
        if self.operador[1] == '*' and isinstance(derecha, NodoNumero) and derecha.valor[1] == 1:
            return izquierda
        if self.operador[1] == '*' and isinstance(izquierda, NodoNumero) and izquierda.valor[1] == 1:
            return derecha
        if self.operador[1] == '+' and isinstance(derecha, NodoNumero) and derecha.valor[1] == 0:
            return izquierda
        if self.operador[1] == '+' and isinstance(izquierda, NodoNumero) and izquierda.valor[1] == 0:
            return derecha

        # Si no se puede optimizar mas, se devuelve la expresion
        return NodoOperacion(izquierda, self.operador, derecha)



class NodoRetorno(NodoAST):
    def __init__(self, expresion): self.expresion = expresion

    def traducir(self):
        return f"return {self.expresion.traducir()}"

    def generarCodigo(self): return self.expresion.generarCodigo()

class NodoIdentificador(NodoAST):
    def __init__(self, nombre): self.nombre = nombre
    def generarCodigo(self):
        # SE AGREGA dword PARA ESPECIFICAR TAMAÑO
        return f'\n    mov eax [{self.nombre[1]}]'

class NodoNumero(NodoAST):
    def __init__(self, valor): self.valor = valor
    def generarCodigo(self):
        return f'\n    mov eax, {self.valor[1]}'

# ---------------- Parser ----------------
class Parser:
    def __init__(self, tokens): 
        self.tokens = tokens; self.pos = 0

    def obtener_token_actual(self): 
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def coincidir(self, tipo_esperado):
        token = self.obtener_token_actual()
        if token and token[0] == tipo_esperado: 
            self.pos += 1; return token
        else: 
            raise SyntaxError(f'Error sintactico: se esperaba {tipo_esperado}, pero se encontro: {token}')

    def parsear(self): 
        funciones = []
        while self.obtener_token_actual() is not None:
            funciones.append(self.funcion())
        return NodoPrograma(funciones)

    def funcion(self):
        tipo = self.coincidir('KEYWORD') 
        nombre = self.coincidir('IDENTIFIER') 
        self.coincidir('DELIMITER') 
        parametros = [] if nombre[1] == 'main' else self.parametros()
        self.coincidir('DELIMITER') 
        self.coincidir('DELIMITER') 
        cuerpo = self.cuerpo()
        self.coincidir('DELIMITER') 
        return NodoFuncion(tipo, nombre, parametros, cuerpo)

    def parametros(self):
        lista = []
        token = self.obtener_token_actual()
        if token and token[1] == ')': return lista
        tipo = self.coincidir('KEYWORD'); nombre = self.coincidir('IDENTIFIER')
        lista.append(NodoParametros(tipo, nombre))
        while self.obtener_token_actual() and self.obtener_token_actual()[1] == ',':
            self.coincidir('DELIMITER')
            tipo = self.coincidir('KEYWORD'); nombre = self.coincidir('IDENTIFIER')
            lista.append(NodoParametros(tipo, nombre))
        return lista

    def cuerpo(self):
        instrucciones = []
        while self.obtener_token_actual() and self.obtener_token_actual()[1] != '}':
            token = self.obtener_token_actual()
            if token[1] == 'return': instrucciones.append(self.retorno())
            elif token[1] == 'Console': instrucciones.append(self.sentencia_imprimir_csharp())
            elif token[1] in ['print', 'printf']: instrucciones.append(self.sentencia_imprimir_cpp())
            else: instrucciones.append(self.asignacion())
        return instrucciones

    def sentencia_imprimir_csharp(self):
        token = self.obtener_token_actual()
        if token[0] == 'IDENTIFIER': self.coincidir('IDENTIFIER') 
        else: self.coincidir('KEYWORD')

        self.coincidir('DELIMITER') # Punto '.'

        metodo = self.obtener_token_actual()[1]
        nueva_linea = False
        if metodo == 'WriteLine': 
            nueva_linea = True
            self.pos += 1
        elif metodo == 'Write': self.pos += 1
        else: raise SyntaxError("Se esperaba Write o WriteLine")

        self.coincidir('DELIMITER') # '('
        args = self.lista_argumentos()
        self.coincidir('DELIMITER') # ')'
        self.coincidir('DELIMITER') # ';'
        return NodoPrint(args, nueva_linea)

    def sentencia_imprimir_cpp(self):
        token = self.obtener_token_actual()
        nueva_linea = (token[1] == 'println')
        self.coincidir('KEYWORD') 
        self.coincidir('DELIMITER') 
        args = self.lista_argumentos()
        self.coincidir('DELIMITER') 
        self.coincidir('DELIMITER') 
        return NodoPrint(args, nueva_linea)

    def lista_argumentos(self):
        args = []
        if self.obtener_token_actual()[1] != ')':
            sigue = True
            while sigue:
                args.append(self.expresion())
                if self.obtener_token_actual()[1] == ',': self.coincidir('DELIMITER')
                else: sigue = False
        return args

    def asignacion(self):
        tipo = self.coincidir('KEYWORD'); nombre = self.coincidir('IDENTIFIER'); self.coincidir('OPERATOR')
        exp = self.expresion(); self.coincidir('DELIMITER')
        return NodoAsignacion(tipo, nombre, exp)

    def retorno(self):
        self.coincidir('KEYWORD'); exp = self.expresion(); self.coincidir('DELIMITER')
        return NodoRetorno(exp)

    def expresion(self):
        izq = self.termino()
        while self.obtener_token_actual() and self.obtener_token_actual()[0] == 'OPERATOR':
            op = self.coincidir('OPERATOR'); der = self.termino()
            izq = NodoOperacion(izq, op, der)
        return izq

    def termino(self):
        token = self.obtener_token_actual()
        if token[0] == 'NUMBER': return NodoNumero(self.coincidir('NUMBER'))
        elif token[0] == 'STRING': return NodoString(self.coincidir('STRING'))
        elif token[0] == 'IDENTIFIER': 
            identificador = self.coincidir('IDENTIFIER')
            siguiente = self.obtener_token_actual()
            if siguiente and siguiente[1] == '(':
                self.coincidir('DELIMITER')
                args = self.lista_argumentos()
                self.coincidir('DELIMITER')
                return NodoLlamada(identificador, args)
            return NodoIdentificador(identificador)
        raise SyntaxError(f"Token inesperado: {token}")
