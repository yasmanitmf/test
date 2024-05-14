import os

def search_error_in_files():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".txt") or file.endswith(".py"):  # Puedes ajustar las extensiones de archivo según tus necesidades
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    for line_number, line in enumerate(f, 1):
                        if "Error" in line:
                            print(f"Error encontrado en {os.path.join(root, file)} en la línea {line_number}: {line.strip()}")
                            exit(1)  # Termina el script con un código de error

if __name__ == "__main__":
    search_error_in_files()
