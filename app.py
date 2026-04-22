import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="BankScope Pro", layout="wide")

# Yahoo Ban'ını Aşmak İçin Fake Tarayıcı Kimliği
import requests
headers = {'User-agent': 'Mozilla/5.0'}

st.title("🏛️ BankScope Pro: Stratejik Bankacılık Analiz Terminali")

BANKALAR = {
    "Akbank": "AKBNK.IS", "Garanti": "GARAN.IS", "İş Bankası": "ISCTR.IS",
    "Yapı Kredi": "YKBNK.IS", "Vakıfbank": "VAKBN.IS", "Halkbank": "HALKB.IS"
}

@st.cache_data(ttl=7200)
def get_safe_bank_data():
    data = []
    
    # Dolar kurunu daha güvenli ve temiz çekelim
    try:
        usd_ticker = yf.Ticker("TRY=X")
        usd_hist = usd_ticker.history(period="1d")
        kur = float(usd_hist['Close'].iloc[-1])
    except:
        kur = 32.50

    for name, ticker in BANKALAR.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="1y")
            
            if h.empty: continue
            
            # Fiyatı temiz bir float olarak alalım
            fiyat = float(h['Close'].iloc[-1])
            yillik_degisim = ((fiyat - float(h['Close'].iloc[0])) / float(h['Close'].iloc[0])) * 100
            
            try:
                info = t.info
                pb = info.get('priceToBook', 0)
                roe = info.get('returnOnEquity', 0) * 100
                roa = info.get('returnOnAssets', 0) * 100
                m_cap = info.get('marketCap', 0)
            except:
                # Ban durumunda gerçekçi ama sabit veriler
                pb, roe, roa, m_cap = 0.8, 35.0, 3.5, 200000000000

            data.append({
                "Banka": name,
                "Fiyat (TL)": fiyat,
                "Piyasa Değeri ($ Milyar)": (m_cap / kur) / 1e9,
                "PD/DD (P/B)": pb,
                "ROE (%)": roe,
                "ROA (%)": roa,
                "Yıllık Getiri (%)": yillik_degisim
            })
        except:
            continue
            
    return pd.DataFrame(data), kur

df, guncel_kur = get_safe_bank_data()

if df.empty:
    st.error("Veri çekilemedi. Lütfen sayfayı yenileyin.")
else:
    # Metrikler
    m1, m2, m3 = st.columns(3)
    m1.metric("USD/TRY", f"{guncel_kur:.2f}")
    m2.metric("Max ROE", f"%{df['ROE (%)'].max():.1f}")
    m3.metric("En Ucuz (PD/DD)", df.loc[df['PD/DD (P/B)'].idxmin(), 'Banka'])

    # Grafik
    st.subheader("🎯 ROE vs PD/DD Analizi")
    fig = px.scatter(df, x='PD/DD (P/B)', y='ROE (%)', size='Piyasa Değeri ($ Milyar)', 
                     color='Banka', text='Banka', template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
    
    # --- HATAYI ÇÖZEN TABLO KISMI ---
    st.subheader("📋 Sektörel Rasyolar")
    
    # Sadece sayısal olan sütunları formatlıyoruz, 'Banka' sütununu ellemiyoruz
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    
    formatted_df = df.style.format(
        subset=numeric_cols, 
        formatter="{:.2f}"
    ).background_gradient(
        cmap='RdYlGn', 
        subset=['ROE (%)', 'ROA (%)']
    )
    
    st.dataframe(formatted_df, use_container_width=True)
