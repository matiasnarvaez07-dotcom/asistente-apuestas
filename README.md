# Web MVP - Asistente de análisis deportivo

Esta es una versión web simple para usar desde iPad, iPhone o computador.

## Qué hace

- Permite ingresar un partido manualmente.
- Permite ingresar cuotas Betsson o de otra casa.
- Calcula probabilidad implícita de mercado.
- Calcula probabilidad propia con:
  - Poisson/xG
  - ELO
  - Forma reciente
  - Contexto neutro
- Calcula diferencia modelo vs mercado.
- Aplica filtros:
  - Señal vs ruido
  - Consenso
  - IGC
  - Muestra mínima
  - Anomalías
- Guarda historial en SQLite.
- Muestra resultados en una interfaz web responsive.

## Importante

Esta MVP no garantiza ganancias. Solo muestra posibles discrepancias estadísticas entre modelo y mercado.

## Instalación local

```bash
cd web_mvp_asistente_apuestas
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Luego abrir:

```text
http://127.0.0.1:5000
```

## Uso desde iPad/iPhone

La forma más cómoda es subirla a Render o Railway. Luego podrás abrirla desde Safari.

## Subir a Render

1. Crear cuenta en Render.
2. Crear nuevo Web Service.
3. Subir este proyecto a GitHub.
4. Conectar GitHub con Render.
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
gunicorn app:app
```

## Archivos principales

- `app.py`: servidor Flask.
- `analysis_engine.py`: motor estadístico.
- `database.py`: SQLite.
- `templates/index.html`: pantalla principal.
- `templates/history.html`: historial.
- `static/style.css`: diseño.
- `requirements.txt`: dependencias.

## Nota sobre Betsson

La web permite ingresar cuotas Betsson manualmente. Para conectar Betsson automáticamente se requiere proveedor de odds compatible o integración autorizada.
