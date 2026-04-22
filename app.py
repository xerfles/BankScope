import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="BankScope Pro+", layout="wide")

st.title("🏛️ BankScope Pro+: İleri Düzey Bankacılık Terminali")

# Veri tabanımızı biraz daha genişletelim (Temettü verimi tahmini ekledik)
BANKA_BILGILERI = {
    "Akbank": {"ticker": "AKBNK.IS", "grup": "Özel", "ozsermaye": 220e9, "ana_kar": 66e9, "temettü": 5.5},
    "Garanti": {"ticker": "GARAN.IS", "grup": "Özel", "ozsermaye": 240e9, "ana_kar": 87e9, "temettü": 6.2},
    "İş Bankası": {"ticker": "ISCTR.IS", "grup": "Özel", "ozsermaye": 270e9, "ana_kar": 72e9, "temettü": 4.8},
    "Yapı Kredi": {"ticker": "YKBNK.IS", "grup": "Özel", "ozsermaye": 200e9, "ana_kar": 68e9, "temettü": 5.0},
    "Vakıfbank": {"ticker": "VAKBN.IS", "grup": "Kamu", "ozsermaye": 180e9, "ana_kar": 25e9, "temettü": 1.5},
    "Halkbank": {"ticker": "HALKB.IS", "grup": "Kamu", "ozsermaye": 160e9, "ana_kar": 10e9, "temettü": 1.0}
}

# --- SIDEBAR: DUYARLILIK ANALİZİ ---
st.sidebar.header("🧪 Stres Testi & Senaryo")
sim_kur = st.sidebar.slider("Dolar Kuru Senaryosu (TRY)", 30.0, 50.0, 32.50)
st.sidebar.info(f"Kur {sim_kur} TL olursa sektörün dolar bazlı büyüklüğü yeniden hesaplanacaktır.")

@st.cache_data(ttl=3600)
def get_bank_ultra_data(kur_manual):
    data = []
    for name, info in BANKA_BILGILERI.items():
        try:
            t = yf.Ticker(info['ticker'])
            h = t.history(period="10y") # Tarihi zirve için uzun çektik
            if h.empty: continue
            
            fiyat = float(h['Close'].iloc[-1])
            zirve_tl = float(h['Close'].max())
            
            # Lot sayıları (Öncekiyle aynı)
            lot_sayilari = {"Akbank": 5.2, "Garanti": 4.2, "İş Bankası": 10.0, "Yapı Kredi": 8.4, "Vakıfbank": 9.9, "Halkbank": 5.0}
            m_cap_tl = fiyat * lot_sayilari[name] * 1e9
            
            pb = m_cap_tl / info['ozsermaye']
            roe = (info['ana_kar'] / info['ozsermaye']) * 100
            uzaklik = ((zirve_tl - fiyat) / zirve_tl) * 100

            data.append({
                "Banka": name,
                "Grup": info['grup'],
                "Fiyat (TL)": fiyat,
                "Simüle Piyasa Değeri ($ B)": (m_cap_tl / kur_manual) / 1e9,
                "PD/DD": pb,
                "ROE (%)": roe,
                "Zirveye Uzaklık (%)": uzaklik,
                "Tahmini Temettü (%)": info['temettü']
            })
        except: continue
    return pd.DataFrame(data)

df = get_bank_ultra_data(sim_kur)

# --- GÖRSELLEŞTİRME ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📉 Tarihi Zirveye Uzaklık (%)")
    # Bu grafik potansiyeli gösterir
    fig_pot = px.bar(df.sort_values("Zirveye Uzaklık (%)"), x="Banka", y="Zirveye Uzaklık (%)", 
                     color="Zirveye Uzaklık (%)", color_continuous_scale="Reds",
                     title="TL Bazlı Zirveden Düşüş (İskonto Oranı)")
    st.plotly_chart(fig_pot, use_container_width=True)

with c2:
    st.subheader("💰 Temettü ve Karlılık Dengesi")
    fig_div = px.scatter(df, x="ROE (%)", y="Tahmini Temettü (%)", size="PD/DD", 
                         color="Banka", text="Banka", title="Hem Karlı Hem Temettü Verenler")
    st.plotly_chart(fig_div, use_container_width=True)

# --- SEKTÖREL KARNE ---
st.divider()
st.subheader("📜 BankScope Stratejik Karne")

# Tabloyu özelleştirilmiş görünümle verelim
st.dataframe(df.style.format({
    "Fiyat (TL)": "{:.2f}",
    "Simüle Piyasa Değeri ($ B)": "{:.2f}",
    "PD/DD": "{:.2f}",
    "ROE (%)": "{:.1f}%",
    "Zirveye Uzaklık (%)": "{:.1f}%",
    "Tahmini Temettü (%)": "{:.1f}%"
}).highlight_min(subset=["PD/DD"], color="#2ecc71") # En ucuz olanı yeşil yak
  .highlight_max(subset=["ROE (%)"], color="#2ecc71"), # En karlı olanı yeşil yak
use_container_width=True)

st.caption(f"⚠️ Not: Veriler {sim_kur} TL kur senaryosuna göre simüle edilmiştir.")
