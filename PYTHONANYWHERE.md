# Deploy en PythonAnywhere (Gratuito)

PythonAnywhere gratuito soporta procesos persistentes (a diferencia de Vercel serverless), por lo que el estado en memoria se conserva entre requests.

## Paso 1: Subir el código

### Opción A: Git (recomendado)
1. Ve a https://www.pythonanywhere.com → Consoles → Bash
2. Ejecuta:
```bash
git clone <URL_DE_TU_REPO>
cd frontierChallenge
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Opción B: Upload directo
1. Ve a https://www.pythonanywhere.com → Files
2. Crea carpeta `frontierChallenge`
3. Sube todos los archivos del repo

## Paso 2: Configurar Web App

1. Ve a Web → Add a new web app
2. Selecciona **"Manual configuration"**
3. Selecciona **Python 3.12**
4. Click en el link del archivo WSGI (ej: `/var/www/tuusuario_pythonanywhere_com_wsgi.py`)
5. Reemplaza TODO el contenido por:

```python
import sys
path = '/home/TU_USUARIO/frontierChallenge'
if path not in sys.path:
    sys.path.append(path)

from pythonanywhere_wsgi import application
```

6. Ve a la pestaña **Virtualenv** en la misma página
7. Escribe: `/home/TU_USUARIO/frontierChallenge/venv`
8. Click en **Reload**

## Paso 3: Verificar

Tu app estará disponible en:
```
https://TU_USUARIO.pythonanywhere.com
```

Prueba:
```bash
curl https://TU_USUARIO.pythonanywhere.com/health \
  -H "Authorization: Bearer test-token"
```

## Notas importantes

- **Estado persistente**: A diferencia de Vercel, PythonAnywhere mantiene el proceso corriendo, así que el estado en memoria (`dict` de cuentas/operaciones) se conserva entre requests.
- **Sleep**: El plan gratuito "duerme" la app después de inactividad. La primera request tras dormir tarda ~2-5 segundos en despertarla. Pero el estado se mantiene.
- **Requisitos**: El archivo `requirements.txt` incluye `a2wsgi` que adapta FastAPI (ASGI) a WSGI para PythonAnywhere.

## Troubleshooting

### Error "No module named 'src'"
Asegúrate de que el `path` en el archivo WSGI apunta correctamente a la carpeta `frontierChallenge` donde está el código.

### Error 500
Ve a Web → Error log para ver el traceback.
