import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import json
import os
import time
import hashlib
import uuid

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Portföy Analiz ve Yönetimi", layout="wide", page_icon="📊")

# =========================================================================================
# --- GELİŞMİŞ UI / UX TASARIMI (PREMIUM ARAYÜZ MÜHENDİSLİĞİ) ---
# =========================================================================================
st.markdown("""
<style>
    /* Google Fonts'tan Modern Bir Font (Inter) Çekiyoruz */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* Tüm Sayfaya Fontu ve Özel Arka Plan Gradiyanını Uyguluyoruz */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #131d2b 0%, #0b0f19 100%) !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0e131f !important;
        border-right: 1px solid rgba(0, 255, 255, 0.05) !important;
    }

    /* Glassmorphism (Buzlu Cam) Metrik Kartları */
    div[data-testid="metric-container"] {
        background: rgba(20, 26, 36, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0, 255, 255, 0.15) !important;
        padding: 20px !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: all 0.4s ease-in-out !important;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-7px) !important;
        border-color: rgba(0, 255, 255, 0.6) !important;
        box-shadow: 0 12px 40px 0 rgba(0, 255, 255, 0.15) !important;
    }

    /* Genel Buton Tasarımları (Neon Glow Etkisi) */
    div.stButton > button {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #fff !important;
        border: 1px solid rgba(0, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        border-color: #00ffff !important;
        color: #00ffff !important;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.3), inset 0 0 10px rgba(0, 255, 255, 0.1) !important;
        transform: scale(1.03) !important;
    }

    /* Sekme (Tabs) Tasarımını Modernleştirme */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        color: #667085 !important;
        transition: all 0.3s ease !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00ffff !important;
        border-bottom: 3px solid #00ffff !important;
        background-color: rgba(0, 255, 255, 0.05) !important;
        border-radius: 8px 8px 0 0 !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #e2e8f0 !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
    }

    /* Girdi Kutuları (Input, Select) Odaklanma Efektleri */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], input[type="password"] {
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="select"] > div:hover, input[type="text"]:focus, input[type="number"]:focus, input[type="password"]:focus {
        border-color: #00ffff !important;
        box-shadow: 0 0 8px rgba(0,255,255,0.4) !important;
    }

    /* Komisyon Bağış Panosu (Geliştirilmiş) */
    .bagis-panosu {
        text-align: center; 
        padding: 25px; 
        background: linear-gradient(135deg, rgba(255,215,0,0.1) 0%, rgba(255,140,0,0.1) 100%); 
        border-radius: 16px; 
        border: 1px solid rgba(255,215,0,0.4); 
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(255, 215, 0, 0.08);
        backdrop-filter: blur(8px);
    }
    .bagis-sayi {
        color: #FFD700; 
        font-size: 34px; 
        font-weight: 800; 
        text-shadow: 0 0 20px rgba(255,215,0,0.5);
        letter-spacing: 1.5px;
    }

    /* TÜM RADIO BUTONLARINI MODERN KARTLARA ÇEVİRME (HİZALAMA DÜZELTİLDİ) */
    div.stRadio div[role="radiogroup"] {
        display: flex !important;
        width: 100% !important;
        align-items: stretch !important; /* Butonların konteyneri tam kaplamasını sağlar */
    }
    div.stRadio div[role="radiogroup"] > label {
        width: 100% !important; /* Genişliği kesin olarak 100% sabitler */
        min-height: 45px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        padding: 5px 10px !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        background-color: #0f172a !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    div.stRadio div[role="radiogroup"] > label > div:first-child {
        display: none !important; /* Yuvarlak seçeneği gizler */
    }
    div.stRadio div[role="radiogroup"] > label p {
        margin: 0 !important;
        font-size: 14px !important;
        width: 100% !important; /* Yazının butona ortalanmasını sağlar */
    }
    div.stRadio div[role="radiogroup"] > label:hover {
        border-color: #00ffff !important;
        background-color: #1e293b !important;
        box-shadow: 0 4px 15px rgba(0, 255, 255, 0.15) !important;
    }
    
    /* SOL MENÜ DÜZENİ (Alt Alta Duvar Gibi) */
    [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] {
        flex-direction: column !important;
        gap: 12px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0,255,255,0.15) 0%, rgba(0,255,255,0.02) 100%) !important;
        border-color: #00ffff !important;
        border-left: 5px solid #00ffff !important; 
    }
    [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] > label:has(input:checked) p {
        color: #00ffff !important;
        font-weight: bold !important;
    }

    /* ANA EKRAN DÜZENİ (AL/SAT Butonları Yan Yana Eşit) */
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] {
        flex-direction: row !important;
        gap: 15px !important;
    }
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label {
        flex: 1 1 0px !important; /* Yan yana durduklarında eşit alan paylaşımı sağlar */
    }
    
    /* AL Butonu Yeşile Dönsün */
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(1):has(input:checked) {
        background: linear-gradient(90deg, rgba(0,255,0,0.15) 0%, rgba(0,255,0,0.02) 100%) !important;
        border-color: #00ff00 !important;
        border-left: 5px solid #00ff00 !important; 
    }
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(1):has(input:checked) p {
        color: #00ff00 !important;
        font-weight: bold !important;
    }
    /* SAT Butonu Kırmızıya Dönsün */
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(2):has(input:checked) {
        background: linear-gradient(90deg, rgba(255,68,68,0.15) 0%, rgba(255,68,68,0.02) 100%) !important;
        border-color: #ff4444 !important;
        border-left: 5px solid #ff4444 !important; 
    }
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(2):has(input:checked) p {
        color: #ff4444 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

DB_DOSYASI = "kullanicilar_db.json"

@st.cache_data(ttl=300)
def guncel_kur_getir():
    try:
        return float(yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1])
    except:
        return 34.50

def sifre_sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def db_yukle():
    if os.path.exists(DB_DOSYASI):
        with open(DB_DOSYASI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            if "_GLOBAL_" not in veri:
                veri["_GLOBAL_"] = {"toplam_komisyon": 0.0}
            if "_OTURUMLAR_" not in veri:
                veri["_OTURUMLAR_"] = {}
            for k, v in veri.items():
                if k not in ["_GLOBAL_", "_OTURUMLAR_"] and "cuzdan" in v:
                    if "bekleyen_emirler" not in v["cuzdan"]:
                        v["cuzdan"]["bekleyen_emirler"] = []
            return veri
    return {"_GLOBAL_": {"toplam_komisyon": 0.0}, "_OTURUMLAR_": {}}

def db_kaydet(db):
    with open(DB_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

if 'aktif_kullanici' not in st.session_state:
    st.session_state.aktif_kullanici = None

db = db_yukle()

# --- 10 DAKİKALIK OTURUM SÜRESİ KONTROLÜ ---
su_an = time.time()
silinecek_oturumlar = [t for t, v in db.get("_OTURUMLAR_", {}).items() if su_an > v["bitis"]]
for t in silinecek_oturumlar:
    del db["_OTURUMLAR_"][t]
if silinecek_oturumlar:
    db_kaydet(db)

mevcut_token = st.query_params.get("oturum")

if mevcut_token:
    if mevcut_token in db.get("_OTURUMLAR_", {}):
        st.session_state.aktif_kullanici = db["_OTURUMLAR_"][mevcut_token]["kullanici"]
        db["_OTURUMLAR_"][mevcut_token]["bitis"] = su_an + 600
        db_kaydet(db)
    else:
        st.warning("⏱️ Hareketsizlik sebebiyle oturum süreniz (10 dk) doldu. Lütfen tekrar giriş yapın.")
        st.query_params.clear()
        st.session_state.aktif_kullanici = None

if st.session_state.aktif_kullanici is None:
    st.title("📊 Portföy Analiz ve Yönetimi")
    st.markdown("Sanal 1.000.000 TL bakiye ile kendi fonunuzu yönetmek ve yapay zeka analizlerine ulaşmak için giriş yapın.")
    tab_giris, tab_kayit = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab_giris:
        with st.form("giris_formu"):
            st.info("💡 Lütfen kayıt olurken belirlediğiniz gizli 'Kullanıcı Adınızı' giriniz (Takma Adınızı değil).")
            g_kullanici = st.text_input("Kullanıcı Adı (Gizli ID)")
            g_sifre = st.text_input("Şifre", type="password")
            giris_buton = st.form_submit_button("Giriş Yap", use_container_width=True)
            
        if giris_buton:
            sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_"]
            if g_kullanici in db and g_kullanici not in sistem_idleri and db[g_kullanici]["sifre"] == sifre_sifrele(g_sifre):
                yeni_token = str(uuid.uuid4())
                db["_OTURUMLAR_"][yeni_token] = {"kullanici": g_kullanici, "bitis": su_an + 600}
                db_kaydet(db)
                st.query_params["oturum"] = yeni_token
                st.session_state.aktif_kullanici = g_kullanici
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
                
    with tab_kayit:
        with st.form("kayit_formu"):
            k_kullanici = st.text_input("Sisteme Giriş İçin Kullanıcı Adı (Kimse Görmeyecek)")
            k_nickname = st.text_input("Liderlik Tablosu İçin Takma Ad (Nickname - Herkes Görecek)")
            k_sifre = st.text_input("Yeni Şifre", type="password")
            kayit_buton = st.form_submit_button("Hesap Oluştur", use_container_width=True)
            
        if kayit_buton:
            sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_"]
            mevcut_nicknameler = [v.get("nickname", "").lower() for k, v in db.items() if k not in sistem_idleri]
            
            if k_kullanici in db or k_kullanici in sistem_idleri:
                st.error("❌ Bu Gizli Kullanıcı Adı zaten alınmış!")
            elif k_nickname.lower() in mevcut_nicknameler:
                st.error("❌ Bu Takma Ad (Nickname) başka bir yatırımcı tarafından kullanılıyor!")
            elif k_kullanici.lower() == k_nickname.lower():
                st.error("🛡️ Güvenlik İhlali: Kullanıcı adı ile Takma Ad aynı olamaz. Lütfen farklı bir takma ad belirleyin.")
            elif len(k_kullanici) < 3 or len(k_sifre) < 4 or len(k_nickname) < 3:
                st.warning("Kullanıcı adı/Takma ad en az 3, şifre en az 4 karakter olmalıdır.")
            else:
                db[k_kullanici] = {
                    "sifre": sifre_sifrele(k_sifre), 
                    "nickname": k_nickname, 
                    "son_isim_degistirme": 0,
                    "cuzdan": {"nakit": 1000000.0, "varliklar": {}, "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)", "NVIDIA", "Apple"], "bekleyen_emirler": []}
                }
                db_kaydet(db)
                st.success("✅ Hesabınız oluşturuldu! Şimdi 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")
    st.stop()

aktif_kullanici = st.session_state.aktif_kullanici
cuzdan = db[aktif_kullanici]["cuzdan"]
aktif_nickname = db[aktif_kullanici].get("nickname", aktif_kullanici)

def aktif_cuzdan_kaydet():
    db[aktif_kullanici]["cuzdan"] = cuzdan
    db_kaydet(db)

st.title("📊 Portföy Analiz ve Yönetimi")
st.caption(f"👤 Fon Yöneticisi: **{aktif_nickname.upper()}** | 💵 Güncel Kur (USD/TRY): **{guncel_kur_getir():.2f} ₺**")

bist_30 = {"Akbank": "AKBNK.IS", "Alarko": "ALARK.IS", "Aselsan": "ASELS.IS", "Astor": "ASTOR.IS", "BİM": "BIMAS.IS", "Borusan": "BRSAN.IS", "Coca-Cola İçecek": "CCOLA.IS", "Emlak Konut": "EKGYO.IS", "Enka": "ENKAI.IS", "Ereğli": "EREGL.IS", "Ford Otosan": "FROTO.IS", "Garanti": "GARAN.IS", "Gübre Fab": "GUBRF.IS", "Hektaş": "HEKTS.IS", "İş Bankası": "ISCTR.IS", "Koç Hol": "KCHOL.IS", "Kontrolmatik": "KONTR.IS", "Koza Altın": "KOZAL.IS", "Kardemir": "KRDMD.IS", "Odaş": "ODAS.IS", "Petkim": "PETKM.IS", "Pegasus": "PGSUS.IS", "Sabancı Hol": "SAHOL.IS", "Sasa": "SASA.IS", "Şişecam": "SISE.IS", "Turkcell": "TCELL.IS", "THY": "THYAO.IS", "Tofaş": "TOASO.IS", "Tüpraş": "TUPRS.IS", "Yapı Kredi": "YKBNK.IS"}
bist_100 = {**bist_30, **{"Alfa Solar": "ALFAS.IS", "Arçelik": "ARCLK.IS", "Brisa": "BRISA.IS", "Çimsa": "CIMSA.IS", "CW Enerji": "CWENE.IS", "Doğuş Oto": "DOAS.IS", "Doğan Hol": "DOHOL.IS", "Eczacıbaşı": "ECILC.IS", "Ege Endüstri": "EGEEN.IS", "Enerjisa": "ENJSA.IS", "Europower": "EUPWR.IS", "Girişim Elk": "GESAN.IS", "Halkbank": "HALKB.IS", "İskenderun D.": "ISDMR.IS", "İş GYO": "ISGYO.IS", "İş Yatırım": "ISMEN.IS", "Konya Çimento": "KONYA.IS", "Kordsa": "KORDS.IS", "Koza Anadolu": "KOZAA.IS", "Mavi": "MAVI.IS", "Migros": "MGROS.IS", "Mia Teknoloji": "MIATK.IS", "Otokar": "OTKAR.IS", "Oyak Çimento": "OYAKC.IS", "Qua Granite": "QUAGR.IS", "Şekerbank": "SKBNK.IS", "Smart Güneş": "SMRTG.IS", "Şok Market": "SOKM.IS", "TAV": "TAVHL.IS", "Tekfen": "TKFEN.IS", "TSKB": "TSKB.IS", "Türk Telekom": "TTKOM.IS", "Türk Traktör": "TTRAK.IS", "Tukaş": "TUKAS.IS", "Ülker": "ULKER.IS", "Vakıfbank": "VAKBN.IS", "Vestel Beyaz": "VESBE.IS", "Vestel": "VESTL.IS", "Yeo Teknoloji": "YEOTK.IS", "Zorlu Enerji": "ZOREN.IS"}}
bist_genis = {**bist_100, **{"Agrotech": "AGROT.IS", "Akfen Yenilenebilir": "AKFYE.IS", "Anadolu Efes": "AEFES.IS", "Anadolu Sigorta": "ANSGR.IS", "Aygaz": "AYGAZ.IS", "Bera Holding": "BERA.IS", "Bien Seramik": "BIENY.IS", "Biotrend": "BIOEN.IS", "Borusan Yatırım": "BRYAT.IS", "Bülbüloğlu Vinç": "BVSAN.IS", "Can Termik": "CANTE.IS", "Çan2 Termik": "CANTE.IS", "CVK Maden": "CVKMD.IS", "Eksun Gıda": "EKSUN.IS", "Esenboğa Elektrik": "ESEN.IS", "Forte Bilgi": "FORTE.IS", "Galata Wind": "GWIND.IS", "GSD Holding": "GSDHO.IS", "Hat-San Gemi": "HATSN.IS", "İmaş Makina": "IMASM.IS", "İnfo Yatırım": "INFO.IS", "İzdemir Enerji": "IZENR.IS", "Kaleseramik": "KLSER.IS", "Kayseri Şeker": "KAYSE.IS", "Kocaer Çelik": "KCAER.IS", "Kuştur Kuşadası": "KSTUR.IS", "Margün Enerji": "MAGEN.IS", "Mercan Kimya": "MERCN.IS", "Naten": "NATEN.IS", "Oyak Yatırım": "OYYAT.IS", "Özsu Balık": "OZSUB.IS", "Penta": "PENTA.IS", "Reeder Teknoloji": "REEDR.IS", "Rubenis Tekstil": "RUBNS.IS", "SDT Uzay": "SDTTR.IS", "Tarkim": "TARKM.IS", "Tatlıpınar Enerji": "TATEN.IS", "Tezol": "TEZOL.IS", "VBT Yazılım": "VBTYZ.IS", "Ziraat GYO": "ZRGYO.IS", "Tab Gıda": "TABGD.IS", "Ebebek": "EBEBK.IS", "Fuzul GYO": "FZLGY.IS", "Aydem": "AYDEM.IS", "Söke Değirmencilik": "SOKE.IS", "Enerya": "ENSRV.IS", "Koton": "KOTON.IS", "Lilak Kağıt": "LILAK.IS", "Rönesans GYO": "RGYAS.IS", "Hareket Proje": "HRKET.IS", "Koç Metalurji": "KOCMT.IS"}}
abd_hisseleri = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Tesla": "TSLA", "Amazon": "AMZN", "Alphabet (Google)": "GOOGL", "Meta (Facebook)": "META", "AMD": "AMD", "Netflix": "NFLX", "Intel": "INTC", "Coca-Cola (ABD)": "KO", "PepsiCo": "PEP", "McDonald's": "MCD", "Boeing": "BA", "Ford Motor (ABD)": "F", "General Motors": "GM", "Uber": "UBER", "Airbnb": "ABNB", "Disney": "DIS", "Pfizer": "PFE", "Johnson & Johnson": "JNJ", "Visa": "V", "Mastercard": "MA", "JPMorgan Chase": "JPM", "Bank of America": "BAC", "Goldman Sachs": "GS", "Walmart": "WMT", "Nike": "NKE", "Starbucks": "SBUX", "Alibaba": "BABA"}
kripto = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Binance Coin": "BNB-USD", "Ripple (XRP)": "XRP-USD", "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Dogecoin": "DOGE-USD", "Chainlink": "LINK-USD", "Polkadot": "DOT-USD", "Polygon (MATIC)": "MATIC-USD", "Shiba Inu": "SHIB-USD", "Litecoin": "LTC-USD", "TRON": "TRX-USD", "Bitcoin Cash": "BCH-USD", "Uniswap": "UNI-USD", "Cosmos": "ATOM-USD", "Monero": "XMR-USD", "Stellar": "XLM-USD", "Ethereum Classic": "ETC-USD", "VeChain": "VET-USD", "Filecoin": "FIL-USD", "Aave": "AAVE-USD", "Algorand": "ALGO-USD", "EOS": "EOS-USD", "The Sandbox": "SAND-USD", "Decentraland": "MANA-USD", "ApeCoin": "APE-USD", "Fantom": "FTM-USD"}
madenler_emtia = {"Altın (Ons)": "GC=F", "Gümüş (Ons)": "SI=F", "Bakır": "HG=F", "Platin": "PL=F", "Paladyum": "PA=F", "Alüminyum": "ALI=F", "Ham Petrol (WTI)": "CL=F", "Brent Petrol": "BZ=F", "Doğal Gaz": "NG=F", "Isıtma Yakıtı": "HO=F", "Buğday": "ZW=F", "Mısır": "ZC=F", "Soya Fasulyesi": "ZS=F", "Kahve": "KC=F", "Şeker": "SB=F", "Pamuk": "CT=F", "Kakao": "CC=F", "Yulaf": "ZO=F", "Pirinç (Kaba)": "ZR=F", "Canlı Sığır": "LE=F", "Yağsız Domuz": "HE=F", "Kereste": "LBS=F"}

tum_varliklar_mega = {**bist_genis, **abd_hisseleri, **kripto, **madenler_emtia}

st.sidebar.header("🕹️ Uygulama Modu")
uygulama_modu = st.sidebar.radio("Mod Seçiniz:", ["🔍 Algoritmik Piyasa Tarama", "💼 Sanal Portföy (Oyun)"], label_visibility="collapsed")
st.sidebar.markdown("---")

if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    mevcut_token = st.query_params.get("oturum")
    if mevcut_token and mevcut_token in db.get("_OTURUMLAR_", {}):
        del db["_OTURUMLAR_"][mevcut_token]
        db_kaydet(db)
    st.query_params.clear()
    st.session_state.aktif_kullanici = None
    st.rerun()

with st.sidebar.expander("⚙️ Hesap Ayarları", expanded=False):
    tab_sifre, tab_isim, tab_sil = st.tabs(["🔑 Şifre", "🏷️ İsim", "❌ Sil"])
    
    with tab_sifre:
        with st.form("sifre_degistir_form"):
            eski_sifre = st.text_input("Mevcut Şifre", type="password")
            yeni_sifre = st.text_input("Yeni Şifre", type="password")
            yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar)", type="password")
            btn_sifre = st.form_submit_button("Güncelle", use_container_width=True)
            
            if btn_sifre:
                if db[aktif_kullanici]["sifre"] != sifre_sifrele(eski_sifre):
                    st.error("❌ Mevcut şifreniz yanlış!")
                elif yeni_sifre != yeni_sifre_tekrar:
                    st.error("❌ Yeni şifreler eşleşmiyor!")
                elif len(yeni_sifre) < 4:
                    st.warning("⚠️ Şifre en az 4 karakter olmalı.")
                else:
                    db[aktif_kullanici]["sifre"] = sifre_sifrele(yeni_sifre)
                    db_kaydet(db)
                    st.success("✅ Şifre güncellendi!")
                    
    with tab_isim:
        son_degisim = db[aktif_kullanici].get("son_isim_degistirme", 0)
        kalan_saniye = (7 * 24 * 60 * 60) - (su_an - son_degisim)
        
        if kalan_saniye > 0:
            kalan_gun = int(kalan_saniye // (24 * 3600))
            kalan_saat = int((kalan_saniye % (24 * 3600)) // 3600)
            st.info(f"⏳ Takma adınızı değiştirmek için **{kalan_gun} gün {kalan_saat} saat** beklemelisiniz.")
        else:
            with st.form("isim_degistir_form"):
                st.caption("Sadece Liderlik Tablosunda görünür.")
                yeni_isim = st.text_input("Yeni Takma Ad (Nickname)")
                btn_isim = st.form_submit_button("İsmi Güncelle", use_container_width=True)
                
                if btn_isim:
                    sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_"]
                    mevcut_nicknameler = [v.get("nickname", "").lower() for k, v in db.items() if k not in sistem_idleri]
                    if yeni_isim.lower() in mevcut_nicknameler:
                        st.error("❌ Bu isim kullanılıyor!")
                    elif yeni_isim.lower() == aktif_kullanici.lower():
                        st.error("❌ Güvenlik: Giriş ID'niz ile aynı olamaz!")
                    elif len(yeni_isim) < 3:
                        st.warning("⚠️ En az 3 karakter olmalı.")
                    else:
                        db[aktif_kullanici]["nickname"] = yeni_isim
                        db[aktif_kullanici]["son_isim_degistirme"] = su_an
                        db_kaydet(db)
                        st.success("✅ İsim güncellendi!")
                        time.sleep(1)
                        st.rerun()

    with tab_sil:
        st.markdown("<span style='font-size: 13px; color: #ff4444;'>Dikkat: Bu işlem kalıcıdır ve tüm portföy/geçmiş verileriniz silinir.</span>", unsafe_allow_html=True)
        sil_onay = st.checkbox("Silme işlemini onaylıyorum")
        if st.button("❌ Hesabımı Sil", use_container_width=True, disabled=not sil_onay):
            if aktif_kullanici in db:
                del db[aktif_kullanici]
                db_kaydet(db)
            st.query_params.clear()
            st.session_state.aktif_kullanici = None
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.warning("**⚠️ YASAL UYARI (YTD)**\nBurada yer alan yatırım bilgi, yorum ve yapay zeka tahminleri yatırım danışmanlığı kapsamında değildir. Sistem tarafından üretilen sinyaller kesin getiri vaat etmez.")

usd_kuru = guncel_kur_getir()

if uygulama_modu == "🔍 Algoritmik Piyasa Tarama":
    st.sidebar.header("⚙️ Tarama Ayarları")
    st.sidebar.markdown("<b>1. Yatırım Vadesi</b>", unsafe_allow_html=True)
    vade_secimi = st.sidebar.radio("Vade:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"], label_visibility="collapsed")
    st.sidebar.markdown("<b>2. İncelenecek Piyasa</b>", unsafe_allow_html=True)
    piyasa_secimi = st.sidebar.radio("Piyasa:", ["🇹🇷 BIST 30 (En Büyükler)", "🇹🇷 BIST 100", "🇹🇷 BIST Tüm (Genişletilmiş)", "🇺🇸 ABD Teknoloji ve Global", "🪙 Kripto Paralar", "⛏️ Tüm Emtia ve Madenler", "👤 Kendi İzleme Listem"], label_visibility="collapsed")

    aktif_varliklar = {}
    if piyasa_secimi == "👤 Kendi İzleme Listem":
        if "ilk_liste" not in st.session_state:
            st.session_state.ilk_liste = [v for v in cuzdan.get("izleme_listesi", []) if v in tum_varliklar_mega]
        secilen_isimler = st.sidebar.multiselect("Varlıkları Seçin:", options=list(tum_varliklar_mega.keys()), default=st.session_state.ilk_liste)
        
        if set(secilen_isimler) != set(st.session_state.ilk_liste):
            st.session_state.ilk_liste = secilen_isimler
            cuzdan["izleme_listesi"] = secilen_isimler
            aktif_cuzdan_kaydet()
        aktif_varliklar = {isim: tum_varliklar_mega[isim] for isim in secilen_isimler}
    elif piyasa_secimi == "🇹🇷 BIST 30 (En Büyükler)": aktif_varliklar = bist_30
    elif piyasa_secimi == "🇹🇷 BIST 100": aktif_varliklar = bist_100
    elif piyasa_secimi == "🇹🇷 BIST Tüm (Genişletilmiş)": aktif_varliklar = bist_genis
    elif piyasa_secimi == "🇺🇸 ABD Teknoloji ve Global": aktif_varliklar = abd_hisseleri
    elif piyasa_secimi == "🪙 Kripto Paralar": aktif_varliklar = kripto
    else: aktif_varliklar = madenler_emtia

    if 'df_sonuc' not in st.session_state: st.session_state.df_sonuc = pd.DataFrame()
    if 'ozel_portfoy_verisi' not in st.session_state: st.session_state.ozel_portfoy_verisi = pd.DataFrame()

    if st.button("🚀 Algoritmayı Çalıştır", use_container_width=True):
        sonuclar = []
        ilerleme_cubugu = st.progress(0.0)
        durum_metni = st.empty()
        toplam_varlik = len(aktif_varliklar)
        islenen = 0
        portfoy_fiyat_gecmisi = {} 

        if toplam_varlik > 0:
            for isim, sembol in aktif_varliklar.items():
                try:
                    durum_metni.text(f"Taranıyor: {isim} ({islenen}/{toplam_varlik})")
                    ticker = yf.Ticker(sembol)
                    veri = ticker.history(period="2y" if vade_secimi == "📅 Uzun Vadeli (1+ Yıl / Yatırım)" else "6mo")
                    if veri is None or veri.empty or len(veri) < 20: continue
                    
                    if 'Volume' not in veri.columns or veri['Volume'].sum() == 0:
                        veri['Volume'] = 1000000.0
                    
                    if piyasa_secimi == "👤 Kendi İzleme Listem":
                        temiz_veri = veri['Close'].copy()
                        temiz_veri.index = pd.to_datetime(temiz_veri.index).tz_localize(None).normalize()
                        portfoy_fiyat_gecmisi[isim] = temiz_veri
                        
                    son_fiyat = float(veri['Close'].iloc[-1])
                    if not sembol.endswith(".IS"):
                        son_fiyat *= usd_kuru
                        
                    puan = 0
                    durum_notu = []

                    if vade_secimi == "⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)":
                        tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3
                        para_akisi = tipik_fiyat * veri['Volume']
                        pozitif_akis = np.where(tipik_fiyat > tipik_fiyat.shift(1), para_akisi, 0)
                        negatif_akis = np.where(tipik_fiyat < tipik_fiyat.shift(1), para_akisi, 0)
                        pozitif_mf = pd.Series(pozitif_akis).rolling(window=14).sum()
                        negatif_mf = pd.Series(negatif_akis).rolling(window=14).sum()
                        
                        mfi_ratio = pozitif_mf / negatif_mf.replace(0, np.nan)
                        mfi = 100 - (100 / (1 + mfi_ratio))
                        son_mfi = float(mfi.ffill().fillna(50.0).iloc[-1])
                        
                        delta = veri['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        
                        rs = gain / loss.replace(0, np.nan)
                        rsi = 100 - (100 / (1 + rs))
                        son_rsi = float(rsi.ffill().fillna(50.0).iloc[-1])
                        
                        ema_12 = veri['Close'].ewm(span=12, adjust=False).mean()
                        ema_26 = veri['Close'].ewm(span=26, adjust=False).mean()
                        macd = ema_12 - ema_26
                        macd_sinyal = macd.ewm(span=9, adjust=False).mean()
                        
                        sma_20 = veri['Close'].rolling(window=20).mean()
                        std_20 = veri['Close'].rolling(window=20).std()
                        son_alt_bant = float(sma_20.iloc[-1] - (std_20.iloc[-1] * 2))
                        
                        if not sembol.endswith(".IS"):
                            son_alt_bant *= usd_kuru

                        if son_mfi < 20: puan += 3; durum_notu.append("Hacim: Para Girişi")
                        elif son_mfi > 80: puan -= 2; durum_notu.append("Hacim: Para Çıkışı")
                        if son_rsi < 30: puan += 2; durum_notu.append("RSI: Dipte")
                        if float(macd.iloc[-1]) > float(macd_sinyal.iloc[-1]): puan += 1; durum_notu.append("MACD: Pozitif")
                        if son_fiyat < son_alt_bant: puan += 2; durum_notu.append("BB: Aşırı Düştü")
                            
                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": round(son_fiyat, 2), "RSI": round(son_rsi, 1), "MFI (Hacim)": round(son_mfi, 1), "Puan": puan, "Durum": " | ".join(durum_notu)})

                    else:
                        sma_50 = veri['Close'].rolling(window=50).mean()
                        sma_200 = veri['Close'].rolling(window=200).mean()
                        if len(veri) < 200 or pd.isna(sma_200.iloc[-1]): continue
                        
                        sma_200_deger = float(sma_200.iloc[-1])
                        if not sembol.endswith(".IS"): 
                            sma_200_deger *= usd_kuru
                            
                        fk_orani = None
                        if sembol.endswith(".IS") or sembol in abd_hisseleri.values():
                            try:
                                fk_orani = ticker.info.get('trailingPE', None)
                            except:
                                pass

                        if son_fiyat > sma_200_deger: puan += 3; durum_notu.append("Boğa Piyasası")
                        else: puan -= 2; durum_notu.append("Ayı Piyasası")
                        if float(sma_50.iloc[-1]) > float(sma_200.iloc[-1]): puan += 2; durum_notu.append("Altın Kesişim")
                        else: puan -= 1; durum_notu.append("Ölüm Kesişimi")
                        
                        fk_metni = "N/A"
                        if fk_orani and isinstance(fk_orani, (int, float)):
                            fk_metni = str(round(fk_orani, 2)); puan += 2 if fk_orani < 15 else -2 if fk_orani > 30 else 0
                            if fk_orani < 15: durum_notu.append("F/K Ucuz")

                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": round(son_fiyat, 2), "200G Ort (₺)": round(sma_200_deger, 2), "F/K": fk_metni, "Puan": puan, "Durum": " | ".join(durum_notu)})
                except Exception as e: 
                    pass 
                finally:
                    islenen += 1
                    ilerleme_cubugu.progress(min(islenen / toplam_varlik, 1.0))
            
            durum_metni.empty() 
            ilerleme_cubugu.empty() 
            
            if sonuclar:
                st.session_state.df_sonuc = pd.DataFrame(sonuclar).sort_values(by="Puan", ascending=False).reset_index(drop=True)
                st.session_state.ozel_portfoy_verisi = pd.DataFrame(portfoy_fiyat_gecmisi) if piyasa_secimi == "👤 Kendi İzleme Listem" and len(portfoy_fiyat_gecmisi) > 1 else pd.DataFrame()
            else: 
                st.error("📉 Seçilen piyasada kriterlere uygun yeterli geçmiş veri bulunamadı.")
        else: st.warning("Lütfen sol menüden en az bir varlık seçin.")

    if not st.session_state.df_sonuc.empty:
        try:
            if "Kısa" in vade_secimi:
                def style_rsi(val):
                    try:
                        v = float(val)
                        if v < 35: return 'background-color: rgba(0, 255, 0, 0.2); font-weight: bold; color: #00ff00;'
                        elif v > 65: return 'background-color: rgba(255, 0, 0, 0.2); font-weight: bold; color: #ff4444;'
                    except: pass
                    return ''
                if hasattr(st.session_state.df_sonuc.style, "map"): styled_df = st.session_state.df_sonuc.style.map(style_rsi, subset=['RSI'])
                else: styled_df = st.session_state.df_sonuc.style.applymap(style_rsi, subset=['RSI'])
                st.dataframe(styled_df.format({"Fiyat (₺)": "{:,.2f}"}), use_container_width=True)
            else: st.dataframe(st.session_state.df_sonuc.style.format({"Fiyat (₺)": "{:,.2f}", "200G Ort (₺)": "{:,.2f}"}), use_container_width=True)
        except: st.dataframe(st.session_state.df_sonuc, use_container_width=True)
            
        if piyasa_secimi == "👤 Kendi İzleme Listem" and not st.session_state.ozel_portfoy_verisi.empty:
            with st.expander("⚖️ Markowitz Optimum Portföy Dağılımını Göster", expanded=False):
                df_port = st.session_state.ozel_portfoy_verisi.ffill().dropna()
                returns = df_port.pct_change().dropna()
                if len(returns) > 10: 
                    mean_returns, cov_matrix, num_portfolios = returns.mean(), returns.cov(), 5000 
                    results, weights_record = np.zeros((3, num_portfolios)), []
                    for i in range(num_portfolios):
                        weights = np.random.random(len(df_port.columns))
                        weights /= np.sum(weights)
                        weights_record.append(weights)
                        p_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
                        p_ret = np.sum(mean_returns * weights) * 252
                        results[0,i], results[1,i], results[2,i] = p_ret, p_std, p_ret / p_std
                    max_sharpe_idx = np.argmax(results[2])
                    opt_weights = weights_record[max_sharpe_idx]
                    col_pie, col_text = st.columns([1, 1])
                    with col_pie:
                        fig_pie = px.pie(pd.DataFrame({'Varlık': df_port.columns, 'Oran': opt_weights * 100}), values='Oran', names='Varlık', title="Optimum Sermaye Dağılımı", hole=0.4, template="plotly_dark")
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col_text:
                        st.write(f"**Beklenen Yıllık Getiri:** %{round(results[0,max_sharpe_idx]*100, 2)}")
                        st.write(f"**Tahmini Yıllık Risk:** %{round(results[1,max_sharpe_idx]*100, 2)}")
                else: st.warning("Yeterli geçmiş veri yok.")
                    
            with st.expander("🗺️ Varlık Korelasyon Matrisi", expanded=False):
                returns_corr = st.session_state.ozel_portfoy_verisi.ffill().dropna().pct_change().dropna()
                if len(returns_corr) > 10 and len(returns_corr.columns) > 1:
                    st.plotly_chart(px.imshow(returns_corr.corr(), text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn", title="Korelasyon", template="plotly_dark"), use_container_width=True)

        col_analiz_baslik, col_analiz_yenile = st.columns([3, 1])
        with col_analiz_baslik: st.write("### 🤖 Gelişmiş Analiz Paneli")
        with col_analiz_yenile:
            if st.button("🔄 Grafiği Tazele", use_container_width=True): st.rerun()
                
        secilen_isim = st.selectbox("Grafik için varlık seçin:", st.session_state.df_sonuc['Varlık'].tolist())
        secilen_sembol = tum_varliklar_mega.get(secilen_isim)
        
        if secilen_sembol:
            col1, col2 = st.columns([2, 1])
            with col1:
                grafik_veri = yf.Ticker(secilen_sembol).history(period="6mo")
                if not grafik_veri.empty:
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🤖 AI Trend", "📊 Hacim Profili", "🎲 Monte Carlo", "⏪ Backtest", "🗓️ Mevsimsellik", "⚖️ İst. Arbitraj"])
                    
                    with tab1:
                        df_ml = grafik_veri[['Close']].dropna().copy()
                        df_ml['Gunler'] = np.arange(len(df_ml))
                        model = LinearRegression().fit(df_ml[['Gunler']], df_ml['Close'])
                        y_tahmin = model.predict(np.array([[len(df_ml) + i] for i in range(1, 16)]))
                        gelecek_tarihler = [df_ml.index[-1] + pd.Timedelta(days=i) for i in range(1, 16)]
                        fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
                        fig1.add_trace(go.Candlestick(x=grafik_veri.index, open=grafik_veri['Open'], high=grafik_veri['High'], low=grafik_veri['Low'], close=grafik_veri['Close'], name='Fiyat'), row=1, col=1)
                        fig1.add_trace(go.Scatter(x=gelecek_tarihler, y=y_tahmin, mode='lines', name='AI Rotası', line=dict(color='cyan', width=4, dash='dot')), row=1, col=1)
                        if 'Volume' in grafik_veri.columns:
                            fig1.add_trace(go.Bar(x=grafik_veri.index, y=grafik_veri['Volume'], marker_color=['green' if c >= o else 'red' for o, c in zip(grafik_veri['Open'], grafik_veri['Close'])]), row=2, col=1)
                        fig1.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(t=10, b=10))
                        st.plotly_chart(fig1, use_container_width=True)
                        
                    with tab2:
                        if 'Volume' not in grafik_veri.columns:
                            grafik_veri['Volume'] = 1.0
                        df_vp = grafik_veri[['Close', 'Volume', 'Open', 'High', 'Low']].copy()
                        min_price = df_vp['Low'].min()
                        max_price = df_vp['High'].max()
                        if min_price != max_price:
                            bins = np.linspace(min_price, max_price, 50)
                            df_vp['Price_Bin'] = pd.cut(df_vp['Close'], bins=bins)
                            vp_grouped = df_vp.dropna().groupby('Price_Bin')['Volume'].sum().reset_index()
                            vp_grouped['Bin_Mid'] = vp_grouped['Price_Bin'].apply(lambda x: x.mid if pd.notnull(x) else 0)
                            fig_vp = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.75, 0.25], horizontal_spacing=0.02)
                            fig_vp.add_trace(go.Candlestick(x=df_vp.index, open=df_vp['Open'], high=df_vp['High'], low=df_vp['Low'], close=df_vp['Close'], name='Fiyat'), row=1, col=1)
                            fig_vp.add_trace(go.Bar(x=vp_grouped['Volume'], y=vp_grouped['Bin_Mid'], orientation='h', name='Fiyat Hacmi', marker=dict(color='rgba(0, 255, 255, 0.6)')), row=1, col=2)
                            fig_vp.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(t=10, b=10), showlegend=False)
                            st.plotly_chart(fig_vp, use_container_width=True)
                        else:
                            st.info("Hacim profili çıkarılamadı.")

                    with tab3:
                        log_returns = np.log(1 + grafik_veri['Close'].pct_change()).dropna()
                        u, var, stdev = log_returns.mean(), log_returns.var(), log_returns.std()
                        drift = u - (0.5 * var)
                        t_intervals, iterations = 30, 100 
                        daily_returns = np.exp(drift + stdev * np.random.randn(t_intervals, iterations))
                        price_paths = np.zeros_like(daily_returns)
                        price_paths[0] = grafik_veri['Close'].iloc[-1]
                        for t in range(1, t_intervals): price_paths[t] = price_paths[t - 1] * daily_returns[t]
                        mc_tarihler = [grafik_veri.index[-1] + pd.Timedelta(days=i) for i in range(t_intervals)]
                        fig2 = go.Figure()
                        gecmis_30 = grafik_veri['Close'].iloc[-30:]
                        fig2.add_trace(go.Scatter(x=gecmis_30.index, y=gecmis_30.values, mode='lines', name='Geçmiş Fiyat', line=dict(color='white', width=3)))
                        for i in range(iterations): fig2.add_trace(go.Scatter(x=mc_tarihler, y=price_paths[:, i], mode='lines', showlegend=False, line=dict(color='rgba(0, 255, 255, 0.05)')))
                        fig2.add_trace(go.Scatter(x=mc_tarihler, y=price_paths.mean(axis=1), mode='lines', name='Ortalama Beklenti', line=dict(color='red', width=3, dash='dash')))
                        fig2.update_layout(height=500, template="plotly_dark", margin=dict(t=10, b=10))
                        st.plotly_chart(fig2, use_container_width=True)
                        
                    with tab4:
                        df_bt = grafik_veri[['Close']].copy()
                        delta_bt = df_bt['Close'].diff()
                        gain_bt = (delta_bt.where(delta_bt > 0, 0)).rolling(14).mean()
                        loss_bt = (-delta_bt.where(delta_bt < 0, 0)).rolling(14).mean()
                        df_bt['RSI'] = 100 - (100 / (1 + (gain_bt / loss_bt.replace(0, np.nan))))
                        nakit, adet, al_t, al_f, sat_t, sat_f = 10000, 0, [], [], [], []
                        for index, row in df_bt.iterrows():
                            if pd.isna(row['RSI']): continue
                            if row['RSI'] < 30 and adet == 0: adet, nakit = nakit / row['Close'], 0; al_t.append(index); al_f.append(row['Close'])
                            elif row['RSI'] > 70 and adet > 0: nakit, adet = adet * row['Close'], 0; sat_t.append(index); sat_f.append(row['Close'])
                        son_deger = nakit if adet == 0 else adet * df_bt['Close'].iloc[-1]
                        c1, c2 = st.columns(2)
                        c1.metric("Al-Sat Getirisi", f"%{round(((son_deger - 10000) / 10000) * 100, 2)}")
                        c2.metric("Bekleme Getirisi", f"%{round(((df_bt['Close'].iloc[-1] - df_bt['Close'].dropna().iloc[0]) / df_bt['Close'].dropna().iloc[0]) * 100, 2)}")
                        fig3 = go.Figure().add_trace(go.Scatter(x=df_bt.index, y=df_bt['Close'], mode='lines', name='Fiyat', line=dict(color='white')))
                        if al_t: fig3.add_trace(go.Scatter(x=al_t, y=al_f, mode='markers', name='AL', marker=dict(color='green', size=12, symbol='triangle-up')))
                        if sat_t: fig3.add_trace(go.Scatter(x=sat_t, y=sat_f, mode='markers', name='SAT', marker=dict(color='red', size=12, symbol='triangle-down')))
                        fig3.update_layout(height=400, template="plotly_dark", margin=dict(t=10, b=10))
                        st.plotly_chart(fig3, use_container_width=True)

                    with tab5:
                        with st.spinner("Mevsimsellik verisi hesaplanıyor (Son 5 Yıl)..."):
                            try:
                                seas_data = yf.Ticker(secilen_sembol).history(period="5y")
                                if len(seas_data) > 100:
                                    seas_data.index = pd.to_datetime(seas_data.index).tz_localize(None)
                                    monthly_closes = seas_data['Close'].resample('ME').last()
                                    monthly_returns = monthly_closes.pct_change() * 100
                                    df_seas = pd.DataFrame({'Getiri': monthly_returns})
                                    df_seas['Yıl'] = df_seas.index.year
                                    df_seas['Ay'] = df_seas.index.month
                                    ay_isimleri = {1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz', 7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'}
                                    heatmap_df = df_seas.pivot(index='Yıl', columns='Ay', values='Getiri').reindex(columns=range(1, 13))
                                    heatmap_df.columns = [ay_isimleri.get(c, str(c)) for c in heatmap_df.columns]
                                    heatmap_df = heatmap_df.dropna(how='all')
                                    
                                    fig_heat = px.imshow(heatmap_df, text_auto=".2f", aspect="auto", color_continuous_scale=["#ff4444", "#1a1a1a", "#00ff00"], color_continuous_midpoint=0, labels=dict(x="Aylar", y="Yıllar", color="Getiri (%)"))
                                    fig_heat.update_layout(template="plotly_dark", margin=dict(t=40, b=10))
                                    fig_heat.update_traces(textfont=dict(color="white", weight="bold"))
                                    st.plotly_chart(fig_heat, use_container_width=True)
                                    
                                    avg_ret = heatmap_df.mean()
                                    st.info(f"💡 Tarihsel olarak **en çok kazandıran ay: {avg_ret.idxmax()}** (Ort. %{avg_ret.max():.2f}) | **En riskli ay: {avg_ret.idxmin()}** (Ort. %{avg_ret.min():.2f})")
                                else:
                                    st.warning("Yeterli tarihsel veri yok.")
                            except:
                                st.error("Mevsimsellik hesaplanamadı.")

                    with tab6:
                        st.markdown("<p style='font-size:14px; color:#aaa;'>İki varlık arasındaki fiyat makasının (spread) tarihsel ortalamasından ne kadar saptığını Z-Skoru ile ölçer.</p>", unsafe_allow_html=True)
                        ikinci_varlik_isim = st.selectbox("Karşılaştırılacak 2. Varlığı Seçin:", list(tum_varliklar_mega.keys()), index=1 if secilen_isim != list(tum_varliklar_mega.keys())[1] else 0)
                        ikinci_sembol = tum_varliklar_mega.get(ikinci_varlik_isim)
                        if ikinci_sembol and ikinci_sembol != secilen_sembol:
                            with st.spinner("Arbitraj modeli hesaplanıyor..."):
                                try:
                                    veri1 = yf.Ticker(secilen_sembol).history(period="1y")['Close']
                                    veri2 = yf.Ticker(ikinci_sembol).history(period="1y")['Close']
                                    df_pair = pd.DataFrame({'Varlık_1': veri1, 'Varlık_2': veri2}).dropna()
                                    if len(df_pair) > 50:
                                        df_pair['Ratio'] = df_pair['Varlık_1'] / df_pair['Varlık_2']
                                        df_pair['Mean'] = df_pair['Ratio'].rolling(window=30).mean()
                                        df_pair['Std'] = df_pair['Ratio'].rolling(window=30).std()
                                        df_pair['Z_Score'] = (df_pair['Ratio'] - df_pair['Mean']) / df_pair['Std']
                                        
                                        fig_pair = go.Figure()
                                        fig_pair.add_trace(go.Scatter(x=df_pair.index, y=df_pair['Z_Score'], mode='lines', name='Z-Skoru Makası', line=dict(color='cyan', width=2)))
                                        fig_pair.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Üst Sınır (+2.0)")
                                        fig_pair.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="Alt Sınır (-2.0)")
                                        fig_pair.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.5)")
                                        fig_pair.update_layout(height=400, template="plotly_dark", title=f"Z-Skoru Makası: {secilen_isim} / {ikinci_varlik_isim}", margin=dict(t=40, b=10))
                                        st.plotly_chart(fig_pair, use_container_width=True)
                                        
                                        son_z = float(df_pair['Z_Score'].iloc[-1])
                                        if son_z > 2.0: st.error(f"🚨 **ARBİTRAJ FIRSATI (Aşırı Değerli):** {secilen_isim}, {ikinci_varlik_isim}'e kıyasla ortalamanın çok üzerinde.")
                                        elif son_z < -2.0: st.success(f"🟢 **ARBİTRAJ FIRSATI (Aşırı Ucuz):** {secilen_isim}, {ikinci_varlik_isim}'e kıyasla ortalamanın çok altında.")
                                        else: st.info(f"⚖️ **Denge Durumu:** İki varlık arasındaki oran tarihsel normaller (Z-Skoru: {son_z:.2f}) içinde seyrediyor.")
                                    else:
                                        st.warning("Eşleşen yeterli tarihsel veri bulunamadı.")
                                except Exception as e:
                                    st.warning("Veriler eşleştirilirken bir uyumsuzluk yaşandı.")
                        elif ikinci_sembol == secilen_sembol:
                            st.warning("Lütfen karşılaştırmak için farklı bir varlık seçin.")

            with col2:
                st.write("### 🧠 Piyasa Psikolojisi")
                try:
                    haberler = yf.Ticker(secilen_sembol).news
                    if haberler:
                        toplam_duygu, gecerli_haber = 0, 0
                        for h in haberler[:10]:
                            baslik = h.get('title') or h.get('content', {}).get('title', '')
                            if baslik and baslik != "Başlık Yok": 
                                toplam_duygu += TextBlob(baslik).sentiment.polarity
                                gecerli_haber += 1
                                
                        if gecerli_haber > 0:
                            fig_gauge = go.Figure(go.Indicator(
                                mode="gauge+number", 
                                value=toplam_duygu/gecerli_haber, 
                                domain={'x': [0, 1], 'y': [0, 1]}, 
                                title={'text': "Medya Hissi", 'font': {'color': 'white'}}, 
                                gauge={'axis': {'range': [-1, 1]}, 'bar': {'color': "white"}, 'steps': [{'range': [-1, -0.2], 'color': "rgba(255,68,68,0.6)"}, {'range': [-0.2, 0.2], 'color': "rgba(150,150,150,0.4)"}, {'range': [0.2, 1], 'color': "rgba(0,200,83,0.6)"}]}
                            ))
                            st.plotly_chart(fig_gauge.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), template="plotly_dark"), use_container_width=True)
                        else:
                            st.info("Haber başlıkları analiz edilemedi.")
                    else:
                        st.info("Bu varlığa ait güncel İngilizce haber bulunamadı.")
                        
                    with st.expander("📰 Son Dakika Haberleri", expanded=True):
                        if haberler:
                            for h in haberler[:5]:
                                t = h.get('title') or h.get('content', {}).get('title', '')
                                if t:
                                    l = h.get('link') or h.get('url') or h.get('content', {}).get('clickThroughUrl', {}).get('url', '#')
                                    st.markdown(f"🔗 **[{t}]({l})**")
                                    st.markdown("---")
                        else:
                            st.write("Gösterilecek haber kaynağı yok.")
                except Exception as e: 
                    st.error("Haber servisine ulaşılamıyor.")

elif uygulama_modu == "💼 Sanal Portföy (Oyun)":
    
    # =========================================================================================
    # TEMBEL KONTROL: ZAMAN PARADOKSU ÇÖZÜLMÜŞ LİMİT EMİR MOTORU
    # =========================================================================================
    gerceklesen_mesajlar = []
    if cuzdan.get("bekleyen_emirler"):
        kalan_emirler = []
        for emir in cuzdan["bekleyen_emirler"]:
            sembol = tum_varliklar_mega.get(emir["varlik"])
            if not sembol: 
                kalan_emirler.append(emir)
                continue
            try:
                veri = yf.Ticker(sembol).history(period="5d")
                if veri.empty:
                    kalan_emirler.append(emir)
                    continue
                
                katsayi = usd_kuru if not sembol.endswith(".IS") else 1.0
                anlik_fiyat = float(veri['Close'].iloc[-1]) * katsayi
                emir_tarihi = pd.to_datetime(emir["tarih"], unit='s').tz_localize(None).date()
                
                veri.index = pd.to_datetime(veri.index).tz_localize(None)
                veri_sonrasi = veri[veri.index.date > emir_tarihi]
                
                tetiklendi = False
                
                if emir["tip"] == "AL" and anlik_fiyat <= emir["hedef_fiyat"]:
                    tetiklendi = True
                elif emir["tip"] == "SAT" and anlik_fiyat >= emir["hedef_fiyat"]:
                    tetiklendi = True
                    
                if not tetiklendi and not veri_sonrasi.empty:
                    min_fiyat = float(veri_sonrasi['Low'].min()) * katsayi
                    max_fiyat = float(veri_sonrasi['High'].max()) * katsayi
                    
                    if emir["tip"] == "AL" and min_fiyat <= emir["hedef_fiyat"]:
                        tetiklendi = True
                    elif emir["tip"] == "SAT" and max_fiyat >= emir["hedef_fiyat"]:
                        tetiklendi = True
                    
                if tetiklendi:
                    if emir["tip"] == "AL":
                        mevcut_veri = cuzdan["varliklar"].get(emir["varlik"], {"adet": 0.0, "maliyet": 0.0})
                        yeni_adet = mevcut_veri["adet"] + emir["adet"]
                        yeni_maliyet = ((mevcut_veri["adet"] * mevcut_veri["maliyet"]) + emir["baglanan_tutar"]) / yeni_adet
                        cuzdan["varliklar"][emir["varlik"]] = {"adet": yeni_adet, "maliyet": yeni_maliyet}
                        db["_GLOBAL_"]["toplam_komisyon"] += emir["komisyon"]
                        gerceklesen_mesajlar.append(f"🔔 {emir['varlik']} hedefinize ({emir['hedef_fiyat']} ₺) ulaştı! Otomatik ALIM yapıldı.")
                        
                    elif emir["tip"] == "SAT":
                        cuzdan["nakit"] += emir["beklenen_getiri"]
                        db["_GLOBAL_"]["toplam_komisyon"] += emir["komisyon"]
                        gerceklesen_mesajlar.append(f"🔔 {emir['varlik']} hedefinize ({emir['hedef_fiyat']} ₺) ulaştı! Otomatik SATIŞ yapıldı.")
                else:
                    kalan_emirler.append(emir)
            except:
                kalan_emirler.append(emir)
                
        if len(cuzdan["bekleyen_emirler"]) != len(kalan_emirler):
            cuzdan["bekleyen_emirler"] = kalan_emirler
            aktif_cuzdan_kaydet()
            for m in gerceklesen_mesajlar:
                st.toast(m, icon="✅")
    # =========================================================================================

    toplam_komisyon = db["_GLOBAL_"].get("toplam_komisyon", 0.0)
    st.markdown(f"<div class='bagis-panosu'>🌟 <b>Komisyon Olarak Bağışlanan Toplam Tutar:</b> <br><span class='bagis-sayi'>{toplam_komisyon:,.2f} ₺</span></div>", unsafe_allow_html=True)

    tab_portfoy, tab_liderlik = st.tabs(["💼 Portföyüm", "🏆 Liderlik Tablosu (En İyiler)"])
    
    with tab_portfoy:
        toplam_varlik_degeri = 0
        guncel_fiyatlar = {}
        
        if cuzdan["varliklar"]:
            for varlik_ismi, v_veri in list(cuzdan["varliklar"].items()):
                if isinstance(v_veri, (int, float)): 
                    cuzdan["varliklar"][varlik_ismi] = {"adet": v_veri, "maliyet": 0.0}
                    aktif_cuzdan_kaydet()
                    adet = v_veri
                else: adet = v_veri["adet"]
                    
                sembol = tum_varliklar_mega.get(varlik_ismi)
                if sembol:
                    try:
                        fiyat = float(yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1])
                        if not sembol.endswith(".IS"): fiyat *= usd_kuru
                        guncel_fiyatlar[varlik_ismi] = fiyat
                        toplam_varlik_degeri += (fiyat * adet)
                    except: guncel_fiyatlar[varlik_ismi] = 0.0

        toplam_portfoy = cuzdan["nakit"] + toplam_varlik_degeri
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Portföy", f"{toplam_portfoy:,.2f} ₺", f"% {((toplam_portfoy - 1000000.0) / 1000000.0) * 100:.2f}")
        col2.metric("Boş Nakit", f"{cuzdan['nakit']:,.2f} ₺")
        col3.metric("Yatırımdaki Varlıklar", f"{toplam_varlik_degeri:,.2f} ₺")
        st.markdown("---")

        col_islem, col_durum = st.columns([1, 2])
        
        with col_islem:
            st.markdown("<b>Hızlı İşlem Masası</b>", unsafe_allow_html=True)
            
            c_yon, c_tur = st.columns(2)
            with c_yon: islem_tipi = st.radio("İşlem Yönü:", ["AL", "SAT"], horizontal=True, label_visibility="collapsed")
            with c_tur: emir_turu = st.radio("Emir Türü:", ["⚡ Piyasa", "🕒 Limit"], horizontal=True, label_visibility="collapsed")
            
            secili_varlik = st.selectbox("Varlık Seçin:", list(tum_varliklar_mega.keys()))
            sembol_islem = tum_varliklar_mega[secili_varlik]
            
            if secili_varlik in bist_genis:
                komisyon_orani = 0.0015
                komisyon_metni = "%0.15 (Hisse)"
            elif secili_varlik in abd_hisseleri:
                komisyon_orani = 0.0025
                komisyon_metni = "%0.25 (Yabancı Hisse)"
            elif secili_varlik in kripto:
                komisyon_orani = 0.0020
                komisyon_metni = "%0.20 (Kripto)"
            else:
                komisyon_orani = 0.0010
                komisyon_metni = "%0.10 (Emtia)"

            try:
                veri_hizli = yf.Ticker(sembol_islem).history(period="5d")
                if veri_hizli.empty:
                    raise ValueError("Veri boş")
                    
                anlik_fiyat = float(veri_hizli['Close'].iloc[-1])
                if not sembol_islem.endswith(".IS"): anlik_fiyat *= usd_kuru
                
                if 'Volume' in veri_hizli.columns:
                    son_hacim = float(veri_hizli['Volume'].iloc[-1])
                    if son_hacim <= 0: son_hacim = float(veri_hizli['Volume'].mean())
                else:
                    son_hacim = 0.0
                    
                if pd.isna(son_hacim) or son_hacim <= 0: 
                    son_hacim = 1000000.0 
                
                max_islem_limiti = son_hacim * 0.10 
                
                st.write(f"Anlık Fiyat: **{anlik_fiyat:,.2f} ₺**")
                st.caption(f"📊 Günlük Piyasa Hacmi: **{son_hacim:,.0f} Adet**")
                st.caption(f"⚖️ Max İşlem Limiti (%10): **{max_islem_limiti:,.2f} Adet**")
            except:
                anlik_fiyat = 0
                max_islem_limiti = float('inf')
                st.warning("Fiyat veya hacim çekilemedi.")

            islem_miktari = st.number_input("Adet / Miktar:", min_value=0.01, step=1.0)
            
            limit_asildi = islem_miktari > max_islem_limiti
            if limit_asildi:
                st.error(f"🚨 LİKİDİTE KISITI: Gerçekçi piyasa simülasyonu gereği tahtayı bozmamak adına tek seferde en fazla {max_islem_limiti:,.2f} adet işlem yapabilirsiniz!")
            
            if "Limit" in emir_turu:
                hedef_fiyat = st.number_input("Hedef Fiyat (₺):", min_value=0.01, value=float(anlik_fiyat) if anlik_fiyat>0 else 1.0, step=1.0)
                islem_tutari = islem_miktari * hedef_fiyat
            else:
                hedef_fiyat = anlik_fiyat
                islem_tutari = islem_miktari * anlik_fiyat
            
            komisyon_tutari = islem_tutari * komisyon_orani
            toplam_islem_maliyeti = islem_tutari + komisyon_tutari 
            toplam_islem_getirisi = islem_tutari - komisyon_tutari 

            st.write(f"İşlem Hacmi: **{islem_tutari:,.2f} ₺**")
            st.write(f"Komisyon ({komisyon_metni}): **{komisyon_tutari:,.2f} ₺**")
            
            if islem_tipi == "AL": st.info(f"Kasadan Çıkacak/Bloke: **{toplam_islem_maliyeti:,.2f} ₺**")
            else: st.success(f"Kasaya Girecek: **{toplam_islem_getirisi:,.2f} ₺**")

            buton_metni = "🕒 Bekleyen Emir Gir" if "Limit" in emir_turu else "⚡ Siparişi Anında Onayla"

            if st.button(buton_metni, use_container_width=True) and anlik_fiyat > 0 and not limit_asildi:
                if islem_tipi == "AL":
                    if cuzdan["nakit"] >= toplam_islem_maliyeti:
                        cuzdan["nakit"] -= toplam_islem_maliyeti
                        
                        if "Limit" in emir_turu:
                            cuzdan["bekleyen_emirler"].append({
                                "id": str(uuid.uuid4()), "tarih": time.time(), "tip": "AL", "varlik": secili_varlik,
                                "adet": islem_miktari, "hedef_fiyat": hedef_fiyat, "baglanan_tutar": toplam_islem_maliyeti, "komisyon": komisyon_tutari
                            })
                            aktif_cuzdan_kaydet()
                            st.success("🕒 Alım Limit Emriniz Başarıyla Sisteme Kaydedildi!")
                        else:
                            mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                            yeni_adet = mevcut_veri["adet"] + islem_miktari
                            yeni_maliyet = ((mevcut_veri["adet"] * mevcut_veri["maliyet"]) + toplam_islem_maliyeti) / yeni_adet
                            cuzdan["varliklar"][secili_varlik] = {"adet": yeni_adet, "maliyet": yeni_maliyet}
                            db["_GLOBAL_"]["toplam_komisyon"] += komisyon_tutari
                            aktif_cuzdan_kaydet()
                            st.success("⚡ İşlem Başarılı! Komisyon bağış havuzuna aktarıldı.")
                            
                        time.sleep(1.5); st.rerun() 
                    else: st.error("Yetersiz bakiye (Komisyon dahil)!")
                elif islem_tipi == "SAT":
                    mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                    if mevcut_veri["adet"] >= islem_miktari:
                        yeni_adet = mevcut_veri["adet"] - islem_miktari
                        if yeni_adet <= 0.000001: del cuzdan["varliklar"][secili_varlik]
                        else: cuzdan["varliklar"][secili_varlik]["adet"] = yeni_adet
                        
                        if "Limit" in emir_turu:
                            cuzdan["bekleyen_emirler"].append({
                                "id": str(uuid.uuid4()), "tarih": time.time(), "tip": "SAT", "varlik": secili_varlik,
                                "adet": islem_miktari, "hedef_fiyat": hedef_fiyat, "beklenen_getiri": toplam_islem_getirisi,
                                "komisyon": komisyon_tutari, "maliyet_rezerv": mevcut_veri["maliyet"]
                            })
                            aktif_cuzdan_kaydet()
                            st.success("🕒 Satış Limit Emriniz Başarıyla Sisteme Kaydedildi!")
                        else:
                            cuzdan["nakit"] += toplam_islem_getirisi
                            db["_GLOBAL_"]["toplam_komisyon"] += komisyon_tutari
                            aktif_cuzdan_kaydet()
                            st.success("⚡ İşlem Başarılı! Komisyon bağış havuzuna aktarıldı.")
                            
                        time.sleep(1.5); st.rerun() 
                    else: st.error("Yetersiz adet!")

        with col_durum:
            col_b, col_y = st.columns([3, 1])
            with col_b: st.subheader("Cüzdan")
            with col_y: 
                if st.button("🔄 Yenile", use_container_width=True): st.rerun()
                    
            if cuzdan["varliklar"]:
                liste = []
                for v, d in cuzdan["varliklar"].items():
                    gf = guncel_fiyatlar.get(v, 0)
                    kz_tl = (d["adet"] * gf) - (d["adet"] * d["maliyet"])
                    kz_yuzde = ((gf - d["maliyet"]) / d["maliyet"] * 100) if d["maliyet"] > 0 else 0
                    liste.append({"Varlık": v, "Adet": d["adet"], "Maliyet (₺)": d["maliyet"], "Fiyat (₺)": gf, "Değer (₺)": d["adet"] * gf, "K/Z (₺)": kz_tl, "% K/Z": kz_yuzde})
                
                df_p = pd.DataFrame(liste).sort_values("Değer (₺)", ascending=False)
                def renk_ver(val):
                    try: return 'color: #00ff00; font-weight:bold;' if float(val) > 0 else 'color: #ff4444; font-weight:bold;' if float(val) < 0 else ''
                    except: return ''
                    
                st.dataframe(df_p.style.map(renk_ver, subset=['K/Z (₺)', '% K/Z']).format({"Adet": "{:,.4f}", "Maliyet (₺)": "{:,.2f}", "Fiyat (₺)": "{:,.2f}", "Değer (₺)": "{:,.2f}", "K/Z (₺)": "{:,.2f}", "% K/Z": "% {:,.2f}"}), use_container_width=True)
            else: st.info("Cüzdan boş.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🕒 Bekleyen Emirlerim")
            if cuzdan.get("bekleyen_emirler"):
                for emir in cuzdan["bekleyen_emirler"]:
                    st.markdown(f"<div style='background-color:rgba(15, 23, 42, 0.8); border:1px solid rgba(0,255,255,0.2); padding:10px; border-radius:10px; margin-bottom:10px; backdrop-filter:blur(5px);'>", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
                    tip_ikon = "🟢 AL" if emir["tip"] == "AL" else "🔴 SAT"
                    c1.write(f"**{emir['varlik']}**")
                    c2.write(f"{tip_ikon} ({emir['adet']})")
                    c3.write(f"Hedef: **{emir['hedef_fiyat']:,.2f} ₺**")
                    
                    if c4.button("❌ İptal", key=f"iptal_{emir['id']}"):
                        if emir["tip"] == "AL":
                            cuzdan["nakit"] += emir["baglanan_tutar"]
                        else:
                            mevcut_veri = cuzdan["varliklar"].get(emir["varlik"], {"adet": 0.0, "maliyet": emir.get("maliyet_rezerv", 0.0)})
                            cuzdan["varliklar"][emir["varlik"]] = {"adet": mevcut_veri["adet"] + emir["adet"], "maliyet": emir.get("maliyet_rezerv", 0.0)}
                        
                        cuzdan["bekleyen_emirler"] = [e for e in cuzdan["bekleyen_emirler"] if e["id"] != emir["id"]]
                        aktif_cuzdan_kaydet()
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.caption("Şu an bekleyen aktif bir emriniz bulunmuyor.")

    with tab_liderlik:
        st.subheader("🏆 En İyi Fon Yöneticileri")
        st.write("Sistemdeki tüm yatırımcıların toplam fon büyüklüklerine göre rekabet sıralaması.")
        
        with st.spinner("Sıralama hesaplanıyor..."):
            tum_kullanici_varliklari = set()
            for k, v in db.items():
                if k not in ["_GLOBAL_", "_OTURUMLAR_"] and "cuzdan" in v and "varliklar" in v["cuzdan"]:
                    for varlik_ismi in v["cuzdan"]["varliklar"]:
                        tum_kullanici_varliklari.add(varlik_ismi)
            
            liderlik_fiyatlar = {}
            for varlik_ismi in tum_kullanici_varliklari:
                sembol = tum_varliklar_mega.get(varlik_ismi)
                if sembol:
                    try:
                        fiyat = float(yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1])
                        if not sembol.endswith(".IS"): fiyat *= usd_kuru
                        liderlik_fiyatlar[varlik_ismi] = fiyat
                    except:
                        liderlik_fiyatlar[varlik_ismi] = 0.0
            
            liderlik_listesi = []
            for k, v in db.items():
                if k not in ["_GLOBAL_", "_OTURUMLAR_"] and "cuzdan" in v:
                    kullanici_cuzdan = v["cuzdan"]
                    kullanici_toplam = kullanici_cuzdan.get("nakit", 1000000.0)
                    for be in kullanici_cuzdan.get("bekleyen_emirler", []):
                        if be["tip"] == "AL": kullanici_toplam += be["baglanan_tutar"]
                    
                    if "varliklar" in kullanici_cuzdan:
                        for v_isim, v_veri in kullanici_cuzdan["varliklar"].items():
                            adet = v_veri if isinstance(v_veri, (int, float)) else v_veri.get("adet", 0)
                            kullanici_toplam += adet * liderlik_fiyatlar.get(v_isim, 0.0)
                            
                    for be in kullanici_cuzdan.get("bekleyen_emirler", []):
                        if be["tip"] == "SAT": kullanici_toplam += be["adet"] * liderlik_fiyatlar.get(be["varlik"], 0.0)
                            
                    gosterilecek_isim = v.get("nickname", k)
                    liderlik_listesi.append({"Kullanici": gosterilecek_isim, "Toplam": kullanici_toplam})
            
            liderlik_listesi = sorted(liderlik_listesi, key=lambda x: x["Toplam"], reverse=True)
            
            gosterim_listesi = []
            for i, user_data in enumerate(liderlik_listesi):
                bakiye_str = str(int(user_data["Toplam"]))
                maskeli_bakiye = bakiye_str[0] + ("*" * (len(bakiye_str) - 1)) + " ₺"
                
                sira = str(i + 1)
                if i == 0: sira = "🥇 1"
                elif i == 1: sira = "🥈 2"
                elif i == 2: sira = "🥉 3"
                
                gosterim_listesi.append({
                    "Sıra": sira,
                    "Yatırımcı (Takma Ad)": user_data["Kullanici"].upper(),
                    "Gizli Kasa Büyüklüğü": maskeli_bakiye
                })
                
            st.dataframe(pd.DataFrame(gosterim_listesi).style.hide(axis="index"), use_container_width=True)
            st.info("💡 **Not:** Güvenlik ve rekabet gizliliği amacıyla kullanıcıların gerçek giriş ID'leri değil takma adları gösterilmektedir. Kasa bakiyeleri ise maskelenmiştir.")
