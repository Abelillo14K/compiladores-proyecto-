class NodoAST:
    def traducirPy(self, nivel=0):
        raise NotImplementedError

    def traducirC(self, declaraciones, nivel=1):
        raise NotImplementedError

    def generarCodigo(self, contexto):
        raise NotImplementedError

    def obtenerVars(self, vars_set):
        pass


def tab(nivel):
    return "    " * nivel


class NodoPrograma(NodoAST):
    def __init__(self, sentencias):
        self.sentencias = sentencias

    def traducirPy(self, nivel=0):
        codigo = []
        for sentencia in self.sentencias:
            codigo.append(sentencia.traducirPy(nivel))
        if not codigo:
            return "# programa vacio"
        return "\n".join(codigo)

    def traducirC(self, declaraciones=None, nivel=1):
        if declaraciones is None:
            declaraciones = set()

        for sentencia in self.sentencias:
            sentencia.obtenerVars(declaraciones)

        codigo = []
        codigo.append("#include <stdio.h>")
        codigo.append("")
        codigo.append("int main() {")

        for var in sorted(declaraciones):
            codigo.append(f"    int {var} = 0;")

        if declaraciones:
            codigo.append("")

        for sentencia in self.sentencias:
            codigo.append(sentencia.traducirC(declaraciones, nivel))

        codigo.append("    return 0;")
        codigo.append("}")
        return "\n".join(codigo)

    def generarCodigo(self, contexto=None):
        if contexto is None:
            contexto = ContextoASM()

        for sentencia in self.sentencias:
            sentencia.obtenerVars(contexto.variables)

        codigo = []
        codigo.append("section .data")
        codigo.append("    salto_linea db 0xA")
        codigo.append("")
        codigo.append("section .bss")
        codigo.append("    buffer resb 16")
        for var in sorted(contexto.variables):
            codigo.append(f"    {var} resd 1")

        codigo.append("")
        codigo.append("section .text")
        codigo.append("global _start")
        codigo.append("")
        codigo.append("_start:")

        for sentencia in self.sentencias:
            codigo.append(sentencia.generarCodigo(contexto))

        codigo.append("    mov eax, 1")
        codigo.append("    xor ebx, ebx")
        codigo.append("    int 0x80")
        codigo.append("")
        codigo.append(contexto.rutina_print_int())
        codigo.append("")
        codigo.append(contexto.rutina_print_newline())
        return "\n".join(codigo)


class NodoAsignacion(NodoAST):
    def __init__(self, nombre, valor):
        self.nombre = nombre.strip()
        self.valor = valor.strip()

    def traducirPy(self, nivel=0):
        return f"{tab(nivel)}{self.nombre} = {self.valor}"

    def traducirC(self, declaraciones, nivel=1):
        declaraciones.add(self.nombre)
        return f"{tab(nivel)}{self.nombre} = {self.valor};"

    def generarCodigo(self, contexto):
        contexto.variables.add(self.nombre)
        codigo = []
        codigo.append(f"    ; {self.nombre} = {self.valor}")

        if self.valor.lstrip("-").isdigit():
            codigo.append(f"    mov eax, {self.valor}")
            codigo.append(f"    mov dword [{self.nombre}], eax")
        elif self.valor.isidentifier():
            contexto.variables.add(self.valor)
            codigo.append(f"    mov eax, dword [{self.valor}]")
            codigo.append(f"    mov dword [{self.nombre}], eax")
        else:
            codigo.append(f"    ; expresion no traducida completamente a asm: {self.valor}")
            codigo.append("    mov eax, 0")
            codigo.append(f"    mov dword [{self.nombre}], eax")

        return "\n".join(codigo)

    def obtenerVars(self, vars_set):
        if self.nombre.isidentifier():
            vars_set.add(self.nombre)
        for token in self.valor.replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").split():
            if token.isidentifier():
                vars_set.add(token)


class NodoEntrada(NodoAST):
    def __init__(self, nombre):
        self.nombre = nombre.strip()

    def traducirPy(self, nivel=0):
        return f"{tab(nivel)}{self.nombre} = int(input('{self.nombre}: '))"

    def traducirC(self, declaraciones, nivel=1):
        declaraciones.add(self.nombre)
        return f"{tab(nivel)}printf(\"{self.nombre}: \" );\n{tab(nivel)}scanf(\"%d\", &{self.nombre});"

    def generarCodigo(self, contexto):
        contexto.variables.add(self.nombre)
        return f"    ; entrada de {self.nombre} no implementada en asm"

    def obtenerVars(self, vars_set):
        if self.nombre.isidentifier():
            vars_set.add(self.nombre)


