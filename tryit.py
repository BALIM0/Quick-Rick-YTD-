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
import time
import hashlib
import uuid
import firebase_admin
from firebase_admin import credentials, db as firebase_db

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Portföy Analiz ve Yönetimi", layout="wide", page_icon="📊")

# =========================================================================================
# 🔥 FIREBASE VERİTABANI BAĞLANTISI 
# =========================================================================================
if not firebase_admin._apps:
    try:
        cert_dict = json.loads(st.secrets["FIREBASE_SECRET"])
        cred = credentials.Certificate(cert_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["FIREBASE_URL"]
        })
    except Exception as e:
        st.error(f"🚨 Firebase Bağlantı Hatası! Secrets ayarlarınızı kontrol edin. Detay: {e}")
        st.stop()

try:
    ADMIN_ID = st.secrets["ADMIN_ID"]
    ADMIN_PASS = st.secrets["ADMIN_PASS"]
except:
    ADMIN_ID = "admin_master"
    ADMIN_PASS = "supergizli123"

def sifre_sifrele(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def db_yukle():
    try:
        veri = firebase_db.reference('/').get()
        degisiklik_var = False
        
        if veri is None:
            veri = {}
            degisiklik_var = True
            
        if "_GLOBAL_" not in veri: 
            veri["_GLOBAL_"] = {"toplam_komisyon": 0.0, "duyuru": "", "sohbet": []}
            degisiklik_var = True
        else:
            if "sohbet" not in veri["_GLOBAL_"]: 
                veri["_GLOBAL_"]["sohbet"] = []
                degisiklik_var = True
                
        if "_OTURUMLAR_" not in veri: 
            veri["_OTURUMLAR_"] = {}
            degisiklik_var = True
            
        if "_DUELLOLAR_" not in veri: 
            veri["_DUELLOLAR_"] = {}
            degisiklik_var = True
            
        if ADMIN_ID not in veri:
            veri[ADMIN_ID] = {"sifre": sifre_sifrele(ADMIN_PASS), "nickname": "👑 SİSTEM YÖNETİCİSİ", "son_isim_degistirme": 0, "kayit_tarihi": time.time(), "rozetler": [], "istatistikler": {"islem_sayisi": 0, "odenen_komisyon": 0.0, "en_yuksek_kar": 0.0, "favori_varliklar": {}, "duello_karnesi": {"katildigi": 0, "kazandigi": 0}}, "cuzdan": {"nakit": 1000000.0, "varliklar": {}, "kaldiracli_islemler": [], "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)", "NVIDIA", "Apple"], "bekleyen_emirler": [], "banka": {"gecelik": {"miktar": 0.0, "son_guncelleme": time.time()}, "vadeli": []}}, "is_admin": True}
            degisiklik_var = True
            
        for k, v in veri.items():
            if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]:
                if "rozetler" not in v: v["rozetler"] = []
                if "kayit_tarihi" not in v: v["kayit_tarihi"] = time.time()
                
                if "istatistikler" not in v: 
                    v["istatistikler"] = {"islem_sayisi": 0, "odenen_komisyon": 0.0, "en_yuksek_kar": 0.0, "favori_varliklar": {}, "duello_karnesi": {"katildigi": 0, "kazandigi": 0}}
                else:
                    if "en_yuksek_kar" not in v["istatistikler"]: v["istatistikler"]["en_yuksek_kar"] = 0.0
                    if "favori_varliklar" not in v["istatistikler"]: v["istatistikler"]["favori_varliklar"] = {}
                    if "duello_karnesi" not in v["istatistikler"]: v["istatistikler"]["duello_karnesi"] = {"katildigi": 0, "kazandigi": 0}
                
                if "cuzdan" not in v: v["cuzdan"] = {}
                cuz = v["cuzdan"]
                if "nakit" not in cuz: cuz["nakit"] = 1000000.0
                if "varliklar" not in cuz: cuz["varliklar"] = {}
                if "kaldiracli_islemler" not in cuz: cuz["kaldiracli_islemler"] = []
                if "izleme_listesi" not in cuz: cuz["izleme_listesi"] = ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)", "NVIDIA", "Apple"]
                if "bekleyen_emirler" not in cuz: cuz["bekleyen_emirler"] = []
                if "banka" not in cuz: cuz["banka"] = {}
                if "gecelik" not in cuz["banka"]: cuz["banka"]["gecelik"] = {"miktar": 0.0, "son_guncelleme": time.time()}
                if "vadeli" not in cuz["banka"]: cuz["banka"]["vadeli"] = []
        
        if degisiklik_var:
            firebase_db.reference('/').set(veri)
            
        return veri
    except Exception as e:
        st.error(f"Veritabanı Okuma Hatası: {e}")
        return {}

def db_kaydet(veritabani):
    try:
        firebase_db.reference('/').set(veritabani)
    except Exception as e:
        st.error(f"Veritabanı Yazma Hatası: {e}")

# =========================================================================================
# TÜRKİYE STANDARTLARI SAYI FORMATLAYICI
# =========================================================================================
def format_tr(val, decimals=2):
    if pd.isna(val): return ""
    try:
        s = f"{float(val):,.{decimals}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

