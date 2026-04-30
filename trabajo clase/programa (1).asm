section .data
    salto_linea db 0xA
section .bss
    buffer resb 16
    x:    resd 1

section .text
global _start
main:

    mov eax, 15
    mov dword [x], eax

    mov eax, dword [x]
    call print_int
    call print_newline

    mov eax, 0
    ret

_start:
    call main
    mov eax, 1    ; syscall exit
    xor ebx, ebx  ; Codigo de Salida 0
    int 0x80

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
