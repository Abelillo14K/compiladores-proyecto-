
import itertools
from sintactico_ast import NodoNumero, NodoTexto, NodoIdentificador, NodoOperacion


# traductor del ast
class Traductor:
    def __init__(self, programa):
        self.programa = programa
        self.contador_etiquetas = itertools.count(1)

    # salida en python
    def traducir_python(self):
        return self.programa.traducir_py()

    # salida en c
    def traducir_c(self):
        return self.programa.traducir_c()

    # salida en ensamblador
    def traducir_asm(self):
        variables = set()
        self.programa.obtener_vars(variables)

        lineas = []
        lineas.append("section .data")
        lineas.append("    salto_linea db 0xA")
        lineas.append("")
        lineas.append("section .bss")
        lineas.append("    buffer resb 16")
        for variable in sorted(variables):
            lineas.append(f"    {variable} resd 1")
        lineas.append("")
        lineas.append("section .text")
        lineas.append("global _start")
        lineas.append("")
        lineas.append("main:")

        for sentencia in self.programa.sentencias:
            self.generar_sentencia_asm(sentencia, lineas)

        lineas.append("    mov eax, 0")
        lineas.append("    ret")
        lineas.append("")
        lineas.append("_start:")
        lineas.append("    call main")
        lineas.append("    mov eax, 1")
        lineas.append("    xor ebx, ebx")
        lineas.append("    int 0x80")
        lineas.append("")
        lineas.extend(self.rutinas_impresion())
        return "\n".join(lineas)

    # asm por instruccion
    def generar_sentencia_asm(self, sentencia, lineas):
        nombre = type(sentencia).__name__
        if nombre == "NodoAsignacion":
            self.generar_expresion(sentencia.expresion, lineas)
            lineas.append(f"    mov dword [{sentencia.nombre}], eax")
        elif nombre == "NodoEntrada":
            lineas.append(f"    ; entrada pendiente en asm: {sentencia.nombre}")
        elif nombre == "NodoImprimir":
            if isinstance(sentencia.expresion, NodoTexto):
                lineas.append(f"    ; impresion de texto pendiente en asm: {sentencia.expresion.valor}")
            else:
                self.generar_expresion(sentencia.expresion, lineas)
                lineas.append("    call print_int")
                lineas.append("    call print_newline")
        elif nombre == "NodoCondicional":
            etiqueta_falsa = f"L_falso_{next(self.contador_etiquetas)}"
            etiqueta_fin = f"L_fin_{next(self.contador_etiquetas)}"
            self.generar_condicion(sentencia.condicion, lineas, etiqueta_falsa)
            for sub in sentencia.cuerpo_verdadero:
                self.generar_sentencia_asm(sub, lineas)
            lineas.append(f"    jmp {etiqueta_fin}")
            lineas.append(f"{etiqueta_falsa}:")
            for sub in sentencia.cuerpo_falso:
                self.generar_sentencia_asm(sub, lineas)
            lineas.append(f"{etiqueta_fin}:")
        elif nombre == "NodoMientras":
            etiqueta_inicio = f"L_mientras_{next(self.contador_etiquetas)}"
            etiqueta_fin = f"L_fin_mientras_{next(self.contador_etiquetas)}"
            lineas.append(f"{etiqueta_inicio}:")
            if sentencia.negar:
                self.generar_condicion_verdadera(sentencia.condicion, lineas, etiqueta_fin)
            else:
                self.generar_condicion(sentencia.condicion, lineas, etiqueta_fin)
            for sub in sentencia.cuerpo:
                self.generar_sentencia_asm(sub, lineas)
            lineas.append(f"    jmp {etiqueta_inicio}")
            lineas.append(f"{etiqueta_fin}:")

    # asm por expresion
    def generar_expresion(self, expresion, lineas):
        if isinstance(expresion, NodoNumero):
            numero = expresion.valor.split('.')[0]
            lineas.append(f"    mov eax, {numero}")
        elif isinstance(expresion, NodoIdentificador):
            lineas.append(f"    mov eax, dword [{expresion.nombre}]")
        elif isinstance(expresion, NodoOperacion):
            if expresion.operador in [">", "<", ">=", "<=", "==", "!="]:
                etiqueta_verdadera = f"L_bool_true_{next(self.contador_etiquetas)}"
                etiqueta_fin = f"L_bool_fin_{next(self.contador_etiquetas)}"
                self.generar_comparacion(expresion, lineas)
                salto = self.salto_para(expresion.operador)
                lineas.append(f"    {salto} {etiqueta_verdadera}")
                lineas.append("    mov eax, 0")
                lineas.append(f"    jmp {etiqueta_fin}")
                lineas.append(f"{etiqueta_verdadera}:")
                lineas.append("    mov eax, 1")
                lineas.append(f"{etiqueta_fin}:")
                return
            self.generar_expresion(expresion.izquierda, lineas)
            lineas.append("    push eax")
            self.generar_expresion(expresion.derecha, lineas)
            lineas.append("    mov ebx, eax")
            lineas.append("    pop eax")
            if expresion.operador == "+":
                lineas.append("    add eax, ebx")
            elif expresion.operador == "-":
                lineas.append("    sub eax, ebx")
            elif expresion.operador == "*":
                lineas.append("    imul eax, ebx")
            elif expresion.operador == "/":
                lineas.append("    cdq")
                lineas.append("    idiv ebx")
        else:
            lineas.append("    mov eax, 0")

    def generar_condicion(self, condicion, lineas, etiqueta_falsa):
        if isinstance(condicion, NodoOperacion) and condicion.operador in [">", "<", ">=", "<=", "==", "!="]:
            self.generar_comparacion(condicion, lineas)
            salto_falso = self.salto_falso_para(condicion.operador)
            lineas.append(f"    {salto_falso} {etiqueta_falsa}")
        else:
            self.generar_expresion(condicion, lineas)
            lineas.append("    cmp eax, 0")
            lineas.append(f"    je {etiqueta_falsa}")

    def generar_condicion_verdadera(self, condicion, lineas, etiqueta_verdadera):
        if isinstance(condicion, NodoOperacion) and condicion.operador in [">", "<", ">=", "<=", "==", "!="]:
            self.generar_comparacion(condicion, lineas)
            salto = self.salto_para(condicion.operador)
            lineas.append(f"    {salto} {etiqueta_verdadera}")
        else:
            self.generar_expresion(condicion, lineas)
            lineas.append("    cmp eax, 0")
            lineas.append(f"    jne {etiqueta_verdadera}")

    def generar_comparacion(self, expresion, lineas):
        self.generar_expresion(expresion.izquierda, lineas)
        lineas.append("    push eax")
        self.generar_expresion(expresion.derecha, lineas)
        lineas.append("    mov ebx, eax")
        lineas.append("    pop eax")
        lineas.append("    cmp eax, ebx")

    def salto_para(self, operador):
        return {">": "jg", "<": "jl", ">=": "jge", "<=": "jle", "==": "je", "!=": "jne"}.get(operador, "je")

    def salto_falso_para(self, operador):
        return {">": "jle", "<": "jge", ">=": "jl", "<=": "jg", "==": "jne", "!=": "je"}.get(operador, "je")

    def rutinas_impresion(self):
        return [
            "print_newline:",
            "    pushad",
            "    mov eax, 4",
            "    mov ebx, 1",
            "    mov ecx, salto_linea",
            "    mov edx, 1",
            "    int 0x80",
            "    popad",
            "    ret",
            "",
            "print_int:",
            "    pushad",
            "    mov ecx, buffer",
            "    add ecx, 15",
            "    mov byte [ecx], 0",
            "    mov ebx, 10",
            ".convert_loop:",
            "    xor edx, edx",
            "    div ebx",
            "    add dl, '0'",
            "    dec ecx",
            "    mov [ecx], dl",
            "    test eax, eax",
            "    jnz .convert_loop",
            "    mov eax, buffer",
            "    add eax, 15",
            "    sub eax, ecx",
            "    mov edx, eax",
            "    mov eax, 4",
            "    mov ebx, 1",
            "    int 0x80",
            "    popad",
            "    ret",
        ]
