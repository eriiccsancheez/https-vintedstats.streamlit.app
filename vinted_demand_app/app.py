import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title='Vinted Sneaker Demand', page_icon='👟', layout='wide')

st.markdown('''
<style>
.main {background-color:#0f1117; color:white;}
.block-container {padding-top:2rem;}
.metric-card {background:#161b22; padding:18px; border-radius:16px; border:1px solid #30363d;}
.small {color:#8b949e; font-size:14px;}
</style>
''', unsafe_allow_html=True)

st.title('👟 Vinted Sneaker Demand Finder')
st.caption('Buscador para detectar modelos con demanda, precio medio y oportunidad de reventa.')

@st.cache_data
def load_demo_data():
    rows = []
    base_date = datetime.today().date() - timedelta(days=29)
    models = [
        ('Adidas Samba OG', 'adidas', 44, 23, 42),
        ('Adidas Campus 00s', 'adidas', 57, 18, 43),
        ('Adidas Gazelle', 'adidas', 39, 14, 42),
        ('Nike Air Force 1', 'nike', 52, 31, 41),
        ('Nike Dunk Low Panda', 'nike', 68, 21, 42),
        ('Nike TN Air Max Plus', 'nike', 91, 16, 43),
        ('Jordan 4 Retro', 'jordan', 158, 12, 42),
        ('New Balance 530', 'new balance', 48, 15, 39),
        ('Asics Gel-Kayano 14', 'asics', 83, 9, 42),
        ('Onitsuka Tiger Mexico 66', 'onitsuka', 62, 8, 40),
    ]
    for model, brand, avg_price, daily_sales, top_size in models:
        for i in range(30):
            date = base_date + timedelta(days=i)
            seasonal = 1 + ((i % 7) - 3) / 18
            sales = max(0, int(daily_sales * seasonal))
            price = round(avg_price * (1 + ((i % 5) - 2) / 25), 2)
            views = sales * 18 + (i % 9) * 7
            favourites = sales * 4 + (i % 6) * 3
            listings = max(8, int(sales * 2.2 + (i % 10)))
            rows.append({
                'date': date,
                'model': model,
                'brand': brand,
                'avg_price_eur': price,
                'sales': sales,
                'views': views,
                'favourites': favourites,
                'active_listings': listings,
                'top_size': top_size,
            })
    return pd.DataFrame(rows)

def score_demand(row):
    sell_through = row['sales'] / max(row['active_listings'], 1)
    heat = row['sales'] * 3 + row['favourites'] * 0.4 + row['views'] * 0.05 + sell_through * 30
    return round(min(100, heat), 1)

def recommendation(score, sell_through, avg_price):
    if score >= 80 and sell_through >= 0.35:
        return 'Comprar rápido si el precio está por debajo del mercado'
    if score >= 60:
        return 'Buena demanda; comprar solo con margen claro'
    if score >= 40:
        return 'Demanda media; riesgo moderado'
    return 'Demanda baja; evitar salvo chollo'

uploaded = st.sidebar.file_uploader('Sube tu CSV de ventas de Vinted', type=['csv'])
st.sidebar.markdown('''
**Columnas recomendadas:**
`date`, `model`, `brand`, `price`, `size`, `status`, `views`, `favourites`

Si no subes CSV, la app usa datos de ejemplo.
''')

if uploaded:
    raw = pd.read_csv(uploaded)
    df = raw.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    if 'price' in df.columns and 'avg_price_eur' not in df.columns:
        df['avg_price_eur'] = pd.to_numeric(df['price'], errors='coerce')
    if 'sales' not in df.columns:
        if 'status' in df.columns:
            df['sales'] = df['status'].astype(str).str.lower().isin(['sold','vendido','sold_out']).astype(int)
        else:
            df['sales'] = 1
    if 'active_listings' not in df.columns:
        df['active_listings'] = 1
    if 'views' not in df.columns:
        df['views'] = 0
    if 'favourites' not in df.columns:
        df['favourites'] = 0
    if 'brand' not in df.columns:
        df['brand'] = 'desconocida'
    if 'top_size' not in df.columns and 'size' in df.columns:
        df['top_size'] = df['size']