class NodoImprimir(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion.strip()

    def traducirPy(self, nivel=0):
        return f"{tab(nivel)}print({self.expresion})"

    def traducirC(self, declaraciones, nivel=1):
        return f"{tab(nivel)}printf(\"%d\\n\", {self.expresion});"

    def generarCodigo(self, contexto):
        codigo = []
        codigo.append(f"    ; imprimir {self.expresion}")

        if self.expresion.lstrip("-").isdigit():
            codigo.append(f"    mov eax, {self.expresion}")
        elif self.expresion.isidentifier():
            contexto.variables.add(self.expresion)
            codigo.append(f"    mov eax, dword [{self.expresion}]")
        else:
            codigo.append(f"    ; expresion no traducida completamente a asm: {self.expresion}")
            codigo.append("    mov eax, 0")

        codigo.append("    call print_int")
        codigo.append("    call print_newline")
        return "\n".join(codigo)

    def obtenerVars(self, vars_set):
        for token in self.expresion.replace("+", " ").replace("-", " ").replace("*", " ").replace("/", " ").split():
            if token.isidentifier():
                vars_set.add(token)


class NodoCondicional(NodoAST):
    def __init__(self, condicion, cuerpo_verdadero, cuerpo_falso=None):
        self.condicion = condicion.strip()
        self.cuerpo_verdadero = cuerpo_verdadero
        self.cuerpo_falso = cuerpo_falso if cuerpo_falso else []

    def traducirPy(self, nivel=0):
        codigo = [f"{tab(nivel)}if {self.condicion}:"]

        if self.cuerpo_verdadero:
            for sentencia in self.cuerpo_verdadero:
                codigo.append(sentencia.traducirPy(nivel + 1))
        else:
            codigo.append(f"{tab(nivel + 1)}pass")

        if self.cuerpo_falso:
            codigo.append(f"{tab(nivel)}else:")
            for sentencia in self.cuerpo_falso:
                codigo.append(sentencia.traducirPy(nivel + 1))

        return "\n".join(codigo)

    def traducirC(self, declaraciones, nivel=1):
        codigo = [f"{tab(nivel)}if ({self.condicion}) {{"]

        if self.cuerpo_verdadero:
            for sentencia in self.cuerpo_verdadero:
                codigo.append(sentencia.traducirC(declaraciones, nivel + 1))
        else:
            codigo.append(f"{tab(nivel + 1)}/* sin instrucciones */")

        codigo.append(f"{tab(nivel)}}}")

        if self.cuerpo_falso:
            codigo[-1] = f"{tab(nivel)}}} else {{"
            for sentencia in self.cuerpo_falso:
                codigo.append(sentencia.traducirC(declaraciones, nivel + 1))
            codigo.append(f"{tab(nivel)}}}")

        return "\n".join(codigo)

    def generarCodigo(self, contexto):
        etiqueta_falsa = contexto.nueva_etiqueta("falso")
        etiqueta_fin = contexto.nueva_etiqueta("fin_si")
        codigo = []
        codigo.append(f"    ; si {self.condicion}")
        codigo.append(f"    ; condicion pendiente de traduccion completa: {self.condicion}")
        codigo.append(f"    ; en esta version se deja como comentario educativo")

        for sentencia in self.cuerpo_verdadero:
            codigo.append(sentencia.generarCodigo(contexto))

        if self.cuerpo_falso:
            codigo.append(f"    jmp {etiqueta_fin}")
            codigo.append(f"{etiqueta_falsa}:")
            for sentencia in self.cuerpo_falso:
                codigo.append(sentencia.generarCodigo(contexto))
            codigo.append(f"{etiqueta_fin}:")

        return "\n".join(codigo)

    def obtenerVars(self, vars_set):
        for token in self.condicion.replace(">", " ").replace("<", " ").replace("=", " ").replace("!", " ").split():
            if token.isidentifier():
                vars_set.add(token)
        for sentencia in self.cuerpo_verdadero:
            sentencia.obtenerVars(vars_set)
        for sentencia in self.cuerpo_falso:
            sentencia.obtenerVars(vars_set)


class ContextoASM:
    def __init__(self):
        self.variables = set()
        self.contador_etiquetas = 0

    def nueva_etiqueta(self, base):
        self.contador_etiquetas += 1
        return f"{base}_{self.contador_etiquetas}"

    def rutina_print_newline(self):
        return """print_newline:
    pushad
    mov eax, 4
    mov ebx, 1
    mov ecx, salto_linea
    mov edx, 1
    int 0x80
    popad
    ret"""

    def rutina_print_int(self):
        return """print_int:
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
    ret"""
