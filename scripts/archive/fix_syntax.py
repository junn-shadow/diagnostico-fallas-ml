with open("app/dashboard/streamlit_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Buscamos la separacion
parts = content.split("\nwith tab_history:\n")

if len(parts) == 2:
    part1 = parts[0]
    part2 = parts[1]
    
    # Dentro de part2, el bloque else esta al final
    part2_lines = part2.split("\nelse:\n")
    if len(part2_lines) == 2:
        history_logic = part2_lines[0]
        else_logic = part2_lines[1]
        
        new_content = part1 + "\nelse:\n" + else_logic + "\nwith tab_history:\n" + history_logic
        
        with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Corregido exitosamente")
    else:
        print("No se encontró el bloque else")
else:
    print("No se encontró with tab_history")

