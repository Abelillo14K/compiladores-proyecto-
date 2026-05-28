section .data
    x_global dd 10
    x_bloque_3 dd 5
section .bss
    y_test_2 resd 1
section .text
global _start
_start:
    mov eax, [y_test_2]
    add eax, [x_bloque_3]
    mov [y_test_2], eax
    mov eax, 1
    xor ebx, ebx
    int 0x80
