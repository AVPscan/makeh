"""
Автор: Поздняков Алексей Васильевич
Email: avp70ru@mail.ru
GitHub: @AVPscan
Лицензия: Apache-2.0
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os

def generate_professional_header(c_file_path):
    if not os.path.exists(c_file_path):
        print(f"Ошибка: Файл {c_file_path} не найден.")
        return
    with open(c_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    h_file_path = c_file_path.replace('.c', '.h')
    h_name = os.path.basename(h_file_path)
    guard = h_name.replace('.', '_').upper()
    top_comment = ""
    first_comment_match = re.search(r'^\s*/\*.*?\*/', content, re.DOTALL)
    if first_comment_match:
        top_comment = first_comment_match.group(0).strip() + "\n\n"
    headers_and_defines = []
    macro_pattern = re.compile(r'^\s*#.*?(?:\\\n.*?)*$', re.MULTILINE)
    for match in macro_pattern.finditer(content):
        headers_and_defines.append(match.group(0).strip())
    prototypes = []
    buffer = ""
    brace_level = 0
    in_string = False
    in_comment = False
    i = 0
    base_types = ('int', 'char', 'long', 'float', 'double', 'uint', 'size_t', 'ssize_t', 'unsigned', 'short')
    while i < len(content):
        char = content[i]
        if not in_comment and not in_string:
            if content[i:i+2] == '/*': in_comment = True; i += 2; continue
            if content[i:i+2] == '//':
                while i < len(content) and content[i] != '\n': i += 1
                continue
            if char == '"': in_string = True; i += 1; continue
            if char == '#': # Директивы сбрасывают буфер захвата кода
                buffer = "" 
                while i < len(content) and content[i] != '\n': i += 1
                continue
        elif in_comment:
            if content[i:i+2] == '*/': in_comment = False; i += 2
            else: i += 1
            continue
        elif in_string:
            if char == '\\': i += 2; continue
            if char == '"': in_string = False
            i += 1; continue
        if char == '{':
            if brace_level == 0:
                sig = ' '.join(buffer.strip().split())
                if '(' in sig and ')' in sig:
                    if not sig.startswith(('if', 'for', 'while', 'switch', 'else')) and \
                       'static' not in sig and 'main' not in sig:
                        prototypes.append(f"extern {sig};")
                elif sig.startswith(('struct', 'typedef struct', 'enum', 'typedef enum', 'union')):
                    depth = 1
                    j = i + 1
                    while j < len(content) and depth > 0:
                        if content[j] == '{': depth += 1
                        if content[j] == '}': depth -= 1
                        j += 1
                    while j < len(content) and content[j] != ';': j += 1
                    if j < len(content) and content[j] == ';': j += 1
                    full_struct = sig + " " + content[i:j].strip()
                    prototypes.append(full_struct)
                    i = j; buffer = ""; continue
            brace_level += 1
            buffer = ""
        elif char == '}':
            brace_level -= 1
            buffer = ""
        elif char == ';':
            if brace_level == 0:
                sig = ' '.join(buffer.strip().split())
                if sig:
                    # А) Глобальные переменные (например, int enc_mode = 0;)
                    if any(sig.startswith(t) for t in base_types) and '(' not in sig and 'static' not in sig:
                        # Если есть инициализация (=), отрезаем её для заголовочного файла
                        clean_var = sig.split('=')[0].strip()
                        prototypes.append(f"extern {clean_var};")
                    # Б) Простые typedef (например, typedef int MyInt;)
                    elif sig.startswith('typedef') and '{' not in sig:
                        prototypes.append(f"{sig};")
                buffer = ""
        else:
            if brace_level == 0:
                buffer += char
        i += 1
    with open(h_file_path, 'w', encoding='utf-8') as f:
        f.write(top_comment)
        f.write(f"#ifndef {guard}\n#define {guard}\n\n#ifdef __cplusplus\nextern \"C\" {{\n#endif\n\n")
        if headers_and_defines:
            f.write("\n".join(headers_and_defines) + "\n\n")
        if prototypes:
            f.write("\n".join(prototypes) + "\n")
        f.write("\n#ifdef __cplusplus\n}\n#endif\n")
        f.write(f"#endif // {guard}\n")
    print(f"Успешно сгенерировано: {h_file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_professional_header(sys.argv[1])
    else:
        print("Использование: python makeh.py <file.c>")

