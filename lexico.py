import re


# separa el texto en tokens
def identificar_tokens(texto):
    especificaciones = [
        ("NUMBER", r"\d+(\.\d+)?"),
        ("STRING", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ("OPERATOR", r"==|!=|>=|<=|&&|\|\||[+\-*/=<>]"),
        ("DELIMITER", r"[(){},;]"),
        ("IDENTIFIER", r"[A-Za-z_ÁÉÍÓÚáéíóúÑñ][A-Za-z0-9_ÁÉÍÓÚáéíóúÑñ]*"),
        ("WHITESPACE", r"\s+"),
        ("MISMATCH", r"."),
    ]

    patron = "|".join(f"(?P<{nombre}>{regex})" for nombre, regex in especificaciones)
    tokens = []

    palabras_reservadas = {
        "inicio", "fin", "si", "entonces", "sino", "finsi", "escribir",
        "entrada", "leer", "int", "float", "void", "return", "main", "print", "printf"
    }

    for coincidencia in re.finditer(patron, texto):
        tipo = coincidencia.lastgroup
        valor = coincidencia.group()

        if tipo == "WHITESPACE":
            continue
        if tipo == "IDENTIFIER" and valor.lower() in palabras_reservadas:
            tokens.append(("KEYWORD", valor))
        elif tipo == "MISMATCH":
            raise Exception(f"Error lexico: caracter no reconocido {valor}")
        else:
            tokens.append((tipo, valor))

    return tokens
