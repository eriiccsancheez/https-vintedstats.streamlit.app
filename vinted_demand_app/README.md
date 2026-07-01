# Vinted Sneaker Demand Finder

App de Streamlit para analizar demanda de zapatillas en Vinted usando CSV o datos de ejemplo.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Desplegar en Streamlit Cloud

1. Sube estos archivos a un repositorio de GitHub.
2. En Streamlit Cloud pulsa Create app.
3. Selecciona el repositorio.
4. Main file path: `app.py`.
5. Deploy.

## CSV recomendado

Columnas recomendadas:

- `date`
- `model`
- `brand`
- `price`
- `size`
- `status`
- `views`
- `favourites`

