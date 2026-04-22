import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="BankScope Intelligence", layout="wide")

st.title("🏛️ BankScope Intelligence: Stratejik Karar Destek Sistemi")

# Temel Veri Bankası
BANKA_VERI = {
    "Akbank": {"ticker": "AKBNK.IS", "grup": "Özel", "ozsermaye": 220e9, "kar": 66e9, "beta": 1.15},
    "Garanti": {"ticker": "GARAN.IS", "grup": "Özel", "ozsermaye": 240e9, "kar": 87e9, "beta": 1.10},
    "İş Bankası": {"ticker": "ISCTR.IS", "grup": "Özel", "ozsermaye": 270e9, "kar": 72e9, "beta": 1.20},
    "Yapı Kredi": {"ticker": "YKBNK.IS", "grup": "Özel", "ozsermaye": 200e9, "kar": 68e9, "beta": 1.18},
    "Vakıfbank": {"ticker": "VAKBN.IS", "grup": "Kamu", "ozsermaye": 180e9, "kar": 25e9, "beta": 0.95},
    "Halkbank": {"ticker": "HALKB.IS", "grup": "Kamu", "ozsermaye": 160e9, "kar": 10e9, "beta": 0.90}
}

@st.cache_data(ttl=3600)
def get_intelligence_data():
    data = []
    usd_ticker = yf.Ticker("TRY=X")
    kur_data = usd_ticker.history(period="1d")
    kur = float(kur_data['Close'].iloc[-1])
    
    for name, info in BANKA_VERI.items():
        t = yf.Ticker(info['ticker'])
        h = t.history(period="1y")
        if h.empty: continue
        
        fiyat = float(h['Close'].iloc[-1])
        # Rasyo Hesaplama
        lot_miktari = {"Akbank": 5.2, "Garanti": 4.2, "İş Bankası": 10.0, "Yapı Kredi": 8.4, "Vakıfbank": 9.9, "Halkbank": 5.0}
        m_cap_tl = fiyat * lot_miktari[name] * 1e9
        pb = m_cap_tl / info['ozsermaye']
        roe = (info['kar'] / info['ozsermaye']) * 100

        # SINYAL ALGORITMASI
        if roe > 40 and pb < 1.0: sinyal = "💎 Ucuz ve Karlı (Fırsat)"
        elif roe < 20 and pb > 1.2: sinyal = "⚠️ Pahalı ve Düşük Karlı"
        else: sinyal = "⚖️ Dengeli Değerleme"

        data.append({
            "Banka": name,
            "Grup": info['grup'],
            "Fiyat (TL)": fiyat,
            "Piyasa Değeri ($ B)": (m_cap_tl / kur) / 1e9,
            "PD/DD": pb,
            "ROE (%)": roe,
            "Beta (Risk Skoru)": info['beta'],
            "Yapay Zeka Sinyali": sinyal
        })
    return pd.DataFrame(data), kur

df, guncel_kur = get_intelligence_data()

# --- ANALİZ PANELİ ---
c1, c2 = st.columns(2)
with c1:
    st.subheader("🎯 ROE vs PD/DD Analizi")
    fig = px.scatter(df, x='PD/DD', y='ROE (%)', size='Piyasa Değeri ($ B)', color='Grup', text='Banka', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📰 Bankacılık KAP Akışı (Haberler)")
    # Dinamik Haber Çekme (Ticker bazlı)
    target_news = st.selectbox("Haberlerini görmek istediğiniz banka:", list(BANKA_VERI.keys()))
    news_ticker = yf.Ticker(BANKA_VERI[target_news]["ticker"])
    for n in news_ticker.news[:5]:
        st.markdown(f"**[{n['publisher']}]** - [{n['title']}]({n['link']})")

# --- SINYAL TABLOSU (HATASIZ) ---
st.divider()
st.subheader("🤖 Algoritmik Analiz Çıktıları")

def color_signals(val):
    if "💎" in val: return 'background-color: #004d1a; color: white;'
    if "⚠️" in val: return 'background-color: #4d0000; color: white;'
    return ''

# applymap yerine map kullanıldı (Hatayı çözen kısım burası kanka)
st.dataframe(df.style.format({
    "Fiyat (TL)": "{:.2f}",
    "Piyasa Değeri ($ B)": "{:.2f}",
    "PD/DD": "{:.2f}",
    "ROE (%)": "{:.1f}%"
}).map(color_signals, subset=['Yapay Zeka Sinyali']), use_container_width=True, height=350)

st.info("**🕵️ Müfettiş Notu:** Sinyal odası, bankaların sermaye yeterliliği ve karlılık anomalilerini anlık tarar. Haber akışı ise temel analizi destekleyen olay tabanlı (event-based) riskleri takip etmenizi sağlar.")