# =========================================================================================
# --- GELİŞMİŞ UI / UX TASARIMI ---
# =========================================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background: radial-gradient(circle at top right, #131d2b 0%, #0b0f19 100%) !important; }
    [data-testid="stSidebar"] { background-color: #0e131f !important; border-right: 1px solid rgba(0, 255, 255, 0.05) !important; }
    
    div[data-testid="metric-container"] { background: rgba(20, 26, 36, 0.6) !important; backdrop-filter: blur(12px) !important; border: 1px solid rgba(0, 255, 255, 0.15) !important; padding: 20px !important; border-radius: 16px !important; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important; transition: all 0.4s ease-in-out !important; }
    div[data-testid="metric-container"]:hover { transform: translateY(-7px) !important; border-color: rgba(0, 255, 255, 0.6) !important; box-shadow: 0 12px 40px 0 rgba(0, 255, 255, 0.15) !important; }
    
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    @media screen and (max-width: 768px) {
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; white-space: normal !important; word-wrap: break-word !important; }
        [data-testid="stMetricLabel"] p { font-size: 0.85rem !important; }
        div[data-testid="metric-container"] { padding: 12px !important; }
    }

    div.stButton > button { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; color: #fff !important; border: 1px solid rgba(0, 255, 255, 0.3) !important; border-radius: 10px !important; padding: 10px 24px !important; font-weight: 600 !important; letter-spacing: 0.5px !important; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; width: 100% !important; }
    div.stButton > button:hover { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; border-color: #00ffff !important; color: #00ffff !important; box-shadow: 0 0 15px rgba(0, 255, 255, 0.3), inset 0 0 10px rgba(0, 255, 255, 0.1) !important; transform: scale(1.03) !important; }
    button[data-baseweb="tab"] { background-color: transparent !important; border: none !important; border-bottom: 3px solid transparent !important; padding: 12px 20px !important; font-weight: 600 !important; color: #667085 !important; transition: all 0.3s ease !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #00ffff !important; border-bottom: 3px solid #00ffff !important; background-color: rgba(0, 255, 255, 0.05) !important; border-radius: 8px 8px 0 0 !important; }
    button[data-baseweb="tab"]:hover { color: #e2e8f0 !important; background-color: rgba(255, 255, 255, 0.02) !important; }
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], input[type="password"] { border-radius: 10px !important; border: 1px solid #334155 !important; background-color: rgba(15, 23, 42, 0.8) !important; color: white !important; transition: all 0.3s ease !important; }
    div[data-baseweb="select"] > div:hover, input[type="text"]:focus, input[type="number"]:focus, input[type="password"]:focus { border-color: #00ffff !important; box-shadow: 0 0 8px rgba(0,255,255,0.4) !important; }
    .bagis-panosu { text-align: center; padding: 25px; background: linear-gradient(135deg, rgba(255,215,0,0.1) 0%, rgba(255,140,0,0.1) 100%); border-radius: 16px; border: 1px solid rgba(255,215,0,0.4); margin-bottom: 30px; box-shadow: 0 10px 30px rgba(255, 215, 0, 0.08); backdrop-filter: blur(8px); }
    .bagis-sayi { color: #FFD700; font-size: 34px; font-weight: 800; text-shadow: 0 0 20px rgba(255,215,0,0.5); letter-spacing: 1.5px; }
    div.stRadio { width: 100% !important; } div.stRadio > div { width: 100% !important; } div.stRadio div[role="radiogroup"] { display: flex !important; width: 100% !important; align-items: stretch !important; } div.stRadio div[role="radiogroup"] > label { width: 100% !important; min-height: 45px !important; display: flex !important; align-items: center !important; justify-content: center !important; text-align: center !important; padding: 5px 10px !important; border: 1px solid #334155 !important; border-radius: 10px !important; background-color: #0f172a !important; transition: all 0.3s ease !important; cursor: pointer !important; margin: 0 !important; box-sizing: border-box !important; white-space: nowrap !important; overflow: hidden !important; } div.stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; } div.stRadio div[role="radiogroup"] > label p { margin: 0 !important; font-size: 14px !important; width: 100% !important; text-align: center !important; white-space: nowrap !important; } div.stRadio div[role="radiogroup"] > label:hover { border-color: #00ffff !important; background-color: #1e293b !important; box-shadow: 0 4px 15px rgba(0, 255, 255, 0.15) !important; }
    [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] { flex-direction: column !important; gap: 12px !important; width: 100% !important; } [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] > label { flex: 1 1 100% !important; } [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(0,255,255,0.15) 0%, rgba(0,255,255,0.02) 100%) !important; border-color: #00ffff !important; border-left: 5px solid #00ffff !important; } [data-testid="stSidebar"] div.stRadio div[role="radiogroup"] > label:has(input:checked) p { color: #00ffff !important; font-weight: bold !important; }
    [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 15px !important; width: 100% !important; } [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label { flex: 1 1 50% !important; width: 50% !important; } [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(1):has(input:checked) { background: linear-gradient(90deg, rgba(0,255,0,0.15) 0%, rgba(0,255,0,0.02) 100%) !important; border-color: #00ff00 !important; border-left: 5px solid #00ff00 !important; } [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(1):has(input:checked) p { color: #00ff00 !important; font-weight: bold !important; } [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(2):has(input:checked) { background: linear-gradient(90deg, rgba(255,68,68,0.15) 0%, rgba(255,68,68,0.02) 100%) !important; border-color: #ff4444 !important; border-left: 5px solid #ff4444 !important; } [data-testid="stMainBlockContainer"] div.stRadio div[role="radiogroup"] > label:nth-child(2):has(input:checked) p { color: #ff4444 !important; font-weight: bold !important; }
    .sohbet-mesaji { background-color: rgba(15, 23, 42, 0.4); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #334155; } .sohbet-mesaji.admin { border-left: 3px solid #FFD700; background-color: rgba(255, 215, 0, 0.05); }
    .kaldirac-kart { background-color: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 255, 255, 0.2); padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: all 0.3s;} .kaldirac-kart:hover { transform: scale(1.02); } .kaldirac-kart.long { border-left: 5px solid #00ff00; } .kaldirac-kart.short { border-left: 5px solid #ff4444; }
    .banka-kart { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid rgba(255, 215, 0, 0.3); padding: 20px; border-radius: 12px; margin-bottom: 15px; } .pulsing-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #00ff00; animation: pulse 2s infinite; margin-right: 5px; } @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0); } }
    .liderlik-tablosu { width: 100%; border-collapse: collapse; margin-top: 10px; background-color: rgba(15,23,42,0.6); border-radius: 10px; overflow: hidden; } .liderlik-tablosu th { color: #aaa; text-transform: uppercase; font-size: 12px; padding: 15px; border-bottom: 1px solid rgba(0,255,255,0.3); text-align: left; background-color: rgba(0,0,0,0.4); } .liderlik-tablosu td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); font-weight: 600; color: white; } .liderlik-tablosu tr:hover { background-color: rgba(255,255,255,0.05); } .rozet { cursor: help; font-size: 18px; margin-left: 6px; display: inline-block; transition: transform 0.2s; } .rozet:hover { transform: scale(1.4); }
    .online-user-box { display: flex; align-items: center; padding: 8px 10px; margin-bottom: 5px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 2px solid #334155; } .online-user-box.admin-online { border-left: 2px solid #FFD700; background: rgba(255,215,0,0.05); }
</style>
""", unsafe_allow_html=True)

# ROZET SÖZLÜĞÜ
ROZET_ANLAMLARI = {
    "👑": "Oligark: 2.000.000 ₺ (2 Milyon) toplam net varlığa ulaştı.",
    "🐋": "Mavi Balina: Tek işlemde 10.000 ₺ üzerinde net kâr elde etti.",
    "🐺": "Wall Street Kurdu: Sistemde toplam 50 işlem sayısını geçti.",
    "🎰": "Büyük Kumarbaz: Tek işleme 500.000 ₺ ve üzeri nakit teminat bağladı.",
    "🎯": "Keskin Nişancı: Kaldıraçlı bir işlemi %100 (2x) ve üzeri kârla kapattı.",
    "📉": "Büyük Çöküş: Tek bir 'Açığa Satış' (Short) işleminden 50.000 ₺ üzeri kâr etti.",
    "🍱": "Sepet Gurmesi: Cüzdanında aynı anda en az 10 farklı spot varlık tuttu.",
    "💸": "Borsa Sponsoru: Merkez Bankası'na toplam 50.000 ₺'den fazla komisyon ödedi.",
    "🛡️": "Demir İrade: Oyunda 7 günden fazla hayatta kaldı.",
    "🧊": "Buzul Kasa: Varlığını 30 Günlük kilitli mevduata bağlayıp unuttu.",
    "👽": "Kripto Baronu: Sadece kripto varlıklarda tek kalemde 100.000 ₺ hacmi aştı.",
    "⚡": "Kamikaze: Ölümü göze alıp 50x kaldıraçlı işlem açtı.",
    "🏦": "Merkez Bankeri: Parasını vadeli mevduata bağladı.",
    "🐻": "Ayı Pençesi: Piyasalar düşerken açığa satış (Short) yaparak kâr elde etti.",
    "⏳": "Kıdemli Kurt: Sistemde 24 saatten uzun süredir aktif (Tecrübeli Oyuncu)."
}

@st.cache_data(ttl=10, show_spinner=False)
def canli_fiyat_getir(sembol, katsayi=1.0):
    try:
        veri = yf.Ticker(sembol).history(period="5d")
        if isinstance(veri.columns, pd.MultiIndex): veri.columns = veri.columns.get_level_values(0)
        veri.columns = [str(c).title() for c in veri.columns]
        veri = veri.dropna(subset=['Close']).ffill()
        return float(veri['Close'].iloc[-1]) * katsayi
    except: return 0.0

@st.cache_data(ttl=300)
def guncel_kur_getir(): return canli_fiyat_getir("TRY=X", 1.0) or 34.50

if 'aktif_kullanici' not in st.session_state: st.session_state.aktif_kullanici = None

db = db_yukle()

def rozet_ver(db_ref, k_id, rozet, mesaj):
    if rozet not in db_ref[k_id].setdefault("rozetler", []):
        db_ref[k_id]["rozetler"].append(rozet)
        db_kaydet(db_ref) 
        if k_id == st.session_state.get("aktif_kullanici"):
            st.toast(f"YENİ BAŞARIM AÇILDI: {rozet} {mesaj}", icon="🏆")
        return True
    return False

su_an = time.time()
silinecek_oturumlar = [t for t, v in db.get("_OTURUMLAR_", {}).items() if su_an > v["bitis"]]
for t in silinecek_oturumlar: del db["_OTURUMLAR_"][t]
if silinecek_oturumlar: db_kaydet(db)

mevcut_token = st.query_params.get("oturum")
if mevcut_token:
    if mevcut_token in db.get("_OTURUMLAR_", {}):
        st.session_state.aktif_kullanici = db["_OTURUMLAR_"][mevcut_token]["kullanici"]
        db["_OTURUMLAR_"][mevcut_token]["bitis"] = su_an + 600
        db["_OTURUMLAR_"][mevcut_token]["son_hareket"] = su_an 
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
            sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]
            if g_kullanici in db and g_kullanici not in sistem_idleri and db[g_kullanici]["sifre"] == sifre_sifrele(g_sifre):
                yeni_token = str(uuid.uuid4())
                db["_OTURUMLAR_"][yeni_token] = {"kullanici": g_kullanici, "bitis": su_an + 600, "son_hareket": su_an}
                db_kaydet(db)
                st.query_params["oturum"] = yeni_token
                st.session_state.aktif_kullanici = g_kullanici
                st.rerun()
            else: st.error("Kullanıcı adı veya şifre hatalı!")
    with tab_kayit:
        with st.form("kayit_formu"):
            k_kullanici = st.text_input("Sisteme Giriş İçin Kullanıcı Adı (Kimse Görmeyecek)")
            k_nickname = st.text_input("Liderlik Tablosu İçin Takma Ad (Nickname - Herkes Görecek)")
            k_sifre = st.text_input("Yeni Şifre", type="password")
            kayit_buton = st.form_submit_button("Hesap Oluştur", use_container_width=True)
        if kayit_buton:
            sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]
            mevcut_nicknameler = [v.get("nickname", "").lower() for k, v in db.items() if k not in sistem_idleri]
            if k_kullanici in db or k_kullanici in sistem_idleri: st.error("❌ Bu Gizli Kullanıcı Adı zaten alınmış!")
            elif k_nickname.lower() in mevcut_nicknameler: st.error("❌ Bu Takma Ad (Nickname) başka bir yatırımcı tarafından kullanılıyor!")
            elif k_kullanici.lower() == k_nickname.lower(): st.error("🛡️ Güvenlik İhlali: Kullanıcı adı ile Takma Ad aynı olamaz.")
            elif len(k_kullanici) < 3 or len(k_sifre) < 4 or len(k_nickname) < 3: st.warning("Kullanıcı adı/Takma ad en az 3, şifre en az 4 karakter olmalıdır.")
            else:
                db[k_kullanici] = {"sifre": sifre_sifrele(k_sifre), "nickname": k_nickname, "son_isim_degistirme": 0, "kayit_tarihi": time.time(), "rozetler": [], "istatistikler": {"islem_sayisi": 0, "odenen_komisyon": 0.0, "en_yuksek_kar": 0.0, "favori_varliklar": {}, "duello_karnesi": {"katildigi": 0, "kazandigi": 0}}, "cuzdan": {"nakit": 1000000.0, "varliklar": {}, "kaldiracli_islemler": [], "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)", "NVIDIA", "Apple"], "bekleyen_emirler": [], "banka": {"gecelik": {"miktar": 0.0, "son_guncelleme": time.time()}, "vadeli": []}}, "is_admin": False}
                db_kaydet(db)
                st.success("✅ Hesabınız oluşturuldu! Şimdi 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")
    st.stop()

aktif_kullanici = st.session_state.aktif_kullanici

if "cuzdan" not in db[aktif_kullanici]: db[aktif_kullanici]["cuzdan"] = {}
cuzdan = db[aktif_kullanici]["cuzdan"]
if "nakit" not in cuzdan: cuzdan["nakit"] = 1000000.0
if "varliklar" not in cuzdan: cuzdan["varliklar"] = {}
if "kaldiracli_islemler" not in cuzdan: cuzdan["kaldiracli_islemler"] = []
if "izleme_listesi" not in cuzdan: cuzdan["izleme_listesi"] = ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)", "NVIDIA", "Apple"]
if "bekleyen_emirler" not in cuzdan: cuzdan["bekleyen_emirler"] = []
if "banka" not in cuzdan: cuzdan["banka"] = {"gecelik": {"miktar": 0.0, "son_guncelleme": time.time()}, "vadeli": []}

aktif_nickname = db[aktif_kullanici].get("nickname", aktif_kullanici)
is_admin = db[aktif_kullanici].get("is_admin", False)

banka_verisi = cuzdan.get("banka", {"gecelik": {"miktar": 0.0, "son_guncelleme": su_an}, "vadeli": []})
degisiklik_gerekli = False

if banka_verisi["gecelik"]["miktar"] > 0:
    gecen_saniye = su_an - banka_verisi["gecelik"]["son_guncelleme"]
    if gecen_saniye > 0:
        yillik_oran = 0.40
        saniyelik_oran = yillik_oran / (365 * 24 * 3600)
        getiri = banka_verisi["gecelik"]["miktar"] * saniyelik_oran * gecen_saniye
        banka_verisi["gecelik"]["miktar"] += getiri
        degisiklik_gerekli = True

banka_verisi["gecelik"]["son_guncelleme"] = su_an

kalan_vadeli = []
for v in banka_verisi.get("vadeli", []):
    if su_an >= v["bitis"]:
        vade_getirisi = v["miktar"] * v["faiz_orani"] * (v["gun"] / 365)
        cuzdan["nakit"] += v["miktar"] + vade_getirisi
        st.toast(f"🔔 {v['gun']} Günlük Vadeli Hesabınız doldu! Ana para ve {format_tr(vade_getirisi)} ₺ faiz kasanıza yattı.", icon="🏦")
        degisiklik_gerekli = True
    else:
        kalan_vadeli.append(v)

if degisiklik_gerekli or len(kalan_vadeli) != len(banka_verisi.get("vadeli", [])):
    banka_verisi["vadeli"] = kalan_vadeli
    cuzdan["banka"] = banka_verisi
    db_kaydet(db)

def aktif_cuzdan_kaydet():
    db[aktif_kullanici]["cuzdan"] = cuzdan
    db_kaydet(db)

usd_kuru = guncel_kur_getir()

bist_30 = {"Akbank": "AKBNK.IS", "Alarko": "ALARK.IS", "Aselsan": "ASELS.IS", "Astor": "ASTOR.IS", "BİM": "BIMAS.IS", "Borusan": "BRSAN.IS", "Coca-Cola İçecek": "CCOLA.IS", "Emlak Konut": "EKGYO.IS", "Enka": "ENKAI.IS", "Ereğli": "EREGL.IS", "Ford Otosan": "FROTO.IS", "Garanti": "GARAN.IS", "Gübre Fab": "GUBRF.IS", "Hektaş": "HEKTS.IS", "İş Bankası": "ISCTR.IS", "Koç Hol": "KCHOL.IS", "Kontrolmatik": "KONTR.IS", "Koza Altın": "KOZAL.IS", "Kardemir": "KRDMD.IS", "Odaş": "ODAS.IS", "Petkim": "PETKM.IS", "Pegasus": "PGSUS.IS", "Sabancı Hol": "SAHOL.IS", "Sasa": "SASA.IS", "Şişecam": "SISE.IS", "Turkcell": "TCELL.IS", "THY": "THYAO.IS", "Tofaş": "TOASO.IS", "Tüpraş": "TUPRS.IS", "Yapı Kredi": "YKBNK.IS"}
bist_100 = {**bist_30, **{"Alfa Solar": "ALFAS.IS", "Arçelik": "ARCLK.IS", "Brisa": "BRISA.IS", "Çimsa": "CIMSA.IS", "CW Enerji": "CWENE.IS", "Doğuş Oto": "DOAS.IS", "Doğan Hol": "DOHOL.IS", "Eczacıbaşı": "ECILC.IS", "Ege Endüstri": "EGEEN.IS", "Enerjisa": "ENJSA.IS", "Europower": "EUPWR.IS", "Girişim Elk": "GESAN.IS", "Halkbank": "HALKB.IS", "İskenderun D.": "ISDMR.IS", "İş GYO": "ISGYO.IS", "İş Yatırım": "ISMEN.IS", "Konya Çimento": "KONYA.IS", "Kordsa": "KORDS.IS", "Koza Anadolu": "KOZAA.IS", "Mavi": "MAVI.IS", "Migros": "MGROS.IS", "Mia Teknoloji": "MIATK.IS", "Otokar": "OTKAR.IS", "Oyak Çimento": "OYAKC.IS", "Qua Granite": "QUAGR.IS", "Şekerbank": "SKBNK.IS", "Smart Güneş": "SMRTG.IS", "Şok Market": "SOKM.IS", "TAV": "TAVHL.IS", "Tekfen": "TKFEN.IS", "TSKB": "TSKB.IS", "Türk Telekom": "TTKOM.IS", "Türk Traktör": "TTRAK.IS", "Tukaş": "TUKAS.IS", "Ülker": "ULKER.IS", "Vakıfbank": "VAKBN.IS", "Vestel Beyaz": "VESBE.IS", "Vestel": "VESTL.IS", "Yeo Teknoloji": "YEOTK.IS", "Zorlu Enerji": "ZOREN.IS"}}
bist_genis = {**bist_100, **{"Agrotech": "AGROT.IS", "Akfen Yenilenebilir": "AKFYE.IS", "Anadolu Efes": "AEFES.IS", "Anadolu Sigorta": "ANSGR.IS", "Aygaz": "AYGAZ.IS", "Bera Holding": "BERA.IS", "Bien Seramik": "BIENY.IS", "Biotrend": "BIOEN.IS", "Borusan Yatırım": "BRYAT.IS", "Bülbüloğlu Vinç": "BVSAN.IS", "Can Termik": "CANTE.IS", "Çan2 Termik": "CANTE.IS", "CVK Maden": "CVKMD.IS", "Eksun Gıda": "EKSUN.IS", "Esenboğa Elektrik": "ESEN.IS", "Forte Bilgi": "FORTE.IS", "Galata Wind": "GWIND.IS", "GSD Holding": "GSDHO.IS", "Hat-San Gemi": "HATSN.IS", "İmaş Makina": "IMASM.IS", "İnfo Yatırım": "INFO.IS", "İzdemir Enerji": "IZENR.IS", "Kaleseramik": "KLSER.IS", "Kayseri Şeker": "KAYSE.IS", "Kocaer Çelik": "KCAER.IS", "Kuştur Kuşadası": "KSTUR.IS", "Margün Enerji": "MAGEN.IS", "Mercan Kimya": "MERCN.IS", "Naten": "NATEN.IS", "Oyak Yatırım": "OYYAT.IS", "Özsu Balık": "OZSUB.IS", "Penta": "PENTA.IS", "Reeder Teknoloji": "REEDR.IS", "Rubenis Tekstil": "RUBNS.IS", "SDT Uzay": "SDTTR.IS", "Tarkim": "TARKM.IS", "Tatlıpınar Enerji": "TATEN.IS", "Tezol": "TEZOL.IS", "VBT Yazılım": "VBTYZ.IS", "Ziraat GYO": "ZRGYO.IS", "Tab Gıda": "TABGD.IS", "Ebebek": "EBEBK.IS", "Fuzul GYO": "FZLGY.IS", "Aydem": "AYDEM.IS", "Söke Değirmencilik": "SOKE.IS", "Enerya": "ENSRV.IS", "Koton": "KOTON.IS", "Lilak Kağıt": "LILAK.IS", "Rönesans GYO": "RGYAS.IS", "Hareket Proje": "HRKET.IS", "Koç Metalurji": "KOCMT.IS", "Aksa Akrilik": "AKSA.IS", "Aksa Enerji": "AKSEN.IS", "Aksigorta": "AKGRT.IS", "AgeSA Hayat": "AGESA.IS", "Alkim Kimya": "ALKIM.IS", "Afyon Çimento": "AFYON.IS", "Anadolu Isuzu": "ASUZU.IS", "Ard Bilişim": "ARDYZ.IS", "Bursa Çimento": "BUCIM.IS", "Çelebi Hava Servisi": "CLEBI.IS", "Desa Deri": "DESA.IS", "Derimod": "DERIM.IS", "Ege Seramik": "EGSER.IS", "Eczacıbaşı Yatırım": "ECZYT.IS", "Erbosan": "ERBOS.IS", "Goodyear": "GOODY.IS", "Göltaş Çimento": "GOLTS.IS", "Global Yatırım": "GLYHO.IS", "Gedik Yatırım": "GEDIK.IS", "Halk GYO": "HLGYO.IS", "İş Finansal": "ISFIN.IS", "İhlas Holding": "IHLAS.IS", "Jantsa": "JANTS.IS", "Karsan": "KARSN.IS", "Kartonsan": "KARTN.IS", "Karel Elektronik": "KAREL.IS", "Kerevitaş": "KERVT.IS", "Kervan Gıda": "KRVGD.IS", "Kütahya Porselen": "KUTPO.IS", "Klimasan": "KLMSN.IS", "Logo Yazılım": "LOGO.IS", "Lider Turizm": "LIDER.IS", "Net Holding": "NTHOL.IS", "Nuh Çimento": "NUHCM.IS", "Özak GYO": "OZKGY.IS", "Osmanlı Yatırım": "OSMEN.IS", "Papilon Savunma": "PAPIL.IS", "Pınar Süt": "PNSUT.IS", "Pınar Et": "PETUN.IS", "Sinpaş GYO": "SNGYO.IS", "Suwen": "SUWEN.IS", "Torunlar GYO": "TRGYO.IS", "Tat Gıda": "TATGD.IS", "Tümosan": "TMSN.IS", "Vakko": "VAKKO.IS", "Vakıf Finansal": "VAKFN.IS", "Vakıf GYO": "VKGYO.IS", "Yataş": "YATAS.IS", "Yayla Gıda": "YYLGD.IS", "Pasifik GYO": "PSGYO.IS", "Koleksiyon Mobilya": "KLSYN.IS", "Hitit Bilgisayar": "HTTBT.IS", "Orge Enerji": "ORGE.IS", "Arena Bilgisayar": "ARENA.IS", "Lokman Hekim": "LKMNH.IS", "Gentaş": "GENTS.IS", "Bossa": "BOSSA.IS", "E-Data": "EDATA.IS", "Ege Profil": "EGPRO.IS", "Kalekim": "KLKIM.IS", "Ulusoy Un": "ULUUN.IS", "Sarkuysan": "SARKY.IS", "Türkiye Sigorta": "TURSG.IS", "Anadolu Hayat": "ANHYT.IS", "İş Girişim": "ISGSY.IS", "Gözde Girişim": "GOZDE.IS", "Verusa Holding": "VERUS.IS", "İzmir Demir Çelik": "IZMDC.IS", "Çemtaş": "CEMTS.IS", "Banvit": "BANVT.IS", "Altınay Savunma": "ALTNY.IS", "Katmerciler Savunma": "KATMR.IS"}}
abd_hisseleri = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Tesla": "TSLA", "Amazon": "AMZN", "Alphabet (Google)": "GOOGL", "Meta (Facebook)": "META", "AMD": "AMD", "Netflix": "NFLX", "Intel": "INTC", "Coca-Cola (ABD)": "KO", "PepsiCo": "PEP", "McDonald's": "MCD", "Boeing": "BA", "Ford Motor (ABD)": "F", "General Motors": "GM", "Uber": "UBER", "Airbnb": "ABNB", "Disney": "DIS", "Pfizer": "PFE", "Johnson & Johnson": "JNJ", "Visa": "V", "Mastercard": "MA", "JPMorgan Chase": "JPM", "Bank of America": "BAC", "Goldman Sachs": "GS", "Walmart": "WMT", "Nike": "NKE", "Starbucks": "SBUX", "Alibaba": "BABA"}
kripto = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Binance Coin": "BNB-USD", "Ripple (XRP)": "XRP-USD", "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Dogecoin": "DOGE-USD", "Chainlink": "LINK-USD", "Polkadot": "DOT-USD", "Polygon (MATIC)": "MATIC-USD", "Shiba Inu": "SHIB-USD", "Litecoin": "LTC-USD", "TRON": "TRX-USD", "Bitcoin Cash": "BCH-USD", "Uniswap": "UNI-USD", "Cosmos": "ATOM-USD", "Monero": "XMR-USD", "Stellar": "XLM-USD", "Ethereum Classic": "ETC-USD", "VeChain": "VET-USD", "Filecoin": "FIL-USD", "Aave": "AAVE-USD", "Algorand": "ALGO-USD", "EOS": "EOS-USD", "The Sandbox": "SAND-USD", "Decentraland": "MANA-USD", "ApeCoin": "APE-USD", "Fantom": "FTM-USD", "Near Protocol": "NEAR-USD", "Aptos": "APT-USD", "Arbitrum": "ARB-USD", "Injective": "INJ-USD", "Optimism": "OP-USD", "Render": "RNDR-USD", "Kaspa": "KAS-USD", "Pepe": "PEPE-USD", "Bonk": "BONK-USD", "Floki": "FLOKI-USD", "Gala": "GALA-USD", "Fetch.ai": "FET-USD", "dogwifhat": "WIF-USD", "Jupiter": "JUP-USD", "Theta Network": "THETA-USD", "Hedera": "HBAR-USD", "Synthetix": "SNX-USD", "Maker": "MKR-USD", "Celestia": "TIA-USD", "Sei": "SEI-USD", "Manta Network": "MANTA-USD", "Starknet": "STRK-USD", "Ondo": "ONDO-USD", "Pyth Network": "PYTH-USD", "Arweave": "AR-USD", "Immutable": "IMX-USD", "Mantle": "MNT-USD", "Lido DAO": "LDO-USD"}
madenler_emtia = {"Altın (Ons)": "GC=F", "Gümüş (Ons)": "SI=F", "Bakır": "HG=F", "Platin": "PL=F", "Paladyum": "PA=F", "Alüminyum": "ALI=F", "Ham Petrol (WTI)": "CL=F", "Brent Petrol": "BZ=F", "Doğal Gaz": "NG=F", "Isıtma Yakıtı": "HO=F", "Buğday": "ZW=F", "Mısır": "ZC=F", "Soya Fasulyesi": "ZS=F", "Kahve": "KC=F", "Şeker": "SB=F", "Pamuk": "CT=F", "Kakao": "CC=F", "Yulaf": "ZO=F", "Pirinç (Kaba)": "ZR=F", "Canlı Sığır": "LE=F", "Yağsız Domuz": "HE=F", "Kereste": "LBS=F"}

tum_varliklar_mega = {**bist_genis, **abd_hisseleri, **kripto, **madenler_emtia}

st.sidebar.header("🕹️ Uygulama Modu")
modlar = ["💼 Sanal Portföy Yönetimi", "🔍 Algoritmik Piyasa Tarama"]
if is_admin: modlar.append("👑 Yönetici Paneli (Kurucu)")
uygulama_modu = st.sidebar.radio("Mod Seçiniz:", modlar, label_visibility="collapsed")
st.sidebar.markdown("---")

online_user_ids = set()
for token, v_data in db.get("_OTURUMLAR_", {}).items():
    son_hareket = v_data.get("son_hareket", v_data["bitis"] - 600)
    if su_an - son_hareket <= 30: 
        online_user_ids.add(v_data["kullanici"])

with st.sidebar.expander(f"🟢 Çevrimiçi Tüccarlar ({len(online_user_ids)})", expanded=True):
    if not online_user_ids:
        st.caption("Şu an kimse aktif değil.")
    else:
        for uid in online_user_ids:
            if uid in db and uid not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]:
                nick = db[uid].get("nickname", uid)
                rozetler_str = "".join(db[uid].get("rozetler", []))
                if db[uid].get("is_admin", False):
                    st.markdown(f"<div class='online-user-box admin-online'><span class='pulsing-dot'></span> <span><b style='color:#FFD700;'>👑 {nick}</b> {rozetler_str}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='online-user-box'><span class='pulsing-dot'></span> <span><b style='color:white;'>{nick}</b> {rozetler_str}</span></div>", unsafe_allow_html=True)

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
            if st.form_submit_button("Güncelle", use_container_width=True):
                if db[aktif_kullanici]["sifre"] != sifre_sifrele(eski_sifre): st.error("❌ Mevcut şifreniz yanlış!")
                elif yeni_sifre != yeni_sifre_tekrar: st.error("❌ Yeni şifreler eşleşmiyor!")
                elif len(yeni_sifre) < 4: st.warning("⚠️ Şifre en az 4 karakter olmalı.")
                else:
                    db[aktif_kullanici]["sifre"] = sifre_sifrele(yeni_sifre)
                    db_kaydet(db)
                    st.success("✅ Şifre güncellendi!")
    with tab_isim:
        son_degisim = db[aktif_kullanici].get("son_isim_degistirme", 0)
        kalan_saniye = (7 * 24 * 60 * 60) - (su_an - son_degisim)
        if kalan_saniye > 0 and not is_admin:
            kalan_gun, kalan_saat = int(kalan_saniye // (24 * 3600)), int((kalan_saniye % (24 * 3600)) // 3600)
            st.info(f"⏳ Takma adınızı değiştirmek için **{kalan_gun} gün {kalan_saat} saat** beklemelisiniz.")
        else:
            with st.form("isim_degistir_form"):
                st.caption("Sadece Liderlik Tablosunda görünür.")
                yeni_isim = st.text_input("Yeni Takma Ad (Nickname)")
                if st.form_submit_button("İsmi Güncelle", use_container_width=True):
                    mevcut_nicknameler = [v.get("nickname", "").lower() for k, v in db.items() if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]]
                    if yeni_isim.lower() in mevcut_nicknameler and yeni_isim.lower() != aktif_nickname.lower(): st.error("❌ Bu isim kullanılıyor!")
                    elif yeni_isim.lower() == aktif_kullanici.lower() and not is_admin: st.error("❌ Güvenlik: Giriş ID'niz ile aynı olamaz!")
                    elif len(yeni_isim) < 3: st.warning("⚠️ En az 3 karakter olmalı.")
                    else:
                        db[aktif_kullanici]["nickname"] = yeni_isim
                        db[aktif_kullanici]["son_isim_degistirme"] = su_an
                        db_kaydet(db)
                        st.success("✅ İsim güncellendi!")
                        time.sleep(1); st.rerun()
    with tab_sil:
        st.markdown("<span style='font-size: 13px; color: #ff4444;'>Dikkat: Bu işlem kalıcıdır.</span>", unsafe_allow_html=True)
        sil_onay = st.checkbox("Silme işlemini onaylıyorum")
        if st.button("❌ Hesabımı Sil", use_container_width=True, disabled=not sil_onay):
            if is_admin: st.error("Kurucu hesap silinemez!")
            else:
                if aktif_kullanici in db: del db[aktif_kullanici]; db_kaydet(db)
                st.query_params.clear(); st.session_state.aktif_kullanici = None; st.rerun()

st.sidebar.markdown("---")
st.sidebar.warning("**⚠️ YASAL UYARI (YTD)**\nBurada yer alan yatırım bilgi, yorum ve yapay zeka tahminleri yatırım danışmanlığı kapsamında değildir.")

if uygulama_modu == "👑 Yönetici Paneli (Kurucu)":
    st.header("👑 SİSTEM YÖNETİCİSİ (ADMIN) PANELİ")
    st.markdown("Merkez bankası yetkileriyle donatılmış, oyunu ve oyuncuları yöneteceğiniz kontrol paneline hoş geldiniz.")
    tab_oyuncular, tab_ekonomi, tab_duyuru = st.tabs(["👥 Kullanıcı Yönetimi (Ban/Sil)", "🏦 Merkez Bankası (Ekonomi)", "📢 Duyuru & Sohbet"])
    with tab_oyuncular:
        st.subheader("Aktif Kullanıcılar ve Giyotin")
        oyuncu_listesi = []
        for k, v in db.items():
            if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"] and not v.get("is_admin", False):
                bakiye = v.get("cuzdan", {}).get("nakit", 0)
                oyuncu_listesi.append({"ID (Gizli)": k, "Takma Ad": v.get("nickname"), "Nakit Bakiye": f"{format_tr(bakiye)} ₺"})
        if oyuncu_listesi:
            st.dataframe(pd.DataFrame(oyuncu_listesi), use_container_width=True)
            st.markdown("---")
            st.error("☠️ **Hileci/Kural İhlali Yapan Kullanıcıyı Sil (Ban)**")
            silinecek_id = st.selectbox("Sistemden tamamen silinecek oyuncunun GİZLİ ID'sini seçin:", [o["ID (Gizli)"] for o in oyuncu_listesi])
            if st.button("Kullanıcıyı Kalıcı Olarak Sil (BANLA)"):
                if silinecek_id in db: del db[silinecek_id]; db_kaydet(db); st.success(f"{silinecek_id} sistemden silindi!"); time.sleep(1); st.rerun()
        else: st.info("Sistemde şu an yönetici haricinde kimse yok.")

    with tab_ekonomi:
        st.subheader("Ekonomik Müdahaleler")
        st.metric("Merkez Havuzda Biriken Komisyon", f"{format_tr(db['_GLOBAL_'].get('toplam_komisyon', 0.0))} ₺")
        
        st.markdown("---")
        st.markdown("### 🎯 Bireysel Fon Aktarımı (Tek Kullanıcıya)")
        kullanicilar = {k: v.get("nickname", k) for k, v in db.items() if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]}
        if kullanicilar:
            col_b1, col_b2 = st.columns(2)
            with col_b1: secilen_id = st.selectbox("Alıcı Oyuncu Seçin:", list(kullanicilar.keys()), format_func=lambda x: f"{kullanicilar[x]} (ID: {x})")
            with col_b2: bireysel_miktar = st.number_input("Gönderilecek Tutar (₺)", min_value=0.0, value=10000.0, step=1000.0, key="bireysel_para")
            if st.button("💰 Belirtilen Oyuncuya Gönder", use_container_width=True):
                if secilen_id in db:
                    db[secilen_id]["cuzdan"]["nakit"] += bireysel_miktar
                    db_kaydet(db); st.success(f"Başarılı! {kullanicilar[secilen_id]} adlı oyuncuya {format_tr(bireysel_miktar)} ₺ aktarıldı."); time.sleep(1); st.rerun()
        else: st.info("Sistemde şu an para gönderilecek aktif bir oyuncu yok.")
            
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🚁 Tüm Oyunculara Hibe")
            hibe_miktari = st.number_input("Dağıtılacak Tutar (₺)", min_value=0.0, value=50000.0, step=1000.0)
            if st.button("💸 Parayı Herkese Gönder"):
                dagitilan_kisi = 0
                for k, v in db.items():
                    if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]:
                        db[k]["cuzdan"]["nakit"] += hibe_miktari
                        dagitilan_kisi += 1
                db_kaydet(db); st.success(f"Başarılı! {dagitilan_kisi} kişiye toplam {format_tr(dagitilan_kisi * hibe_miktari)} ₺ dağıtıldı.")
        with c2:
            st.markdown("### 🧹 Havuzu Sıfırla")
            if st.button("🔄 Havuzu Sıfırla (0 ₺ Yap)"):
                db["_GLOBAL_"]["toplam_komisyon"] = 0.0; db_kaydet(db); st.success("Komisyon havuzu sıfırlandı!"); time.sleep(1); st.rerun()

    with tab_duyuru:
        st.subheader("Tüm Oyunculara Sistem Mesajı Gönder")
        yeni_duyuru = st.text_area("Duyuru Metni (Silmek için boş bırakıp kaydedin):", value=db["_GLOBAL_"].get("duyuru", ""))
        if st.button("📢 Duyuruyu Yayınla / Güncelle"):
            db["_GLOBAL_"]["duyuru"] = yeni_duyuru; db_kaydet(db); st.success("Duyuru güncellendi!"); time.sleep(1); st.rerun()
        st.markdown("---")
        st.subheader("Sohbet Geçmişini Temizle")
        if st.button("🧹 Borsa Meydanı'ndaki Tüm Mesajları Sil"):
            db["_GLOBAL_"]["sohbet"] = []; db_kaydet(db); st.success("Tüm sohbet geçmişi silindi!"); time.sleep(1); st.rerun()

elif uygulama_modu == "🔍 Algoritmik Piyasa Tarama":
    st.title("📊 Portföy Analiz ve Yönetimi")
    global_duyuru = db["_GLOBAL_"].get("duyuru", "")
    if global_duyuru: st.error(f"📢 **SİSTEM DUYURUSU:** {global_duyuru}")
    st.caption(f"👤 Fon Yöneticisi: **{aktif_nickname.upper()}** | 💵 Güncel Kur (USD/TRY): **{format_tr(usd_kuru)} ₺**")

    st.sidebar.header("⚙️ Tarama Ayarları")
    st.sidebar.markdown("<b>1. Yatırım Vadesi</b>", unsafe_allow_html=True)
    vade_secimi = st.sidebar.radio("Vade:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"], label_visibility="collapsed")
    st.sidebar.markdown("<b>2. İncelenecek Piyasa</b>", unsafe_allow_html=True)
    piyasa_secimi = st.sidebar.radio("Piyasa:", ["🇹🇷 BIST 30 (En Büyükler)", "🇹🇷 BIST 100", "🇹🇷 BIST Tüm (Genişletilmiş)", "🇺🇸 ABD Teknoloji ve Global", "🪙 Kripto Paralar", "⛏️ Tüm Emtia ve Madenler", "👤 Kendi İzleme Listem"], label_visibility="collapsed")

    aktif_varliklar = {}
    if piyasa_secimi == "👤 Kendi İzleme Listem":
        if "ilk_liste" not in st.session_state: st.session_state.ilk_liste = [v for v in cuzdan.get("izleme_listesi", []) if v in tum_varliklar_mega]
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
                    if veri is None or veri.empty: continue
                    
                    if isinstance(veri.columns, pd.MultiIndex):
                        veri.columns = veri.columns.get_level_values(0)
                    veri.columns = [str(c).title() for c in veri.columns]
                    
                    veri = veri.dropna(subset=['Close'])
                    if veri.empty or len(veri) < 20: continue
                    veri = veri.ffill()
                    
                    if 'Volume' not in veri.columns:
                        veri['Volume'] = 1000000.0
                    else:
                        veri['Volume'] = pd.to_numeric(veri['Volume'], errors='coerce').fillna(1000000.0)
                        veri.loc[veri['Volume'] <= 0, 'Volume'] = 1000000.0

                    if piyasa_secimi == "👤 Kendi İzleme Listem":
                        temiz_veri = veri['Close'].copy()
                        temiz_veri.index = pd.to_datetime(temiz_veri.index).tz_localize(None).normalize()
                        portfoy_fiyat_gecmisi[isim] = temiz_veri
                        
                    son_fiyat = float(veri['Close'].iloc[-1])
                    if not sembol.endswith(".IS"): son_fiyat *= usd_kuru
                        
                    puan = 0
                    durum_notu = []

                    if vade_secimi == "⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)":
                        tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3.0
                        para_akisi = tipik_fiyat * veri['Volume']
                        delta_fiyat = tipik_fiyat.diff()
                        pozitif_akis = pd.Series(0.0, index=para_akisi.index)
                        negatif_akis = pd.Series(0.0, index=para_akisi.index)
                        pozitif_akis[delta_fiyat > 0] = para_akisi[delta_fiyat > 0]
                        negatif_akis[delta_fiyat < 0] = para_akisi[delta_fiyat < 0]
                        pozitif_mf = pozitif_akis.rolling(window=14, min_periods=1).sum()
                        negatif_mf = negatif_akis.rolling(window=14, min_periods=1).sum()
                        mfi_ratio = pozitif_mf / negatif_mf.replace(0.0, np.nan)
                        mfi = 100.0 - (100.0 / (1.0 + mfi_ratio))
                        son_mfi = float(mfi.fillna(50.0).iloc[-1])
                        
                        delta = veri['Close'].diff()
                        gain = delta.copy()
                        gain[gain < 0] = 0.0
                        loss = -delta.copy()
                        loss[loss < 0] = 0.0
                        avg_gain = gain.rolling(window=14, min_periods=1).mean()
                        avg_loss = loss.rolling(window=14, min_periods=1).mean()
                        rs = avg_gain / avg_loss.replace(0.0, np.nan)
                        rsi = 100.0 - (100.0 / (1.0 + rs))
                        son_rsi = float(rsi.fillna(50.0).iloc[-1])
                        
                        ema_12 = veri['Close'].ewm(span=12, adjust=False).mean()
                        ema_26 = veri['Close'].ewm(span=26, adjust=False).mean()
                        macd = ema_12 - ema_26
                        macd_sinyal = macd.ewm(span=9, adjust=False).mean()
                        macd_val = float(macd.fillna(0.0).iloc[-1])
                        macd_sinyal_val = float(macd_sinyal.fillna(0.0).iloc[-1])
                        
                        sma_20 = veri['Close'].rolling(window=20, min_periods=1).mean()
                        std_20 = veri['Close'].rolling(window=20, min_periods=1).std().fillna(0.0)
                        son_alt_bant = float((sma_20 - (std_20 * 2.0)).iloc[-1])
                        
                        if not sembol.endswith(".IS"): son_alt_bant *= usd_kuru

                        if son_mfi < 20: puan += 3; durum_notu.append("Hacim: Para Girişi")
                        elif son_mfi > 80: puan -= 2; durum_notu.append("Hacim: Para Çıkışı")
                        if son_rsi < 30: puan += 2; durum_notu.append("RSI: Dipte")
                        if macd_val > macd_sinyal_val: puan += 1; durum_notu.append("MACD: Pozitif")
                        if son_fiyat < son_alt_bant and son_alt_bant > 0: puan += 2; durum_notu.append("BB: Aşırı Düştü")
                            
                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": son_fiyat, "RSI": son_rsi, "MFI (Hacim)": son_mfi, "Puan": puan, "Durum": " | ".join(durum_notu) if durum_notu else "Nötr"})

                    else:
                        sma_50 = veri['Close'].rolling(window=50, min_periods=1).mean()
                        sma_200 = veri['Close'].rolling(window=200, min_periods=1).mean()
                        sma_200_deger = float(sma_200.iloc[-1])
                        sma_50_deger = float(sma_50.iloc[-1])
                        
                        if not sembol.endswith(".IS"): 
                            sma_200_deger *= usd_kuru
                            sma_50_deger *= usd_kuru
                            
                        fk_orani = None
                        if sembol.endswith(".IS") or sembol in abd_hisseleri.values():
                            try: fk_orani = ticker.info.get('trailingPE', None)
                            except: pass

                        if son_fiyat > sma_200_deger: puan += 3; durum_notu.append("Boğa Piyasası")
                        else: puan -= 2; durum_notu.append("Ayı Piyasası")
                        if sma_50_deger > sma_200_deger: puan += 2; durum_notu.append("Altın Kesişim")
                        else: puan -= 1; durum_notu.append("Ölüm Kesişimi")
                        
                        fk_metni = "N/A"
                        if fk_orani and isinstance(fk_orani, (int, float)):
                            fk_metni = str(round(fk_orani, 2))
                            if fk_orani < 15: puan += 2; durum_notu.append("F/K Ucuz")
                            elif fk_orani > 30: puan -= 2

                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": son_fiyat, "200G Ort (₺)": sma_200_deger, "F/K": fk_metni, "Puan": puan, "Durum": " | ".join(durum_notu) if durum_notu else "Nötr"})
                        
                except Exception:
                    pass 
                finally:
                    time.sleep(0.05)
                    islenen += 1
                    ilerleme_cubugu.progress(min(islenen / toplam_varlik, 1.0))
            
            durum_metni.empty() 
            ilerleme_cubugu.empty() 
            
            if sonuclar:
                st.session_state.df_sonuc = pd.DataFrame(sonuclar).sort_values(by="Puan", ascending=False).reset_index(drop=True)
                if piyasa_secimi == "👤 Kendi İzleme Listem" and len(portfoy_fiyat_gecmisi) > 1: st.session_state.ozel_portfoy_verisi = pd.DataFrame(portfoy_fiyat_gecmisi)
                else: st.session_state.ozel_portfoy_verisi = pd.DataFrame()
            else: st.error("📉 Seçilen piyasada kriterlere uygun yeterli geçmiş veri bulunamadı.")
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
                st.dataframe(styled_df.format({"Fiyat (₺)": format_tr, "RSI": lambda x: format_tr(x, 1), "MFI (Hacim)": lambda x: format_tr(x, 1)}), use_container_width=True)
            else:
                st.dataframe(st.session_state.df_sonuc.style.format({"Fiyat (₺)": format_tr, "200G Ort (₺)": format_tr}), use_container_width=True)
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
                        st.write(f"**Beklenen Yıllık Getiri:** %{format_tr(results[0,max_sharpe_idx]*100)}")
                        st.write(f"**Tahmini Yıllık Risk:** %{format_tr(results[1,max_sharpe_idx]*100)}")
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
                    if isinstance(grafik_veri.columns, pd.MultiIndex):
                        grafik_veri.columns = grafik_veri.columns.get_level_values(0)
                    grafik_veri.columns = [str(c).title() for c in grafik_veri.columns]
                    grafik_veri = grafik_veri.dropna(subset=['Close']).ffill()
                
                if not grafik_veri.empty:
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🤖 AI Trend", "📊 Hacim Profili", "🎲 Monte Carlo", "⏪ Backtest", "🗓️ Mevsimsellik", "⚖️ İst. Arbitraj"])
                    
                    with tab1:
                        df_ml = grafik_veri[['Close']].dropna().copy()
                        if len(df_ml) > 10:
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
                        if 'Volume' not in grafik_veri.columns: grafik_veri['Volume'] = 1.0
                        df_vp = grafik_veri[['Close', 'Volume', 'Open', 'High', 'Low']].copy()
                        min_price, max_price = df_vp['Low'].min(), df_vp['High'].max()
                        if min_price != max_price and pd.notna(min_price) and pd.notna(max_price):
                            bins = np.linspace(min_price, max_price, 50)
                            df_vp['Price_Bin'] = pd.cut(df_vp['Close'], bins=bins)
                            vp_grouped = df_vp.dropna().groupby('Price_Bin')['Volume'].sum().reset_index()
                            vp_grouped['Bin_Mid'] = vp_grouped['Price_Bin'].apply(lambda x: x.mid if pd.notnull(x) else 0)
                            fig_vp = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.75, 0.25], horizontal_spacing=0.02)
                            fig_vp.add_trace(go.Candlestick(x=df_vp.index, open=df_vp['Open'], high=df_vp['High'], low=df_vp['Low'], close=df_vp['Close'], name='Fiyat'), row=1, col=1)
                            fig_vp.add_trace(go.Bar(x=vp_grouped['Volume'], y=vp_grouped['Bin_Mid'], orientation='h', name='Fiyat Hacmi', marker=dict(color='rgba(0, 255, 255, 0.6)')), row=1, col=2)
                            fig_vp.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(t=10, b=10), showlegend=False)
                            st.plotly_chart(fig_vp, use_container_width=True)
                        else: st.info("Hacim profili çıkarılamadı.")

                    with tab3:
                        log_returns = np.log(1 + grafik_veri['Close'].pct_change()).dropna()
                        if len(log_returns) > 10:
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
                        delta = df_bt['Close'].diff()
                        gain = delta.copy()
                        gain[gain < 0] = 0.0
                        loss = -delta.copy()
                        loss[loss < 0] = 0.0
                        avg_gain = gain.rolling(window=14, min_periods=1).mean()
                        avg_loss = loss.rolling(window=14, min_periods=1).mean()
                        rs = avg_gain / avg_loss.replace(0.0, np.nan)
                        df_bt['RSI'] = 100.0 - (100.0 / (1.0 + rs))
                        nakit, adet, al_t, al_f, sat_t, sat_f = 10000, 0, [], [], [], []
                        for index, row in df_bt.iterrows():
                            if pd.isna(row['RSI']): continue
                            if row['RSI'] < 30 and adet == 0: adet = nakit / row['Close']; nakit = 0; al_t.append(index); al_f.append(row['Close'])
                            elif row['RSI'] > 70 and adet > 0: nakit = adet * row['Close']; adet = 0; sat_t.append(index); sat_f.append(row['Close'])
                        son_deger = nakit if adet == 0 else adet * df_bt['Close'].iloc[-1]
                        c1, c2 = st.columns(2)
                        c1.metric("Al-Sat Getirisi", f"%{format_tr(((son_deger - 10000) / 10000) * 100)}")
                        c2.metric("Bekleme Getirisi", f"%{format_tr(((df_bt['Close'].iloc[-1] - df_bt['Close'].dropna().iloc[0]) / df_bt['Close'].dropna().iloc[0]) * 100)}")
                        fig3 = go.Figure().add_trace(go.Scatter(x=df_bt.index, y=df_bt['Close'], mode='lines', name='Fiyat', line=dict(color='white')))
                        if al_t: fig3.add_trace(go.Scatter(x=al_t, y=al_f, mode='markers', name='AL', marker=dict(color='green', size=12, symbol='triangle-up')))
                        if sat_t: fig3.add_trace(go.Scatter(x=sat_t, y=sat_f, mode='markers', name='SAT', marker=dict(color='red', size=12, symbol='triangle-down')))
                        fig3.update_layout(height=400, template="plotly_dark", margin=dict(t=10, b=10))
                        st.plotly_chart(fig3, use_container_width=True)

                    with tab5:
                        with st.spinner("Mevsimsellik verisi hesaplanıyor (Son 5 Yıl)..."):
                            try:
                                seas_data = yf.Ticker(secilen_sembol).history(period="5y").dropna(subset=['Close'])
                                if len(seas_data) > 100:
                                    seas_data.index = pd.to_datetime(seas_data.index).tz_localize(None)
                                    monthly_closes = seas_data['Close'].resample('ME').last()
                                    monthly_returns = monthly_closes.pct_change() * 100
                                    df_seas = pd.DataFrame({'Getiri': monthly_returns})
                                    df_seas['Yıl'], df_seas['Ay'] = df_seas.index.year, df_seas.index.month
                                    ay_isimleri = {1: 'Oca', 2: 'Şub', 3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz', 7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'}
                                    heatmap_df = df_seas.pivot(index='Yıl', columns='Ay', values='Getiri').reindex(columns=range(1, 13))
                                    heatmap_df.columns = [ay_isimleri.get(c, str(c)) for c in heatmap_df.columns]
                                    heatmap_df = heatmap_df.dropna(how='all')
                                    fig_heat = px.imshow(heatmap_df, text_auto=".2f", aspect="auto", color_continuous_scale=["#ff4444", "#1a1a1a", "#00ff00"], color_continuous_midpoint=0, labels=dict(x="Aylar", y="Yıllar", color="Getiri (%)"))
                                    fig_heat.update_layout(template="plotly_dark", margin=dict(t=40, b=10))
                                    fig_heat.update_traces(textfont=dict(color="white", weight="bold"))
                                    st.plotly_chart(fig_heat, use_container_width=True)
                                    avg_ret = heatmap_df.mean()
                                    st.info(f"💡 Tarihsel olarak **en çok kazandıran ay: {avg_ret.idxmax()}** (Ort. %{format_tr(avg_ret.max())}) | **En riskli ay: {avg_ret.idxmin()}** (Ort. %{format_tr(avg_ret.min())})")
                                else: st.warning("Yeterli tarihsel veri yok.")
                            except: st.error("Mevsimsellik hesaplanamadı.")

                    with tab6:
                        st.markdown("<p style='font-size:14px; color:#aaa;'>İki varlık arasındaki fiyat makasının (spread) tarihsel ortalamasından ne kadar saptığını Z-Skoru ile ölçer.</p>", unsafe_allow_html=True)
                        ikinci_varlik_isim = st.selectbox("Karşılaştırılacak 2. Varlığı Seçin:", list(tum_varliklar_mega.keys()), index=1 if secilen_isim != list(tum_varliklar_mega.keys())[1] else 0)
                        ikinci_sembol = tum_varliklar_mega.get(ikinci_varlik_isim)
                        
                        if ikinci_sembol and ikinci_sembol != secilen_sembol:
                            with st.spinner("Arbitraj modeli hesaplanıyor..."):
                                try:
                                    veri1 = yf.Ticker(secilen_sembol).history(period="1y")['Close'].dropna()
                                    veri2 = yf.Ticker(ikinci_sembol).history(period="1y")['Close'].dropna()
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
                                        son_z = float(df_pair['Z_Score'].dropna().iloc[-1])
                                        if son_z > 2.0: st.error(f"🚨 **ARBİTRAJ FIRSATI (Aşırı Değerli):** {secilen_isim}, {ikinci_varlik_isim}'e kıyasla ortalamanın çok üzerinde.")
                                        elif son_z < -2.0: st.success(f"🟢 **ARBİTRAJ FIRSATI (Aşırı Ucuz):** {secilen_isim}, {ikinci_varlik_isim}'e kıyasla ortalamanın çok altında.")
                                        else: st.info(f"⚖️ **Denge Durumu:** İki varlık arasındaki oran tarihsel normaller (Z-Skoru: {format_tr(son_z)}) içinde seyrediyor.")
                                    else: st.warning("Eşleşen yeterli tarihsel veri bulunamadı.")
                                except Exception as e: st.warning("Veriler eşleştirilirken bir uyumsuzluk yaşandı.")
                        elif ikinci_sembol == secilen_sembol: st.warning("Lütfen karşılaştırmak için farklı bir varlık seçin.")

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
                                mode="gauge+number", value=toplam_duygu/gecerli_haber, domain={'x': [0, 1], 'y': [0, 1]}, 
                                title={'text': "Medya Hissi", 'font': {'color': 'white'}}, 
                                gauge={'axis': {'range': [-1, 1]}, 'bar': {'color': "white"}, 'steps': [{'range': [-1, -0.2], 'color': "rgba(255,68,68,0.6)"}, {'range': [-0.2, 0.2], 'color': "rgba(150,150,150,0.4)"}, {'range': [0.2, 1], 'color': "rgba(0,200,83,0.6)"}]}
                            ))
                            st.plotly_chart(fig_gauge.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), template="plotly_dark"), use_container_width=True)
                        else: st.info("Haber başlıkları analiz edilemedi.")
                    else: st.info("Bu varlığa ait güncel İngilizce haber bulunamadı.")
                    with st.expander("📰 Son Dakika Haberleri", expanded=True):
                        if haberler:
                            for h in haberler[:5]:
                                t = h.get('title') or h.get('content', {}).get('title', '')
                                if t:
                                    l = h.get('link') or h.get('url') or h.get('content', {}).get('clickThroughUrl', {}).get('url', '#')
                                    st.markdown(f"🔗 **[{t}]({l})**")
                                    st.markdown("---")
                        else: st.write("Gösterilecek haber kaynağı yok.")
                except: st.error("Haber servisine ulaşılamıyor.")

elif uygulama_modu == "💼 Sanal Portföy Yönetimi":

    st.title("📊 Portföy Analiz ve Yönetimi")
    global_duyuru = db["_GLOBAL_"].get("duyuru", "")
    if global_duyuru: st.error(f"📢 **SİSTEM DUYURUSU:** {global_duyuru}")
    st.caption(f"👤 Fon Yöneticisi: **{aktif_nickname.upper()}** | 💵 Güncel Kur (USD/TRY): **{format_tr(usd_kuru)} ₺**")

    @st.dialog("🕵️ Oyuncu Karnesi")
    def profil_goster(profil_id, profil_nick, profil_veri):
        istatistikler = profil_veri.get("istatistikler", {})
        en_yuksek_kar = istatistikler.get("en_yuksek_kar", 0.0)
        dk = istatistikler.get("duello_karnesi", {"katildigi": 0, "kazandigi": 0})
        fav = istatistikler.get("favori_varliklar", {})
        
        win_rate = (dk["kazandigi"] / dk["katildigi"] * 100) if dk["katildigi"] > 0 else 0
        sirali_fav = sorted(fav.items(), key=lambda x: x[1], reverse=True)[:3]
        
        rozetler_str = "".join(profil_veri.get("rozetler", []))
        
        st.markdown(f"<h2 style='text-align:center; color:#FFD700; margin-bottom:5px;'>{profil_nick}</h2>", unsafe_allow_html=True)
        if rozetler_str:
            st.markdown(f"<div style='text-align:center; font-size:24px; margin-bottom:20px;'>{rozetler_str}</div>", unsafe_allow_html=True)
            
        c1, c2 = st.columns(2)
        c1.metric("💰 En Büyük Vurgun", f"+{format_tr(en_yuksek_kar)} ₺")
        c2.metric("⚔️ Arena Başarısı", f"%{format_tr(win_rate, 0)}", f"{dk['kazandigi']} Galibiyet / {dk['katildigi']} Maç")
        
        st.markdown("---")
        st.markdown("#### 🔥 En Çok İşlem Yaptığı Varlıklar")
        if sirali_fav:
            for v_isim, count in sirali_fav:
                st.markdown(f"- **{v_isim}** ({count} İşlem)")
        else:
            st.caption("Henüz yeterli işlem geçmişi yok.")

    toplam_komisyon = db["_GLOBAL_"].get("toplam_komisyon", 0.0)
    st.markdown(f"<div class='bagis-panosu'>🌟 <b>Merkez Bankası Komisyon ve Likidasyon Havuzu:</b> <br><span class='bagis-sayi'>{format_tr(toplam_komisyon)} ₺</span></div>", unsafe_allow_html=True)

    tab_portfoy, tab_banka, tab_arena, tab_liderlik, tab_sohbet = st.tabs(["💼 Portföyüm", "🏦 Banka (Faiz)", "⚔️ Arena (Düello)", "🏆 Liderlik Tablosu", "💬 Borsa Meydanı"])
    
    with tab_portfoy:
        
        toplam_varlik_degeri = 0
        guncel_fiyatlar_metrik = {}
        
        if cuzdan.get("varliklar"):
            for varlik_ismi, v_veri in list(cuzdan["varliklar"].items()):
                if isinstance(v_veri, (int, float)): 
                    cuzdan["varliklar"][varlik_ismi] = {"adet": v_veri, "maliyet": 0.0}
                    aktif_cuzdan_kaydet()
                    adet = v_veri
                else: 
                    adet = v_veri["adet"]
                    
                sembol = tum_varliklar_mega.get(varlik_ismi)
                if sembol:
                    anlik_f = canli_fiyat_getir(sembol, usd_kuru if not sembol.endswith(".IS") else 1.0)
                    guncel_fiyatlar_metrik[varlik_ismi] = anlik_f
                    toplam_varlik_degeri += (anlik_f * adet)

        toplam_kaldirac_net_deger = 0
        for poz in cuzdan.get("kaldiracli_islemler", []):
            if poz["varlik"] not in guncel_fiyatlar_metrik:
                sembol = tum_varliklar_mega.get(poz["varlik"])
                anlik_f = canli_fiyat_getir(sembol, usd_kuru if not sembol.endswith(".IS") else 1.0) if sembol else poz["giris_fiyati"]
                guncel_fiyatlar_metrik[poz["varlik"]] = anlik_f
            
            g_fiyat = guncel_fiyatlar_metrik[poz["varlik"]]
            if poz["yon"] == "AL (Long)":
                pnl = (g_fiyat - poz["giris_fiyati"]) * poz["adet"]
            else:
                pnl = (poz["giris_fiyati"] - g_fiyat) * poz["adet"]
            toplam_kaldirac_net_deger += max(0, poz["teminat"] + pnl)

        banka_mevcut = cuzdan.get("banka", {"gecelik": {"miktar": 0.0}, "vadeli": []})
        toplam_banka = banka_mevcut["gecelik"]["miktar"] + sum([v["miktar"] for v in banka_mevcut["vadeli"]])

        toplam_portfoy = cuzdan["nakit"] + toplam_varlik_degeri + toplam_kaldirac_net_deger + toplam_banka
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Toplam Net Değer", f"{format_tr(toplam_portfoy)} ₺", f"% {format_tr(((toplam_portfoy - 1000000.0) / 1000000.0) * 100)}")
        col2.metric("Boş Nakit", f"{format_tr(cuzdan['nakit'])} ₺")
        col3.metric("Yatırımdaki Varlıklar", f"{format_tr(toplam_varlik_degeri + toplam_kaldirac_net_deger)} ₺")
        col4.metric("Bankadaki Nakit (Faiz)", f"{format_tr(toplam_banka)} ₺")
        st.markdown("---")

        col_islem, col_durum = st.columns([1, 2])
        
        with col_islem:
            st.markdown("<b>Hızlı İşlem Masası</b>", unsafe_allow_html=True)
            kaldirac_orani = st.select_slider("⚡ Kaldıraç Oranı (1x = Spot)", options=[1, 2, 5, 10, 25, 50], value=1)
            c_yon, c_tur = st.columns(2)
            with c_yon: 
                yon_opsiyonlari = ["AL", "SAT"] if kaldirac_orani == 1 else ["AL (Long)", "SAT (Short)"]
                islem_tipi = st.radio("İşlem Yönü:", yon_opsiyonlari, horizontal=True, label_visibility="collapsed")
            with c_tur: 
                emir_opsiyonlari = ["⚡ Piyasa", "🕒 Limit"] if kaldirac_orani == 1 else ["⚡ Piyasa"]
                emir_turu = st.radio("Emir Türü:", emir_opsiyonlari, horizontal=True, label_visibility="collapsed")
            
            secili_varlik = st.selectbox("Varlık Seçin:", list(tum_varliklar_mega.keys()))
            sembol_islem = tum_varliklar_mega[secili_varlik]
            
            if secili_varlik in bist_genis: baz_komisyon = 0.0015
            elif secili_varlik in abd_hisseleri: baz_komisyon = 0.0025
            elif secili_varlik in kripto: baz_komisyon = 0.0020
            else: baz_komisyon = 0.0010
            
            if kaldirac_orani > 1:
                komisyon_orani = baz_komisyon / 10 
                komisyon_metni = f"%{format_tr(komisyon_orani*100, 3)} (Kaldıraçlı İndirim)"
            else:
                komisyon_orani = baz_komisyon
                komisyon_metni = f"%{format_tr(komisyon_orani*100, 3)} (Spot)"

            try:
                anlik_fiyat = canli_fiyat_getir(sembol_islem, usd_kuru if not sembol_islem.endswith(".IS") else 1.0)
                if anlik_fiyat == 0.0: raise ValueError("Fiyat sıfır geldi")
                son_hacim = 1000000.0 
                max_islem_limiti = son_hacim * 0.10 
                st.write(f"Anlık Fiyat: **{format_tr(anlik_fiyat)} ₺**")
            except Exception as e:
                anlik_fiyat, max_islem_limiti = 0.0, float('inf')
                st.warning(f"Fiyat çekilemedi. Hata: {str(e)}")

            if kaldirac_orani == 1:
                islem_miktari = st.number_input("Adet / Miktar:", min_value=0.01, step=1.0)
                limit_asildi = islem_miktari > max_islem_limiti
                if limit_asildi: st.error(f"🚨 LİKİDİTE KISITI: En fazla {format_tr(max_islem_limiti)} adet alabilirsiniz!")
                
                if "Limit" in emir_turu:
                    hedef_fiyat = st.number_input("Hedef Fiyat (₺):", min_value=0.01, value=float(anlik_fiyat) if anlik_fiyat>0 else 1.0, step=1.0)
                    islem_tutari = islem_miktari * hedef_fiyat
                else:
                    hedef_fiyat = anlik_fiyat
                    islem_tutari = islem_miktari * anlik_fiyat
                    
                komisyon_tutari = islem_tutari * komisyon_orani
                toplam_islem_maliyeti = islem_tutari + komisyon_tutari 
                toplam_islem_getirisi = islem_tutari - komisyon_tutari 

                st.write(f"İşlem Hacmi: **{format_tr(islem_tutari)} ₺**")
                st.write(f"Komisyon ({komisyon_metni}): **{format_tr(komisyon_tutari)} ₺**")
                if islem_tipi == "AL": st.info(f"Kasadan Çıkacak: **{format_tr(toplam_islem_maliyeti)} ₺**")
                else: st.success(f"Kasaya Girecek: **{format_tr(toplam_islem_getirisi)} ₺**")

                buton_metni = "🕒 Bekleyen Emir Gir" if "Limit" in emir_turu else "⚡ Siparişi Anında Onayla"
                if st.button(buton_metni, use_container_width=True) and anlik_fiyat > 0 and not limit_asildi:
                    
                    db[aktif_kullanici]["istatistikler"]["islem_sayisi"] += 1
                    db[aktif_kullanici]["istatistikler"]["odenen_komisyon"] += komisyon_tutari
                    db[aktif_kullanici]["istatistikler"].setdefault("favori_varliklar", {})
                    db[aktif_kullanici]["istatistikler"]["favori_varliklar"][secili_varlik] = db[aktif_kullanici]["istatistikler"]["favori_varliklar"].get(secili_varlik, 0) + 1
                    
                    if islem_tipi == "AL":
                        if cuzdan["nakit"] >= toplam_islem_maliyeti:
                            cuzdan["nakit"] -= toplam_islem_maliyeti
                            if "Limit" in emir_turu:
                                cuzdan["bekleyen_emirler"].append({"id": str(uuid.uuid4()), "tarih": time.time(), "tip": "AL", "varlik": secili_varlik, "adet": islem_miktari, "hedef_fiyat": hedef_fiyat, "baglanan_tutar": toplam_islem_maliyeti, "komisyon": komisyon_tutari})
                                st.success("🕒 Alım Limit Emriniz Kaydedildi!")
                            else:
                                mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                                yeni_adet = mevcut_veri["adet"] + islem_miktari
                                cuzdan["varliklar"][secili_varlik] = {"adet": yeni_adet, "maliyet": ((mevcut_veri["adet"] * mevcut_veri["maliyet"]) + toplam_islem_maliyeti) / yeni_adet}
                                db["_GLOBAL_"]["toplam_komisyon"] += komisyon_tutari
                                st.success("⚡ İşlem Başarılı!")
                            
                            if db[aktif_kullanici]["istatistikler"]["islem_sayisi"] >= 50: rozet_ver(db, aktif_kullanici, "🐺", "Wall Street Kurdu")
                            if db[aktif_kullanici]["istatistikler"]["odenen_komisyon"] >= 50000: rozet_ver(db, aktif_kullanici, "💸", "Borsa Sponsoru")
                            if secili_varlik in kripto and islem_tutari >= 100000: rozet_ver(db, aktif_kullanici, "👽", "Kripto Baronu")
                                
                            aktif_cuzdan_kaydet()
                            time.sleep(1); st.rerun() 
                        else: st.error("Yetersiz bakiye!")
                    elif islem_tipi == "SAT":
                        mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                        if mevcut_veri["adet"] >= islem_miktari:
                            yeni_adet = mevcut_veri["adet"] - islem_miktari
                            
                            if "Limit" not in emir_turu:
                                net_kar = toplam_islem_getirisi - (mevcut_veri["maliyet"] * islem_miktari)
                                if net_kar > db[aktif_kullanici]["istatistikler"].get("en_yuksek_kar", 0.0):
                                    db[aktif_kullanici]["istatistikler"]["en_yuksek_kar"] = net_kar
                                if net_kar >= 10000: rozet_ver(db, aktif_kullanici, "🐋", "Mavi Balina")

                            if yeni_adet <= 0.000001: del cuzdan["varliklar"][secili_varlik]
                            else: cuzdan["varliklar"][secili_varlik]["adet"] = yeni_adet
                            if "Limit" in emir_turu:
                                cuzdan["bekleyen_emirler"].append({"id": str(uuid.uuid4()), "tarih": time.time(), "tip": "SAT", "varlik": secili_varlik, "adet": islem_miktari, "hedef_fiyat": hedef_fiyat, "beklenen_getiri": toplam_islem_getirisi, "komisyon": komisyon_tutari, "maliyet_rezerv": mevcut_veri["maliyet"]})
                                st.success("🕒 Satış Limit Emriniz Kaydedildi!")
                            else:
                                cuzdan["nakit"] += toplam_islem_getirisi
                                db["_GLOBAL_"]["toplam_komisyon"] += komisyon_tutari
                                st.success("⚡ İşlem Başarılı!")
                                
                            if db[aktif_kullanici]["istatistikler"]["islem_sayisi"] >= 50: rozet_ver(db, aktif_kullanici, "🐺", "Wall Street Kurdu")
                            if db[aktif_kullanici]["istatistikler"]["odenen_komisyon"] >= 50000: rozet_ver(db, aktif_kullanici, "💸", "Borsa Sponsoru")
                            if secili_varlik in kripto and islem_tutari >= 100000: rozet_ver(db, aktif_kullanici, "👽", "Kripto Baronu")
                                
                            aktif_cuzdan_kaydet()
                            time.sleep(1); st.rerun() 
                        else: st.error("Yetersiz adet!")
            
            else:
                girilen_teminat = st.number_input("Bağlanacak Nakit Teminat (₺):", min_value=10.0, value=10.0, step=100.0)
                islem_hacmi = girilen_teminat * kaldirac_orani
                alinacak_adet = islem_hacmi / anlik_fiyat if anlik_fiyat > 0 else 0
                
                limit_asildi = alinacak_adet > max_islem_limiti
                if limit_asildi: st.error(f"🚨 Hacim çok büyük! Tahtayı bozmamak için teminatı veya kaldıracı düşürün.")
                
                if islem_tipi == "AL (Long)": liq_fiyat = anlik_fiyat * (1 - (1/kaldirac_orani))
                else: liq_fiyat = anlik_fiyat * (1 + (1/kaldirac_orani))
                
                st.info(f"📊 Pozisyon Büyüklüğü: **{format_tr(islem_hacmi)} ₺** ({format_tr(alinacak_adet, 4)} Adet)")
                komisyon_tutari = islem_hacmi * komisyon_orani
                st.write(f"Sisteme Ödenecek Komisyon: **{format_tr(komisyon_tutari)} ₺**")
                st.error(f"🚨 **Likidasyon Fiyatı:** {format_tr(liq_fiyat)} ₺ (Fiyat buraya gelirse paranız yanar!)")

                if st.button("🚀 Kaldıraçlı Pozisyonu Aç", use_container_width=True) and anlik_fiyat > 0 and not limit_asildi:
                    gerekli_nakit = girilen_teminat + komisyon_tutari
                    if cuzdan["nakit"] >= gerekli_nakit:
                        cuzdan["nakit"] -= gerekli_nakit
                        db["_GLOBAL_"]["toplam_komisyon"] += komisyon_tutari
                        
                        db[aktif_kullanici]["istatistikler"]["islem_sayisi"] += 1
                        db[aktif_kullanici]["istatistikler"]["odenen_komisyon"] += komisyon_tutari
                        db[aktif_kullanici]["istatistikler"].setdefault("favori_varliklar", {})
                        db[aktif_kullanici]["istatistikler"]["favori_varliklar"][secili_varlik] = db[aktif_kullanici]["istatistikler"]["favori_varliklar"].get(secili_varlik, 0) + 1
                        
                        yeni_pozisyon = {
                            "id": str(uuid.uuid4()), "varlik": secili_varlik, "yon": islem_tipi, "kaldirac": kaldirac_orani,
                            "teminat": girilen_teminat, "adet": alinacak_adet, "giris_fiyati": anlik_fiyat,
                            "liq_fiyati": liq_fiyat, "tarih": time.time()
                        }
                        cuzdan["kaldiracli_islemler"].append(yeni_pozisyon)
                        
                        if kaldirac_orani == 50: rozet_ver(db, aktif_kullanici, "⚡", "Kamikaze")
                        if girilen_teminat >= 500000: rozet_ver(db, aktif_kullanici, "🎰", "Büyük Kumarbaz")
                        if secili_varlik in kripto and islem_hacmi >= 100000: rozet_ver(db, aktif_kullanici, "👽", "Kripto Baronu")
                        if db[aktif_kullanici]["istatistikler"]["islem_sayisi"] >= 50: rozet_ver(db, aktif_kullanici, "🐺", "Wall Street Kurdu")
                        if db[aktif_kullanici]["istatistikler"]["odenen_komisyon"] >= 50000: rozet_ver(db, aktif_kullanici, "💸", "Borsa Sponsoru")
                            
                        aktif_cuzdan_kaydet()
                        st.success(f"{kaldirac_orani}x {islem_tipi} Pozisyonu Başarıyla Açıldı!")
                        time.sleep(1); st.rerun()
                    else:
                        st.error(f"Yetersiz Nakit! Teminat + Komisyon için {format_tr(gerekli_nakit)} ₺ gerekiyor.")

        with col_durum:
            def canli_portfoy_motoru():
                try:
                    db_canli = db_yukle()
                    cz_canli = db_canli[aktif_kullanici]["cuzdan"]
                    degisiklik_var = False
                    mesaj_listesi = []
                    
                    st.markdown("<span class='pulsing-dot'></span> <span style='color:#00ffff; font-size:12px; font-weight:bold;'>Canlı Veri Akışı Aktif (Her 10 Sn)</span>", unsafe_allow_html=True)
                    
                    guncel_fiyatlar = {}
                    tum_varlik_isimleri = set(cz_canli.get("varliklar", {}).keys())
                    for poz in cz_canli.get("kaldiracli_islemler", []): tum_varlik_isimleri.add(poz["varlik"])
                    for em in cz_canli.get("bekleyen_emirler", []): tum_varlik_isimleri.add(em["varlik"])
                    
                    for v_ismi in tum_varlik_isimleri:
                        sembol = tum_varliklar_mega.get(v_ismi)
                        if sembol:
                            kat = usd_kuru if not sembol.endswith(".IS") else 1.0
                            guncel_fiyatlar[v_ismi] = canli_fiyat_getir(sembol, kat)

                    kalan_emirler = []
                    for emir in cz_canli.get("bekleyen_emirler", []):
                        anlik = guncel_fiyatlar.get(emir["varlik"], 0.0)
                        if anlik > 0:
                            if emir["tip"] == "AL" and anlik <= emir["hedef_fiyat"]:
                                mevcut = cz_canli["varliklar"].get(emir["varlik"], {"adet": 0.0, "maliyet": 0.0})
                                if isinstance(mevcut, (int, float)): mevcut = {"adet": mevcut, "maliyet": 0.0}
                                yn_adet = mevcut["adet"] + emir["adet"]
                                yn_maliyet = ((mevcut["adet"] * mevcut["maliyet"]) + emir["baglanan_tutar"]) / yn_adet
                                cz_canli["varliklar"][emir["varlik"]] = {"adet": yn_adet, "maliyet": yn_maliyet}
                                db_canli["_GLOBAL_"]["toplam_komisyon"] += emir["komisyon"]
                                mesaj_listesi.append(f"🔔 {emir['varlik']} hedefe ulaştı! SPOT ALIM yapıldı.")
                                degisiklik_var = True
                            elif emir["tip"] == "SAT" and anlik >= emir["hedef_fiyat"]:
                                cz_canli["nakit"] += emir["beklenen_getiri"]
                                db_canli["_GLOBAL_"]["toplam_komisyon"] += emir["komisyon"]
                                
                                net_k = emir["beklenen_getiri"] - (emir.get("maliyet_rezerv", 0.0) * emir["adet"])
                                if net_k > db_canli[aktif_kullanici]["istatistikler"].get("en_yuksek_kar", 0.0):
                                    db_canli[aktif_kullanici]["istatistikler"]["en_yuksek_kar"] = net_k
                                    
                                mesaj_listesi.append(f"🔔 {emir['varlik']} hedefe ulaştı! SPOT SATIŞ yapıldı.")
                                degisiklik_var = True
                            else: kalan_emirler.append(emir)
                        else: kalan_emirler.append(emir)
                    cz_canli["bekleyen_emirler"] = kalan_emirler

                    kalan_pozisyonlar = []
                    for poz in cz_canli.get("kaldiracli_islemler", []):
                        anlik = guncel_fiyatlar.get(poz["varlik"], 0.0)
                        if anlik > 0:
                            patladi = False
                            if poz["yon"] == "AL (Long)" and anlik <= poz["liq_fiyati"]: patladi = True
                            elif poz["yon"] == "SAT (Short)" and anlik >= poz["liq_fiyati"]: patladi = True
                            
                            if patladi:
                                db_canli["_GLOBAL_"]["toplam_komisyon"] += poz["teminat"]
                                mesaj_listesi.append(f"🚨 {poz['varlik']} {poz['kaldirac']}x {poz['yon']} MARGIN CALL! ({format_tr(poz['teminat'])} ₺ Yandı)")
                                degisiklik_var = True
                            else: kalan_pozisyonlar.append(poz)
                        else: kalan_pozisyonlar.append(poz)
                    cz_canli["kaldiracli_islemler"] = kalan_pozisyonlar
                    
                    if len(cz_canli.get("varliklar", {})) >= 10:
                        if rozet_ver(db_canli, aktif_kullanici, "🍱", "Sepet Gurmesi"):
                            degisiklik_var = True

                    if degisiklik_var:
                        db_kaydet(db_canli)
                        for m in mesaj_listesi: st.toast(m, icon="🔥" if "MARGIN" in m else "✅")
                        time.sleep(1); st.rerun()

                    st.subheader("Cüzdan")
                    if cz_canli.get("varliklar"):
                        liste = []
                        for v, d in cz_canli["varliklar"].items():
                            maliyet = d["maliyet"] if isinstance(d, dict) else 0.0
                            adet = d["adet"] if isinstance(d, dict) else d
                            gf = guncel_fiyatlar.get(v, 0)
                            liste.append({"Varlık": v, "Adet": adet, "Maliyet (₺)": maliyet, "Fiyat (₺)": gf, "Değer (₺)": adet * gf, "K/Z (₺)": (adet * gf) - (adet * maliyet), "% K/Z": ((gf - maliyet) / maliyet * 100) if maliyet > 0 else 0})
                        df_p = pd.DataFrame(liste).sort_values("Değer (₺)", ascending=False)
                        
                        if hasattr(df_p.style, "map"):
                            styled_p = df_p.style.map(lambda val: 'color: #00ff00; font-weight:bold;' if float(val) > 0 else 'color: #ff4444; font-weight:bold;' if float(val) < 0 else '', subset=['K/Z (₺)', '% K/Z'])
                        else:
                            styled_p = df_p.style.applymap(lambda val: 'color: #00ff00; font-weight:bold;' if float(val) > 0 else 'color: #ff4444; font-weight:bold;' if float(val) < 0 else '', subset=['K/Z (₺)', '% K/Z'])
                            
                        st.dataframe(styled_p.format({
                            "Adet": lambda x: format_tr(x, 4), 
                            "Maliyet (₺)": format_tr, 
                            "Fiyat (₺)": format_tr, 
                            "Değer (₺)": format_tr, 
                            "K/Z (₺)": format_tr, 
                            "% K/Z": lambda x: f"% {format_tr(x)}"
                        }), use_container_width=True)
                    else: st.caption("Spot cüzdanınız boş.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("🚀 Aktif Kaldıraçlı İşlemler")
                    if cz_canli.get("kaldiracli_islemler"):
                        for poz in cz_canli["kaldiracli_islemler"]:
                            gf = guncel_fiyatlar.get(poz["varlik"], poz["giris_fiyati"])
                            pnl = (gf - poz["giris_fiyati"]) * poz["adet"] if poz["yon"] == "AL (Long)" else (poz["giris_fiyati"] - gf) * poz["adet"]
                            roe_yuzde = (pnl / poz["teminat"]) * 100
                            net_nakit_karsiligi = max(0, poz["teminat"] + pnl)
                            
                            kaldirac_html = (
                                f"<div class='kaldirac-kart {'long' if poz['yon'] == 'AL (Long)' else 'short'}'>"
                                f"<div style='display:flex; justify-content:space-between; margin-bottom:10px;'>"
                                f"<b>{poz['varlik']}</b><span style='background:#1e293b; padding:2px 8px; border-radius:5px;'>{poz['kaldirac']}x {poz['yon']}</span></div>"
                                f"<div style='display:flex; justify-content:space-between; font-size:14px; color:#aaa;'>"
                                f"<span>Giriş: {format_tr(poz['giris_fiyati'])} ₺</span><span>Anlık: <span style='color:white'>{format_tr(gf)} ₺</span></span></div>"
                                f"<div style='display:flex; justify-content:space-between; font-size:14px; margin-top:5px;'>"
                                f"<span>Liq: <span style='color:#ff4444'>{format_tr(poz['liq_fiyati'])} ₺</span></span><span>Bağlanan: {format_tr(poz['teminat'])} ₺</span></div>"
                                f"<div style='text-align:right; margin-top:10px; font-size:18px; font-weight:bold; color:{'#00ff00' if pnl > 0 else '#ff4444'};'>"
                                f"{format_tr(pnl)} ₺ ( %{format_tr(roe_yuzde)} )</div></div>"
                            )
                            st.markdown(kaldirac_html, unsafe_allow_html=True)
                            
                            if st.button("❌ Pozisyonu Kapat", key=f"kapat_{poz['id']}"):
                                v_isim = poz["varlik"]
                                if v_isim in bist_genis: kop_oran = 0.0015 / 10
                                elif v_isim in abd_hisseleri: kop_oran = 0.0025 / 10
                                elif v_isim in kripto: kop_oran = 0.0020 / 10
                                else: kop_oran = 0.0010 / 10
                                    
                                kapanis_komisyonu = (gf * poz["adet"]) * kop_oran
                                nihai_iade = net_nakit_karsiligi - kapanis_komisyonu
                                
                                cz_canli["nakit"] += max(0, nihai_iade)
                                db_canli["_GLOBAL_"]["toplam_komisyon"] += kapanis_komisyonu
                                db_canli[aktif_kullanici]["istatistikler"]["odenen_komisyon"] += kapanis_komisyonu
                                db_canli[aktif_kullanici]["istatistikler"]["islem_sayisi"] += 1
                                
                                if pnl > db_canli[aktif_kullanici]["istatistikler"].get("en_yuksek_kar", 0.0):
                                    db_canli[aktif_kullanici]["istatistikler"]["en_yuksek_kar"] = pnl
                                
                                cz_canli["kaldiracli_islemler"] = [p for p in cz_canli["kaldiracli_islemler"] if p["id"] != poz["id"]]
                                
                                if pnl >= 10000: rozet_ver(db_canli, aktif_kullanici, "🐋", "Mavi Balina")
                                if pnl >= 50000 and "Short" in poz["yon"]: rozet_ver(db_canli, aktif_kullanici, "📉", "Büyük Çöküş")
                                if roe_yuzde >= 100: rozet_ver(db_canli, aktif_kullanici, "🎯", "Keskin Nişancı")
                                if db_canli[aktif_kullanici]["istatistikler"]["odenen_komisyon"] >= 50000: rozet_ver(db_canli, aktif_kullanici, "💸", "Borsa Sponsoru")
                                if db_canli[aktif_kullanici]["istatistikler"]["islem_sayisi"] >= 50: rozet_ver(db_canli, aktif_kullanici, "🐺", "Wall Street Kurdu")
                                
                                db_kaydet(db_canli)
                                st.success(f"Pozisyon kapandı! Kasanıza {format_tr(max(0, nihai_iade))} ₺ eklendi.")
                                time.sleep(1); st.rerun()
                    else: st.caption("Açık kaldıraçlı işleminiz bulunmuyor.")

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("🕒 Bekleyen Spot Emirlerim")
                    if cz_canli.get("bekleyen_emirler"):
                        for emir in cz_canli["bekleyen_emirler"]:
                            emir_html = (
                                f"<div style='background-color:rgba(15, 23, 42, 0.8); border:1px solid rgba(0,255,255,0.2); padding:10px; border-radius:10px; margin-bottom:10px; backdrop-filter:blur(5px);'>"
                                f"<b>{emir['varlik']}</b> | {'🟢 AL' if emir['tip'] == 'AL' else '🔴 SAT'} ({format_tr(emir['adet'])}) | Hedef: <b>{format_tr(emir['hedef_fiyat'])} ₺</b></div>"
                            )
                            st.markdown(emir_html, unsafe_allow_html=True)
                            if st.button("❌ İptal", key=f"iptal_{emir['id']}"):
                                if emir["tip"] == "AL": cz_canli["nakit"] += emir["baglanan_tutar"]
                                else:
                                    mevcut_veri = cz_canli["varliklar"].get(emir["varlik"], {"adet": 0.0, "maliyet": emir.get("maliyet_rezerv", 0.0)})
                                    cz_canli["varliklar"][emir["varlik"]] = {"adet": mevcut_veri["adet"] + emir["adet"], "maliyet": emir.get("maliyet_rezerv", 0.0)}
                                cz_canli["bekleyen_emirler"] = [e for e in cz_canli["bekleyen_emirler"] if e["id"] != emir["id"]]
                                db_kaydet(db_canli); st.rerun()
                    else: st.caption("Bekleyen aktif bir emriniz bulunmuyor.")
                
                except Exception as e:
                    st.error(f"Sistem bir hata tespit etti ve çalışmayı durdurdu. Lütfen sayfayı yenileyin. (Hata: {str(e)})")

            if hasattr(st, "fragment"): canli_portfoy_motoru = st.fragment(run_every=10)(canli_portfoy_motoru)
            canli_portfoy_motoru()

    with tab_banka:
        st.subheader("🏦 Merkez Bankası (Faiz & Mevduat)")
        st.write("Boşta duran nakit paranızı enflasyona karşı koruyun. Anlık olarak faiz kazanmaya başlayın.")
        
        def canli_banka_motoru():
            try:
                db_canli = db_yukle()
                cz_canli = db_canli[aktif_kullanici]["cuzdan"]
                banka_canli = cz_canli.get("banka", {"gecelik": {"miktar": 0.0, "son_guncelleme": time.time()}, "vadeli": []})
                
                st.markdown("<span class='pulsing-dot'></span> <span style='color:#00ffff; font-size:12px; font-weight:bold;'>Faiz Canlı İşliyor</span>", unsafe_allow_html=True)
                
                st.markdown("<div class='banka-kart'>", unsafe_allow_html=True)
                st.markdown("### 🌙 Para Piyasası Fonu (Gecelik Faiz)")
                st.markdown("<span style='color:#00ff00; font-weight:bold;'>Yıllık Getiri: %40 (Saniye bazlı işler, anında çekilebilir)</span>", unsafe_allow_html=True)
                
                col_b1, col_b2 = st.columns(2)
                with col_b1: st.metric("Fonda Biriken Para", f"{format_tr(banka_canli['gecelik']['miktar'], 4)} ₺")
                with col_b2: st.metric("Kullanılabilir Nakit (Cüzdan)", f"{format_tr(cz_canli['nakit'])} ₺")
                    
                c_yatir, c_cek = st.columns(2)
                with c_yatir:
                    yatirilacak = st.number_input("Fona Yatır (₺)", min_value=0.0, step=100.0)
                    if st.button("💸 Fona Aktar", use_container_width=True) and yatirilacak > 0:
                        if cz_canli["nakit"] >= yatirilacak:
                            cz_canli["nakit"] -= yatirilacak
                            banka_canli["gecelik"]["miktar"] += yatirilacak
                            banka_canli["gecelik"]["son_guncelleme"] = time.time()
                            cz_canli["banka"] = banka_canli
                            db_kaydet(db_canli)
                            st.rerun()
                        else:
                            st.error("Yetersiz Nakit Bakiye!")
                with c_cek:
                    cekilecek = st.number_input("Fondaki Parayı Çek (₺)", min_value=0.0, step=100.0)
                    if st.button("🏦 Kasaya Geri Çek", use_container_width=True) and cekilecek > 0:
                        if banka_canli["gecelik"]["miktar"] >= cekilecek:
                            banka_canli["gecelik"]["miktar"] -= cekilecek
                            cz_canli["nakit"] += cekilecek
                            cz_canli["banka"] = banka_canli
                            db_kaydet(db_canli)
                            st.rerun()
                        else:
                            st.error("Fonda bu kadar paranız bulunmuyor!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='banka-kart'>", unsafe_allow_html=True)
                st.markdown("### 📅 Kilitli Vadeli Mevduat")
                st.markdown("Paranızı belirli bir süre kilitlerseniz çok daha yüksek faiz alırsınız. Vade bozulursa faiz yanar!")
                
                with st.form("vadeli_form"):
                    v_miktar = st.number_input("Kilitlenecek Tutar (₺)", min_value=0.0, step=1000.0)
                    v_sure = st.selectbox("Vade Seçimi", ["1 Günlük Kilit (%45 Yıllık)", "7 Günlük Kilit (%52 Yıllık)", "30 Günlük Kilit (%60 Yıllık)"])
                    if st.form_submit_button("🔒 Vadeye Bağla"):
                        if v_miktar > 0:
                            if cz_canli["nakit"] >= v_miktar:
                                gun = 1 if "1 Günlük" in v_sure else (7 if "7 Günlük" in v_sure else 30)
                                oran = 0.45 if gun == 1 else (0.52 if gun == 7 else 0.60)
                                cz_canli["nakit"] -= v_miktar
                                banka_canli["vadeli"].append({"id": str(uuid.uuid4()), "miktar": v_miktar, "gun": gun, "faiz_orani": oran, "baslangic": time.time(), "bitis": time.time() + (gun * 24 * 3600)})
                                cz_canli["banka"] = banka_canli
                                
                                rozet_ver(db_canli, aktif_kullanici, "🏦", "Merkez Bankeri")
                                if gun == 30: rozet_ver(db_canli, aktif_kullanici, "🧊", "Buzul Kasa")
                                    
                                db_kaydet(db_canli)
                                st.success("Tebrikler! Paranız yüksek faizle kilitlendi.")
                                time.sleep(1); st.rerun()
                            else:
                                st.error("Yetersiz Nakit Bakiye!")
                                
                if banka_canli.get("vadeli"):
                    st.markdown("#### 🔓 Aktif Kilitli Mevduatlarınız")
                    for v in banka_canli["vadeli"]:
                        kalan_saniye = v["bitis"] - time.time()
                        kalan_gun = int(kalan_saniye // (24*3600))
                        kalan_saat = int((kalan_saniye % (24*3600)) // 3600)
                        kalan_dk = int((kalan_saniye % 3600) // 60)
                        beklenen_getiri = v["miktar"] * v["faiz_orani"] * (v["gun"] / 365)
                        mevduat_html = (
                            f"<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-bottom:5px; display:flex; justify-content:space-between; align-items:center;'>"
                            f"<div><b>{format_tr(v['miktar'])} ₺</b> ({v['gun']} Günlük)<br><span style='color:#00ff00; font-size:12px;'>Vade Sonu Getirisi: +{format_tr(beklenen_getiri)} ₺</span><br>"
                            f"<span style='color:#aaa; font-size:12px;'>⏳ Kalan Süre: {kalan_gun} Gün, {kalan_saat} Saat, {kalan_dk} Dk</span></div></div>"
                        )
                        st.markdown(mevduat_html, unsafe_allow_html=True)
                        if st.button("❌ Vadeyi Boz (Faiz Yanar)", key=f"boz_{v['id']}"):
                            banka_canli["vadeli"] = [x for x in banka_canli["vadeli"] if x["id"] != v["id"]]
                            cz_canli["nakit"] += v["miktar"] 
                            cz_canli["banka"] = banka_canli
                            db_kaydet(db_canli)
                            st.error("Vade bozuldu. Ana paranız kasaya döndü, faiz hakkınız yandı.")
                            time.sleep(1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception:
                st.error("Banka motoru durduruldu. Sayfayı yenileyin.")

        if hasattr(st, "fragment"): canli_banka_motoru = st.fragment(run_every=2)(canli_banka_motoru)
        canli_banka_motoru()

    with tab_arena:
        st.subheader("⚔️ Borsa Arenası (1v1 Düello)")
        st.write("24 saat sürecek amansız bir PNL (Kâr/Zarar) savaşı! Meydan oku veya katıl, başlangıç anından itibaren en çok kâr yüzdesini sen yap, masadaki tüm ödülü topla!")

        def arena_motoru():
            try:
                db_arena = db_yukle()
                cz_arena = db_arena[aktif_kullanici]["cuzdan"]
                if "_DUELLOLAR_" not in db_arena: db_arena["_DUELLOLAR_"] = {}
                duellolar = db_arena["_DUELLOLAR_"]
                degisiklik_var = False

                def anlik_net_deger_bul(uid, f_sozluk):
                    if uid not in db_arena: return 0.0
                    cuz = db_arena[uid].get("cuzdan", {})
                    toplam = cuz.get("nakit", 0.0)
                    b_veri = cuz.get("banka", {"gecelik": {"miktar": 0.0}, "vadeli": []})
                    toplam += b_veri["gecelik"]["miktar"] + sum([x["miktar"] for x in b_veri["vadeli"]])
                    for be in cuz.get("bekleyen_emirler", []):
                        if be["tip"] == "AL": toplam += be["baglanan_tutar"]
                    for v_isim, v_veri in cuz.get("varliklar", {}).items():
                        adet = v_veri if isinstance(v_veri, (int, float)) else v_veri.get("adet", 0)
                        toplam += adet * f_sozluk.get(v_isim, 0.0)
                    for be in cuz.get("bekleyen_emirler", []):
                        if be["tip"] == "SAT": toplam += be["adet"] * f_sozluk.get(be["varlik"], 0.0)
                    for poz in cuz.get("kaldiracli_islemler", []):
                        g_fiyat = f_sozluk.get(poz["varlik"], poz["giris_fiyati"])
                        pnl = (g_fiyat - poz["giris_fiyati"]) * poz["adet"] if poz["yon"] == "AL (Long)" else (poz["giris_fiyati"] - g_fiyat) * poz["adet"]
                        toplam += max(0, poz["teminat"] + pnl)
                    return toplam

                aktifler = {k: v for k, v in duellolar.items() if v["durum"] == "aktif"}
                if aktifler:
                    for d_id, d in list(aktifler.items()):
                        if time.time() >= d["bitis_zamani"]:
                            ilgili_varliklar = set()
                            for uid in [d["olusturan_id"], d["katilan_id"]]:
                                if uid in db_arena:
                                    for vi in db_arena[uid]["cuzdan"].get("varliklar", {}): ilgili_varliklar.add(vi)
                                    for pi in db_arena[uid]["cuzdan"].get("kaldiracli_islemler", []): ilgili_varliklar.add(pi["varlik"])
                            
                            fiyatlar = {}
                            for vi in ilgili_varliklar:
                                sembol = tum_varliklar_mega.get(vi)
                                if sembol: fiyatlar[vi] = canli_fiyat_getir(sembol, usd_kuru if not sembol.endswith(".IS") else 1.0)
                                
                            net1 = anlik_net_deger_bul(d["olusturan_id"], fiyatlar)
                            net2 = anlik_net_deger_bul(d["katilan_id"], fiyatlar)
                            
                            pnl1 = ((net1 - d["olusturan_baslangic"]) / d["olusturan_baslangic"]) * 100 if d["olusturan_baslangic"] > 0 else 0
                            pnl2 = ((net2 - d["katilan_baslangic"]) / d["katilan_baslangic"]) * 100 if d["katilan_baslangic"] > 0 else 0
                            
                            toplam_odul = d["bahis_miktari"] * 2
                            
                            if pnl1 > pnl2: kazanan = d["olusturan_id"]
                            elif pnl2 > pnl1: kazanan = d["katilan_id"]
                            else: kazanan = "berabere"
                            
                            if kazanan == "berabere":
                                db_arena[d["olusturan_id"]]["cuzdan"]["nakit"] += d["bahis_miktari"]
                                db_arena[d["katilan_id"]]["cuzdan"]["nakit"] += d["bahis_miktari"]
                            else:
                                db_arena[kazanan]["cuzdan"]["nakit"] += toplam_odul
                            
                            for uid in [d["olusturan_id"], d["katilan_id"]]:
                                if uid in db_arena:
                                    db_arena[uid]["istatistikler"].setdefault("duello_karnesi", {"katildigi": 0, "kazandigi": 0})
                                    db_arena[uid]["istatistikler"]["duello_karnesi"]["katildigi"] += 1
                            if kazanan != "berabere" and kazanan in db_arena:
                                db_arena[kazanan]["istatistikler"]["duello_karnesi"]["kazandigi"] += 1
                                
                            d["durum"] = "bitti"
                            d["kazanan_id"] = kazanan
                            degisiklik_var = True
                            
                if degisiklik_var: db_kaydet(db_arena)

                st.markdown("<div class='banka-kart'>", unsafe_allow_html=True)
                st.markdown("### 🥊 Arenaya Çık")
                
                c_tur, c_bahis = st.columns([1, 1])
                with c_tur:
                    meydan_turu = st.radio("Meydan Okuma Tipi:", ["Açık Meydan Okuma (Herkese)", "Özel Düello (Kişiye Özel)"], horizontal=True)
                    hedef_kisi = None
                    if meydan_turu == "Özel Düello (Kişiye Özel)":
                        kullanicilar_liste = {k: v.get("nickname", k) for k, v in db_arena.items() if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"] and k != aktif_kullanici and not v.get("is_admin", False)}
                        if kullanicilar_liste:
                            hedef_kisi = st.selectbox("Meydan Okunacak Oyuncu Seç:", list(kullanicilar_liste.keys()), format_func=lambda x: kullanicilar_liste[x])
                        else:
                            st.warning("Sistemde meydan okunacak başka aktif oyuncu yok.")
                
                with c_bahis:
                    bahis = st.number_input("Ortaya Konacak Tutar (₺)", min_value=100.0, step=1000.0, key="yeni_duello")
                
                buton_metni = f"⚔️ {meydan_turu.split(' ')[0]} İlan Et (Tutar Kasadan Düşer)"
                if st.button(buton_metni, use_container_width=True):
                    if meydan_turu == "Özel Düello (Kişiye Özel)" and not hedef_kisi:
                        st.error("Lütfen bir rakip seçin.")
                    elif cz_arena["nakit"] >= bahis:
                        cz_arena["nakit"] -= bahis
                        db_arena["_DUELLOLAR_"][str(uuid.uuid4())] = {
                            "olusturan_id": aktif_kullanici, "olusturan_nick": aktif_nickname,
                            "bahis_miktari": float(bahis), "durum": "bekliyor",
                            "hedef_id": hedef_kisi, 
                            "olusturan_baslangic": 0.0, "katilan_id": None, "katilan_nick": None,
                            "katilan_baslangic": 0.0, "baslangic_zamani": 0, "bitis_zamani": 0
                        }
                        db_kaydet(db_arena)
                        st.success("Meydan okumanız arenaya asıldı!")
                        time.sleep(1); st.rerun()
                    else: st.error("Kasanda bu kadar nakit yok!")
                st.markdown("</div>", unsafe_allow_html=True)

                c_bekleyen, c_aktif = st.columns(2)
                
                with c_bekleyen:
                    st.markdown("#### ⏳ Rakip Bekleyenler")
                    
                    bekleyenler = {}
                    for k, v in duellolar.items():
                        if v["durum"] == "bekliyor":
                            if v["olusturan_id"] == aktif_kullanici: 
                                bekleyenler[k] = v
                            elif v.get("hedef_id") == aktif_kullanici: 
                                bekleyenler[k] = v
                            elif v.get("hedef_id") is None: 
                                bekleyenler[k] = v
                                
                    if not bekleyenler: st.caption("Şu an senin katılabileceğin bir düello yok.")
                    for d_id, d in bekleyenler.items():
                        
                        if d.get("hedef_id") == aktif_kullanici:
                            etiket = "<span style='background:#ff4444; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>🎯 SANA ÖZEL MEYDAN OKUMA</span>"
                        else:
                            etiket = "<span style='background:#1e293b; color:#aaa; padding:2px 6px; border-radius:4px; font-size:11px;'>📣 Açık Meydan Okuma</span>"
                            
                        bekleyen_html = (
                            f"<div style='background:rgba(15,23,42,0.8); border:1px solid rgba(255,215,0,0.3); padding:10px; border-radius:8px; margin-bottom:5px;'>"
                            f"{etiket}<br><b>{d['olusturan_nick']}</b> seni düelloya davet ediyor!<br>"
                            f"<span style='color:#FFD700;'>Ortadaki Havuz: {format_tr(d['bahis_miktari']*2)} ₺</span></div>"
                        )
                        st.markdown(bekleyen_html, unsafe_allow_html=True)
                        
                        if d["olusturan_id"] == aktif_kullanici:
                            if st.button("❌ Geri Çekil (İptal)", key=f"iptal_{d_id}"):
                                cz_arena["nakit"] += d["bahis_miktari"]
                                del db_arena["_DUELLOLAR_"][d_id]
                                db_kaydet(db_arena)
                                st.rerun()
                        else:
                            if d.get("hedef_id") == aktif_kullanici:
                                c1, c2 = st.columns(2)
                                with c1:
                                    kabul_edildi = st.button("🔥 Kabul Et", key=f"katil_{d_id}", use_container_width=True)
                                with c2:
                                    reddedildi = st.button("👎 Reddet", key=f"reddet_{d_id}", use_container_width=True)
                            else:
                                kabul_edildi = st.button("🔥 Meydan Oku (Kabul Et)", key=f"katil_{d_id}", use_container_width=True)
                                reddedildi = False

                            if reddedildi:
                                if d["olusturan_id"] in db_arena:
                                    db_arena[d["olusturan_id"]]["cuzdan"]["nakit"] += d["bahis_miktari"]
                                del db_arena["_DUELLOLAR_"][d_id]
                                db_kaydet(db_arena)
                                st.warning("Düelloyu reddettiniz.")
                                time.sleep(1)
                                st.rerun()

                            if kabul_edildi:
                                if cz_arena["nakit"] >= d["bahis_miktari"]:
                                    with st.spinner("Savaş Meydanı Kuruluyor..."):
                                        cz_arena["nakit"] -= d["bahis_miktari"]
                                        
                                        ilgili_v = set()
                                        for uid in [d["olusturan_id"], aktif_kullanici]:
                                            if uid in db_arena:
                                                for vi in db_arena[uid]["cuzdan"].get("varliklar", {}): ilgili_v.add(vi)
                                                for pi in db_arena[uid]["cuzdan"].get("kaldiracli_islemler", []): ilgili_v.add(pi["varlik"])
                                        fiy_sozluk = {}
                                        for vi in ilgili_v:
                                            sembol = tum_varliklar_mega.get(vi)
                                            if sembol: fiy_sozluk[vi] = canli_fiyat_getir(sembol, usd_kuru if not sembol.endswith(".IS") else 1.0)
                                        
                                        net_1 = anlik_net_deger_bul(d["olusturan_id"], fiy_sozluk)
                                        net_2 = anlik_net_deger_bul(aktif_kullanici, fiy_sozluk)
                                        
                                        d["durum"] = "aktif"
                                        d["katilan_id"] = aktif_kullanici
                                        d["katilan_nick"] = aktif_nickname
                                        d["olusturan_baslangic"] = net_1
                                        d["katilan_baslangic"] = net_2
                                        d["baslangic_zamani"] = time.time()
                                        d["bitis_zamani"] = time.time() + (24 * 3600)
                                        
                                        db_kaydet(db_arena)
                                        st.success("Düello Başladı! Anlık net varlıklarınız kilitlendi ve her iki taraf da %0 ile savaşa başlıyor.")
                                        time.sleep(1); st.rerun()
                                else: st.error("Giriş ücreti için kasanızda yeterli nakit yok.")

                with c_aktif:
                    st.markdown("#### 📺 Canlı Arena İzleme")
                    aktif_savaslar = {k: v for k, v in duellolar.items() if v["durum"] == "aktif"}
                    
                    if not aktif_savaslar: 
                        st.caption("Şu an arenada devam eden bir savaş yok.")
                    else:
                        ilgili_canli = set()
                        for d_id, d in aktif_savaslar.items():
                            for uid in [d["olusturan_id"], d["katilan_id"]]:
                                if uid in db_arena:
                                    for vi in db_arena[uid]["cuzdan"].get("varliklar", {}): ilgili_canli.add(vi)
                                    for pi in db_arena[uid]["cuzdan"].get("kaldiracli_islemler", []): ilgili_canli.add(pi["varlik"])
                        
                        f_canli = {}
                        for vi in ilgili_canli:
                            sembol = tum_varliklar_mega.get(vi)
                            if sembol: f_canli[vi] = canli_fiyat_getir(sembol, usd_kuru if not sembol.endswith(".IS") else 1.0)
                            
                        savaslar_listesi = list(aktif_savaslar.items())
                        savaslar_listesi.sort(key=lambda x: 0 if (x[1]["olusturan_id"] == aktif_kullanici or x[1]["katilan_id"] == aktif_kullanici) else 1)

                        for d_id, d in savaslar_listesi:
                            net1 = anlik_net_deger_bul(d["olusturan_id"], f_canli)
                            net2 = anlik_net_deger_bul(d["katilan_id"], f_canli)
                            
                            p1 = ((net1 - d["olusturan_baslangic"]) / d["olusturan_baslangic"]) * 100 if d["olusturan_baslangic"] > 0 else 0
                            p2 = ((net2 - d["katilan_baslangic"]) / d["katilan_baslangic"]) * 100 if d["katilan_baslangic"] > 0 else 0
                            
                            k_saniye = d["bitis_zamani"] - time.time()
                            saat = int(k_saniye // 3600)
                            dakika = int((k_saniye % 3600) // 60)
                            
                            r1 = "#00ff00" if p1 >= 0 else "#ff4444"
                            r2 = "#00ff00" if p2 >= 0 else "#ff4444"
                            
                            p1_str = f"+%{format_tr(p1)}" if p1 > 0 else f"%{format_tr(p1)}"
                            p2_str = f"+%{format_tr(p2)}" if p2 > 0 else f"%{format_tr(p2)}"
                            
                            benim_savasim_mi = (d["olusturan_id"] == aktif_kullanici or d["katilan_id"] == aktif_kullanici)
                            
                            if benim_savasim_mi:
                                isim1 = d['olusturan_nick']
                                isim2 = d['katilan_nick']
                                border_style = "border:2px solid #FFD700; box-shadow: 0 0 10px rgba(255,215,0,0.2);"
                                baslik_etiketi = "<div style='text-align:center; font-size:10px; color:#FFD700; margin-bottom:5px; letter-spacing:1px;'>SENİN SAVAŞIN</div>"
                            else:
                                isim1 = d['olusturan_nick'][:2] + "***" if len(d['olusturan_nick']) >= 2 else "G***"
                                isim2 = d['katilan_nick'][:2] + "***" if len(d['katilan_nick']) >= 2 else "G***"
                                border_style = "border:1px solid rgba(255,255,255,0.1); opacity:0.8;"
                                baslik_etiketi = ""

                            html_str_arena = (
                                f"<div style='background:rgba(0,0,0,0.5); {border_style} padding:15px; border-radius:10px; margin-bottom:10px;'>"
                                f"{baslik_etiketi}"
                                f"<div style='text-align:center; color:#FFD700; font-weight:bold; margin-bottom:5px; font-size:18px;'>Masa: {format_tr(d['bahis_miktari']*2)} ₺</div>"
                                f"<div style='display:flex; justify-content:space-between; font-size:16px;'>"
                                f"<div style='text-align:center; width:33%;'><b>{isim1}</b><br><span style='color:{r1}; font-weight:bold;'>{p1_str}</span></div>"
                                f"<div style='color:#aaa; font-size:12px; margin-top:5px; text-align:center; width:33%;'>⏳ Kalan Süre<br><b>{saat}s {dakika}d</b></div>"
                                f"<div style='text-align:center; width:33%;'><b>{isim2}</b><br><span style='color:{r2}; font-weight:bold;'>{p2_str}</span></div>"
                                f"</div></div>"
                            )
                            st.markdown(html_str_arena, unsafe_allow_html=True)
            except Exception as e:
                pass

        if hasattr(st, "fragment"): arena_motoru = st.fragment(run_every=5)(arena_motoru)
        arena_motoru()

    with tab_liderlik:
        st.subheader("🏆 En İyi Fon Yöneticileri")
        st.write("Sistemdeki tüm yatırımcıların başarımları ve portföy büyüklükleri.")
        
        def liderlik_tablosunu_ciz():
            try:
                db_canli = db_yukle()
                tum_kullanici_varliklari = set()
                for k, v in db_canli.items():
                    if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"] and not v.get("is_admin", False) and "cuzdan" in v:
                        for varlik_ismi in v["cuzdan"].get("varliklar", {}): tum_kullanici_varliklari.add(varlik_ismi)
                        for poz in v["cuzdan"].get("kaldiracli_islemler", []): tum_kullanici_varliklari.add(poz["varlik"])
                
                liderlik_fiyatlar = {}
                for varlik_ismi in tum_kullanici_varliklari:
                    sembol = tum_varliklar_mega.get(varlik_ismi)
                    if sembol:
                        kat = usd_kuru if not sembol.endswith(".IS") else 1.0
                        liderlik_fiyatlar[varlik_ismi] = canli_fiyat_getir(sembol, kat)
                
                liderlik_listesi = []
                for k, v in db_canli.items():
                    if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"] and not v.get("is_admin", False) and "cuzdan" in v:
                        
                        if time.time() - v.get("kayit_tarihi", time.time()) > 86400:
                            rozet_ver(db_canli, k, "⏳", "Kıdemli Kurt")
                        if time.time() - v.get("kayit_tarihi", time.time()) > 7 * 86400:
                            rozet_ver(db_canli, k, "🛡️", "Demir İrade")
                        
                        kullanici_cuzdan = v["cuzdan"]
                        kullanici_toplam = kullanici_cuzdan.get("nakit", 1000000.0)
                        b_veri = kullanici_cuzdan.get("banka", {"gecelik": {"miktar": 0.0}, "vadeli": []})
                        kullanici_toplam += b_veri["gecelik"]["miktar"] + sum([x["miktar"] for x in b_veri["vadeli"]])
                        for be in kullanici_cuzdan.get("bekleyen_emirler", []):
                            if be["tip"] == "AL": kullanici_toplam += be["baglanan_tutar"]
                        if "varliklar" in kullanici_cuzdan:
                            for v_isim, v_veri in kullanici_cuzdan["varliklar"].items():
                                adet = v_veri if isinstance(v_veri, (int, float)) else v_veri.get("adet", 0)
                                kullanici_toplam += adet * liderlik_fiyatlar.get(v_isim, 0.0)
                        for be in kullanici_cuzdan.get("bekleyen_emirler", []):
                            if be["tip"] == "SAT": kullanici_toplam += be["adet"] * liderlik_fiyatlar.get(be["varlik"], 0.0)
                        for poz in kullanici_cuzdan.get("kaldiracli_islemler", []):
                            guncel_p_fiyat = liderlik_fiyatlar.get(poz["varlik"], poz["giris_fiyati"])
                            pnl = (guncel_p_fiyat - poz["giris_fiyati"]) * poz["adet"] if poz["yon"] == "AL (Long)" else (poz["giris_fiyati"] - guncel_p_fiyat) * poz["adet"]
                            kullanici_toplam += max(0, poz["teminat"] + pnl)
                            
                        if kullanici_toplam >= 2000000:
                            rozet_ver(db_canli, k, "👑", "Oligark")
                                
                        gosterilecek_isim = v.get("nickname", k)
                        rozet_str = "".join(v.get("rozetler", []))
                        isim_ve_rozet = f"{gosterilecek_isim} {rozet_str}"
                        
                        # YENİ EKLENEN: Gizli Kullanıcı ID'sini listede tutuyoruz (Tıklama için gerekli)
                        liderlik_listesi.append({"id": k, "Kullanici": isim_ve_rozet, "Toplam": kullanici_toplam})
                
                liderlik_listesi = sorted(liderlik_listesi, key=lambda x: x["Toplam"], reverse=True)
                
                gosterim_listesi = []
                for i, user_data in enumerate(liderlik_listesi):
                    int_str = format_tr(user_data["Toplam"]).split(",")[0]
                    maskeli_bakiye = int_str[0] + "".join(["*" if c.isdigit() else c for c in int_str[1:]]) + " ₺"
                    sira = "🥇 1" if i == 0 else "🥈 2" if i == 1 else "🥉 3" if i == 2 else str(i + 1)
                    
                    gosterim_listesi.append({
                        "Sıra": sira, 
                        "Yatırımcı & Başarımlar": user_data["Kullanici"], 
                        "Gizli Kasa Büyüklüğü": maskeli_bakiye
                    })
                    
                # YENİ EKLENEN: Liderlik Tablosunun Tıklanabilir (Seçilebilir) Hale Getirilmesi
                st.caption("🔍 Profili detaylı incelemek için tablodan bir oyuncunun üzerine tıklayabilirsiniz.")
                
                df_gosterim = pd.DataFrame(gosterim_listesi)
                try:
                    # Yeni Streamlit sürümlerinde satır seçmeyi açıyoruz
                    secim_event = st.dataframe(
                        df_gosterim,
                        hide_index=True,
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    # Eğer bir satıra tıklandıysa, o satırdaki oyuncunun profilini aç
                    if hasattr(secim_event, 'selection') and len(secim_event.selection.rows) > 0:
                        secilen_index = secim_event.selection.rows[0]
                        secilen_oyuncu_id = liderlik_listesi[secilen_index]["id"]
                        secilen_oyuncu_nick = liderlik_listesi[secilen_index]["Kullanici"]
                        profil_goster(secilen_oyuncu_id, secilen_oyuncu_nick, db_canli[secilen_oyuncu_id])
                        
                except TypeError:
                    # Eski bir Streamlit sürümü kullanılıyorsa hata vermemesi için güvenli zırh
                    st.dataframe(df_gosterim.style.hide(axis="index"), use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("💡 Başarım Rozetleri Ne Anlama Geliyor?"):
                    for emoji, aciklama in ROZET_ANLAMLARI.items():
                        st.write(f"**{emoji}** {aciklama}")
                        
            except Exception:
                pass
            
        if hasattr(st, "fragment"): liderlik_tablosunu_ciz = st.fragment(run_every=30)(liderlik_tablosunu_ciz)
        liderlik_tablosunu_ciz()
        
        # Casusluk yazısı temizlendi.
        st.markdown("---")
        st.subheader("🕵️ Oyuncu Profillerini İncele")
        st.write("Rakiplerinin en çok oynadığı hisseleri ve düello başarılarını incele.")
        
        db_guncel = db_yukle()
        kullanicilar_liste = {k: v.get("nickname", k) for k, v in db_guncel.items() if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"] and not v.get("is_admin", False)}
        
        c_secim, c_buton = st.columns([3, 1])
        with c_secim:
            secilen_profil_id = st.selectbox("İncelemek istediğiniz oyuncuyu seçin:", list(kullanicilar_liste.keys()), format_func=lambda x: kullanicilar_liste[x], label_visibility="collapsed")
        with c_buton:
            if st.button("🔍 Profili Görüntüle", use_container_width=True) and secilen_profil_id:
                profil_goster(secilen_profil_id, kullanicilar_liste[secilen_profil_id], db_guncel[secilen_profil_id])

    with tab_sohbet:
        st.subheader("💬 Borsa Meydanı")
        st.write("Diğer fon yöneticileriyle piyasa dedikodularını ve stratejilerinizi paylaşın.")
        
        def sohbet_kutusunu_ciz():
            db_anlik = db_yukle() 
            mesajlar = db_anlik["_GLOBAL_"].get("sohbet", [])
            chat_container = st.container(height=450)
            
            with chat_container:
                if not mesajlar:
                    st.caption("Burası çok sessiz... İlk mesajı sen gönder!")
                else:
                    for msg in mesajlar:
                        zaman_str = pd.to_datetime(msg["time"], unit="s").tz_localize("UTC").tz_convert("Europe/Istanbul").strftime("%H:%M")
                        if msg["user"] == "👑 SİSTEM YÖNETİCİSİ":
                            st.markdown(f"<div class='sohbet-mesaji admin'><b><span style='color:#FFD700'>{msg['user']}</span></b> <span style='font-size:11px; color:#aaa;'>🕒 {zaman_str}</span><br><span style='color:#FFD700'>{msg['text']}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='sohbet-mesaji'><b><span style='color:#00ffff'>{msg['user']}</span></b> <span style='font-size:11px; color:#aaa;'>🕒 {zaman_str}</span><br>{msg['text']}</div>", unsafe_allow_html=True)

        if hasattr(st, "fragment"): sohbet_kutusunu_ciz = st.fragment(run_every=2)(sohbet_kutusunu_ciz)
        else:
            if HAS_AUTOREFRESH: st_autorefresh(interval=2000, key="sohbet_yenile")
        sohbet_kutusunu_ciz()

        yeni_mesaj = st.chat_input("Piyasa hakkında bir şeyler yaz...")
        if yeni_mesaj:
            db_guncel = db_yukle() 
            db_guncel["_GLOBAL_"]["sohbet"].append({"user": aktif_nickname, "text": yeni_mesaj[:250], "time": time.time()})
            db_guncel["_GLOBAL_"]["sohbet"] = db_guncel["_GLOBAL_"]["sohbet"][-50:]
            db_kaydet(db_guncel)
            st.rerun()
