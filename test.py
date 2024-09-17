import importlib.util
import sys
from unittest.mock import MagicMock

# Simula las dependencias innecesarias en 'formulario.py'
sys.modules['flask_wtf'] = MagicMock()
sys.modules['wtforms'] = MagicMock()
sys.modules['wtforms.validators'] = MagicMock()

# Ruta al archivo desde el cual quieres importar la clase
archivo = 'forms.py'

# Nombre del módulo (puede ser cualquier nombre válido)
nombre_modulo = 'mi_modulo_temporal'

# Especificación del módulo
spec = importlib.util.spec_from_file_location(nombre_modulo, archivo)
# Crear el módulo desde la especificación
modulo = importlib.util.module_from_spec(spec)
# Registrar el módulo en sys.modules
sys.modules[nombre_modulo] = modulo
# Ejecutar el módulo para cargar su contenido
spec.loader.exec_module(modulo)

# Extraer la clase RegistrationForm
RegistrationForm = modulo.RegistrationForm

# Crear una instancia ficticia de Field para pasarla a la función validate_password
class FakeField:
    def __init__(self, data):
        self.data = data

# Función para probar diferentes contraseñas
def probar_passwords(passwords):
    for password in passwords:
        fake_field = FakeField(password)
        try:
            form = RegistrationForm()
            form.validate_password(fake_field)
            print(f"'{password}' es válido.")
        except Exception as e:
            print(f"'{password}' no es válido: {e}")

# Lista de contraseñas para probar
passwords = [
    'Short7!',
    'alllowercase7!',
    'NOLOWERCASE7!',
    'NoDigit!',
    'NoSpecial7',
    'ValidPass7!'
]

probar_passwords(passwords)
