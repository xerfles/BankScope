import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="BankScope Pro", layout="wide")

# Kurumsal Tema Ayarları
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ BankScope Pro: Stratejik Bankacılık Analiz Terminali")
st.sidebar.title("🛠️ Veri Yönetimi")

BANKALAR = {
    "Akbank": "AKBNK.IS", "Garanti": "GARAN.IS", "İş Bankası": "ISCTR.IS",
    "Yapı Kredi": "YKBNK.IS", "Vakıfbank": "VAKBN.IS", "Halkbank": "HALKB.IS"
}

@st.cache_data(ttl=3600)
def get_bank_pro_data():
    usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
    data = []
    for name, ticker in BANKALAR.items():
        t = yf.Ticker(ticker)
        info = t.info
        
        # Profesyonel Bankacılık Metrikleri
        # Not: yfinance bazı rasyoları doğrudan 'info' içinde sunar. 
        # Marj verileri bazen 'operatingMargins' veya 'profitMargins' olarak çekilebilir.
        data.append({
            "Banka": name,
            "Piyasa Değeri ($ Milyar)": (info.get('marketCap', 0) / usd_try) / 1e9,
            "PD/DD (P/B)": info.get('priceToBook', 0),
            "Özsermaye Karlılığı (ROE %)": info.get('returnOnEquity', 0) * 100,
            "Aktif Karlılığı (ROA %)": info.get('returnOnAssets', 0) * 100,
            "Net Faiz Marjı (NIM-Est %)": info.get('operatingMargins', 0) * 100,
            "F/K (P/E)": info.get('trailingPE', 0),
            "Fiyat (TL)": info.get('currentPrice', 0)
        })
    return pd.DataFrame(data), usd_try

with st.spinner('Bankacılık rasyoları ve bilanço verileri analiz ediliyor...'):
    df, kur = get_bank_pro_data()

# --- ÜST ÖZET PANELİ ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("📌 USD/TRY Kuru", f"{kur:.4f} ₺")
m2.metric("📊 Sektör PD/DD Ort.", f"{df['PD/DD (P/B)'].mean():.2f}")
m3.metric("📈 Max ROE", f"%{df['Özsermaye Karlılığı (ROE %)'].max():.1f}", df.loc[df['Özsermaye Karlılığı (ROE %)'].idxmax(), 'Banka'])
m4.metric("💰 Toplam Sektör Değeri", f"${df['Piyasa Değeri ($ Milyar)'].sum():.1f} B")

st.divider()

# --- ANA ANALİZ GRAFİKLERİ ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("🎯 Değerleme ve Karlılık Matrisi")
    # Balon Grafiği: Bir bankanın hem ucuz olup hem de çok kar edip etmediğini gösterir
    fig_matrix = px.scatter(df, x='PD/DD (P/B)', y='Özsermaye Karlılığı (ROE %)', 
                            size='Piyasa Değeri ($ Milyar)', color='Banka',
                            text='Banka', title="ROE vs PD/DD (Verimlilik/Değerleme Dengesi)")
    fig_matrix.add_hline(y=df['Özsermaye Karlılığı (ROE %)'].mean(), line_dash="dot", annotation_text="Ort. ROE")
    fig_matrix.add_vline(x=df['PD/DD (P/B)'].mean(), line_dash="dot", annotation_text="Ort. PD/DD")
    st.plotly_chart(fig_matrix, use_container_width=True)

with c2:
    st.subheader("💸 Net Faiz Marjı Tahmini (%)")
    # Bar Grafiği: Operasyonel verimlilik
    fig_nim = px.bar(df.sort_values('Net Faiz Marjı (NIM-Est %)', ascending=False), 
                     x='Banka', y='Net Faiz Marjı (NIM-Est %)', color='Net Faiz Marjı (NIM-Est %)',
                     color_continuous_scale='Viridis', title="Tahmini Marj Yapısı")
    st.plotly_chart(fig_nim, use_container_width=True)

# --- KARŞILAŞTIRMALI TABLO ---
st.divider()
st.subheader("📋 Detaylı Sektörel Rasyo Tablosu")

# Tabloyu renklendirerek en iyi verileri vurgulayalım
styled_df = df.style.format({
    "Piyasa Değeri ($ Milyar)": "{:.2f}",
    "PD/DD (P/B)": "{:.2f}",
    "Özsermaye Karlılığı (ROE %)": "{:.1f}%",
    "Aktif Karlılığı (ROA %)": "{:.2f}%",
    "Net Faiz Marjı (NIM-Est %)": "{:.1f}%",
    "F/K (P/E)": "{:.2f}",
    "Fiyat (TL)": "{:.2f}"
}).background_gradient(cmap='RdYlGn', subset=['Özsermaye Karlılığı (ROE %)', 'Aktif Karlılığı (ROA %)'])

st.dataframe(styled_df, use_container_width=True)

# --- PROFESYONEL ANALİZ NOTU ---
st.info("""
**🔍 Müfettiş Gözüyle Analiz:** - **DuPont Analizi:** ROE oranının yüksekliği, bankanın kaldıracı mı yoksa operasyonel verimliliği mi kullandığını gösterir.
- **PD/DD vs ROE:** PD/DD oranı sektör ortalamasının altında, ROE oranı ise üstünde olan bankalar 'Pozitif Ayrışma' sinyali verir.
""")
