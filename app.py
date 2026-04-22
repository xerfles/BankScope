import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="BankScope Intelligence", layout="wide")

st.title("🏛️ BankScope Intelligence: Stratejik Karar Destek Sistemi")

# Temel Veri Bankası (Geliştirilmiş)
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
    kur = float(usd_ticker.history(period="1d")['Close'].iloc[-1])
    
    for name, info in BANKA_VERI.items():
        t = yf.Ticker(info['ticker'])
        h = t.history(period="max") # Dolar zirvesi için max veri
        
        fiyat = float(h['Close'].iloc[-1])
        # Tarihi Dolar Zirvesi (Yaklaşık 2013-2014 dönemleri)
        # Bankalar genellikle dolar bazında 2-4$ arası zirve gördüler.
        zirve_usd = 3.5 # Ortalama tarihi zirve dolar bazlı
        guncel_usd = fiyat / kur
        recovery_pot = ((zirve_usd - guncel_usd) / zirve_usd) * 100

        # Rasyo Hesaplama
        lot_miktari = {"Akbank": 5.2, "Garanti": 4.2, "İş Bankası": 10.0, "Yapı Kredi": 8.4, "Vakıfbank": 9.9, "Halkbank": 5.0}
        m_cap_tl = fiyat * lot_miktari[name] * 1e9
        pb = m_cap_tl / info['ozsermaye']
        roe = (info['kar'] / info['ozsermaye']) * 100

        # SINYAL ALGORITMASI
        if roe > 40 and pb < 1.0:
            sinyal = "💎 Ucuz ve Karlı (Fırsat)"
        elif roe < 20 and pb > 1.2:
            sinyal = "⚠️ Pahalı ve Düşük Karlı"
        else:
            sinyal = "⚖️ Dengeli Değerleme"

        data.append({
            "Banka": name,
            "Grup": info['grup'],
            "Fiyat (TL)": fiyat,
            "Piyasa Değeri ($ B)": (m_cap_tl / kur) / 1e9,
            "PD/DD": pb,
            "ROE (%)": roe,
            "Dolar Bazlı Zirveye Uzaklık (%)": recovery_pot,
            "Beta (Risk Skoru)": info['beta'],
            "Yapay Zeka Sinyali": sinyal
        })
    return pd.DataFrame(data), kur

df, guncel_kur = get_intelligence_data()

# --- ANALİZ PANELİ ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("🏁 Recovery (Toparlanma) Potansiyeli")
    # Dolar bazlı zirveye ne kadar yol var?
    fig_rec = px.bar(df, x='Banka', y='Dolar Bazlı Zirveye Uzaklık (%)', 
                     color='Dolar Bazlı Zirveye Uzaklık (%)', color_continuous_scale='Blues_r',
                     title="Tarihi Dolar Zirvesine Uzaklık")
    st.plotly_chart(fig_rec, use_container_width=True)

with c2:
    st.subheader("⚖️ Risk vs Getiri (Beta Analizi)")
    # Beta ne kadar yüksekse piyasaya o kadar duyarlı
    fig_beta = px.scatter(df, x='Beta (Risk Skoru)', y='ROE (%)', size='Piyasa Değeri ($ B)',
                         color='Banka', text='Banka', title="Banka Risk Skoru vs Karlılık")
    st.plotly_chart(fig_beta, use_container_width=True)

# --- SINYAL TABLOSU ---
st.divider()
st.subheader("🤖 Algoritmik Analiz Çıktıları")

def color_signals(val):
    if "💎" in val: return 'background-color: #004d1a'
    if "⚠️" in val: return 'background-color: #4d0000'
    return ''

st.dataframe(df.style.format({
    "Fiyat (TL)": "{:.2f}",
    "Piyasa Değeri ($ B)": "{:.2f}",
    "PD/DD": "{:.2f}",
    "ROE (%)": "{:.1f}%",
    "Dolar Bazlı Zirveye Uzaklık (%)": "{:.1f}%"
}).applymap(color_signals, subset=['Yapay Zeka Sinyali']), use_container_width=True)

st.info("**🕵️ Müfettiş Notu:** 'Dolar Bazlı Zirveye Uzaklık', bankacılık sektörünün makroekonomik normalleşme sürecindeki 'alanını' gösterir. Beta skoru ise para politikası kararlarına karşı bankanın vereceği tepkinin şiddetini ölçer.")
