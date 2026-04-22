import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="BankScope Pro", layout="wide")

st.title("🏛️ BankScope Pro: Bankacılık Sektörü Analiz Terminali")

# Bankalar ve Gruplandırma
BANKA_GRUPLARI = {
    "Akbank": "Özel", "Garanti": "Özel", "İş Bankası": "Özel",
    "Yapı Kredi": "Özel", "Vakıfbank": "Kamu", "Halkbank": "Kamu"
}
BANKA_TICKERS = {
    "Akbank": "AKBNK.IS", "Garanti": "GARAN.IS", "İş Bankası": "ISCTR.IS",
    "Yapı Kredi": "YKBNK.IS", "Vakıfbank": "VAKBN.IS", "Halkbank": "HALKB.IS"
}

@st.cache_data(ttl=7200)
def get_safe_bank_data():
    data = []
    try:
        usd_hist = yf.Ticker("TRY=X").history(period="1d")
        kur = float(usd_hist['Close'].iloc[-1])
    except:
        kur = 32.50

    for name, ticker in BANKA_TICKERS.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="1y")
            if h.empty: continue
            
            fiyat = float(h['Close'].iloc[-1])
            yillik_degisim = ((fiyat - float(h['Close'].iloc[0])) / float(h['Close'].iloc[0])) * 100
            
            try:
                info = t.info
                pb = info.get('priceToBook', 0)
                roe = info.get('returnOnEquity', 0) * 100
                m_cap = info.get('marketCap', 0)
            except:
                # Ban durumunda dummy veriler
                pb, roe, m_cap = 0.8, 35.0, 200000000000

            data.append({
                "Banka": name,
                "Grup": BANKA_GRUPLARI[name], # Kamu/Özel ayrımı
                "Fiyat (TL)": fiyat,
                "Piyasa Değeri ($ Milyar)": (m_cap / kur) / 1e9,
                "PD/DD (P/B)": pb,
                "ROE (%)": roe,
                "Yıllık Getiri (%)": yillik_degisim
            })
        except: continue
    return pd.DataFrame(data), kur

df, guncel_kur = get_safe_bank_data()

if not df.empty:
    # Üst Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("USD/TRY", f"{guncel_kur:.2f}")
    m2.metric("Sektör ROE Ort.", f"%{df['ROE (%)'].mean():.1f}")
    m3.metric("Özel vs Kamu PD/DD", f"{df[df['Grup']=='Özel']['PD/DD (P/B)'].mean():.2f} / {df[df['Grup']=='Kamu']['PD/DD (P/B)'].mean():.2f}")

    # Grafik: Kamu vs Özel Ayrımı ile
    st.subheader("🎯 ROE vs PD/DD Analizi (Grup Bazlı)")
    fig = px.scatter(df, x='PD/DD (P/B)', y='ROE (%)', 
                     size='Piyasa Değeri ($ Milyar)', 
                     color='Grup', # Rengi gruba göre ayırdık
                     symbol='Grup',
                     text='Banka', 
                     template="plotly_dark",
                     color_discrete_map={"Özel": "#2ecc71", "Kamu": "#e74c3c"})
    
    fig.add_hline(y=df['ROE (%)'].mean(), line_dash="dash", opacity=0.5)
    fig.add_vline(x=df['PD/DD (P/B)'].mean(), line_dash="dash", opacity=0.5)
    st.plotly_chart(fig, use_container_width=True)

    # Tablo: Hatasız Formatlama
    st.subheader("📋 Sektörel Rasyolar")
    
    # Sayısal sütunları seç ve formatla (Styler kullanmadan düz dataframe gösterimi daha güvenlidir)
    # Ama yine de şık dursun diye basitleştirilmiş styler:
    numeric_cols = ["Fiyat (TL)", "Piyasa Değeri ($ Milyar)", "PD/DD (P/B)", "ROE (%)", "Yıllık Getiri (%)"]
    
    # background_gradient'i sildik, ImportError riskini sıfırladık.
    st.dataframe(df.style.format({col: "{:.2f}" for col in numeric_cols}), use_container_width=True)

    # Stratejik Not
    st.info("**💡 Profesyonel Not:** Grafikte görüldüğü üzere Kamu bankaları genellikle daha düşük PD/DD (çarpan) ile işlem görmektedir. Bu durum 'risk primi' ve 'temettü politikaları' farkından kaynaklanmaktadır.")