else:
    df = load_demo_data()

query = st.text_input('Buscar zapatilla', placeholder='Ej: Adidas Samba, Nike TN, Jordan 4...')
brand_filter = st.multiselect('Filtrar marca', sorted(df['brand'].dropna().unique()))

filtered = df.copy()
if query:
    filtered = filtered[filtered['model'].str.contains(query, case=False, na=False)]
if brand_filter:
    filtered = filtered[filtered['brand'].isin(brand_filter)]

if filtered.empty:
    st.warning('No hay resultados para esa búsqueda.')
    st.stop()

summary = filtered.groupby('model').agg(
    brand=('brand','first'),
    avg_price_eur=('avg_price_eur','mean'),
    total_sales=('sales','sum'),
    avg_daily_sales=('sales','mean'),
    total_views=('views','sum'),
    total_favourites=('favourites','sum'),
    active_listings=('active_listings','mean'),
    top_size=('top_size', lambda x: x.mode().iloc[0] if len(x.mode()) else '')
).reset_index()

summary['sell_through'] = summary['avg_daily_sales'] / summary['active_listings'].clip(lower=1)
summary['demand_score'] = summary.apply(score_demand, axis=1)
summary['recommendation'] = summary.apply(lambda r: recommendation(r['demand_score'], r['sell_through'], r['avg_price_eur']), axis=1)
summary = summary.sort_values('demand_score', ascending=False)

best = summary.iloc[0]
col1, col2, col3, col4 = st.columns(4)
col1.metric('Modelo más caliente', best['model'])
col2.metric('Precio medio', f"{best['avg_price_eur']:.0f} €")
col3.metric('Ventas/día', f"{best['avg_daily_sales']:.1f}")
col4.metric('Score demanda', f"{best['demand_score']}/100")

st.subheader('Ranking de demanda')
st.dataframe(
    summary.rename(columns={
        'model':'Modelo', 'brand':'Marca', 'avg_price_eur':'Precio medio €',
        'total_sales':'Ventas 30 días', 'avg_daily_sales':'Ventas/día',
        'total_views':'Visualizaciones', 'total_favourites':'Favoritos',
        'active_listings':'Anuncios activos', 'top_size':'Talla top',
        'sell_through':'Ratio venta/anuncios', 'demand_score':'Demanda',
        'recommendation':'Recomendación'
    }),
    use_container_width=True,
    hide_index=True
)

selected = st.selectbox('Analizar modelo', summary['model'])
model_df = filtered[filtered['model'] == selected]

c1, c2 = st.columns(2)
with c1:
    daily = model_df.groupby('date', as_index=False).agg(sales=('sales','sum'), avg_price_eur=('avg_price_eur','mean'))
    fig = px.line(daily, x='date', y='sales', markers=True, title=f'Ventas diarias - {selected}')
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig2 = px.line(daily, x='date', y='avg_price_eur', markers=True, title=f'Precio medio - {selected}')
    st.plotly_chart(fig2, use_container_width=True)

if 'size' in model_df.columns:
    size_data = model_df.groupby('size', as_index=False).agg(sales=('sales','sum')).sort_values('sales', ascending=False)
else:
    size_data = pd.DataFrame({'size':[best['top_size']], 'sales':[best['total_sales']]})

st.subheader('Tallas con más demanda')
st.bar_chart(size_data.set_index('size'))

csv = summary.to_csv(index=False).encode('utf-8')
st.download_button('Descargar ranking en CSV', csv, 'ranking_demanda_vinted.csv', 'text/csv')

st.info('Nota: esta app no extrae datos automáticamente de Vinted. Para datos reales debes importar un CSV propio o conectar una fuente de datos permitida.')
