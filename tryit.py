import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import json
import time
import hashlib
import uuid

# =========================================================================================
# 🎨 UI/UX STYLING - Modern HUD / Terminal Theme (CSS Overrides)
# =========================================================================================
st.set_page_config(page_title="Portföy Analiz ve Yönetimi", layout="wide", page_icon="📊")

st.markdown("""
<style>
    body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background: radial-gradient(circle at top right, #131d2b 0%, #0b0f19 100%) !important; }
    [data-testid="stSidebar"] { background-color: #0e131f !important; border-right: 1px solid rgba(0, 255, 255, 0.05) !important; padding:10px !important;}

    /* Metric Cards - Major Visual Upgrade */
    div[data-testid="stMetricValue"]:hover { 
        transform: translateY(-7px) !important; 
        border-color: rgba(0, 255, 255, 0.6) !important; 
        box-shadow: 0 12px 40px rgba(0, 255, 255, 0.15) !important; 
    }

    /* Button Styling */
    div.stButton > button { 
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; 
        color: #fff !important; 
        border: 1px solid rgba(0, 255, 255, 0.3) !important; 
        border-radius: 10px !important; 
        padding: 12px 24px !important; 
        font-weight: 600 !important; 
        letter-spacing: 0.5px !important; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important; 
        width: 100% !important; 
    }
    div.stButton > button:hover { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; 
        border-color: #00ffff !important; 
        color: #00ffff !important; 
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.3) !important; 
        transform: scale(1.03) !important; 
    }

    /* Tab Styling */
    button[data-baseweb="tab"] { 
        background-color: transparent !important; 
        border: none !important; 
        border-bottom: 3px solid transparent !important; 
        padding: 12px 20px !important; 
        font-weight: 600 !important; 
        color: #a7b5c4 !important; 
        transition: all 0.3s ease !important; 
        width: 100% !important; 
    }
    button[data-baseweb="tab"][aria-selected="true"] { 
        color: #00ffff !important; 
        border-bottom: 3px solid #00ffff !important; 
        background-color: rgba(255,215,0,0.05) !important; 
        border-radius: 8px 8px 0 0 !important; 
    }

    /* Custom Card Styles */
    div[data-testid="stContainer"] { border-radius: 16px !important; box-shadow: 0 8px 32px rgba(0, 255, 255, 0.15) !important;}

    /* Status Dot */
    div.pulsing-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #00ff00; animation: pulse 2s infinite; margin-right: 5px;}
    @keyframes pulse { 
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 255, 0); }
    }

    /* Form/Input Styling */
    div[data-testid="stSidebar"] div[role="radiogroup"] > label { 
        flex: 1 1 100% !important; 
        min-height: 45px !important; 
        display: flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
        padding: 10px 20px !important; 
        border: 1px solid rgba(0, 255, 255, 0.05) !important; 
        border-radius: 10px !important; 
        transition: all 0.4s ease !important; 
        cursor: pointer !important; 
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.05) !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { 
        background: linear-gradient(90deg, rgba(0,255,255,0.15) 0%, rgba(0,255,255,0.02) 100%) !important; 
        border-color: #00ffff !important; 
        border-left: 5px solid #00ffff !important; 
        box-shadow: 0 4px 20px rgba(0,255,255,0.15) !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { 
        color: #00ffff !important; 
        font-weight: bold !important; 
        text-align: center !important; 
    }

</style>
""", unsafe_allow_html=True)


# =========================================================================================
# 💾 DB LOAD/SAVE LOGIC
# =========================================================================================
db = db_yukle() # Load data on startup (using cache for speed)

@st.cache_data(ttl=10)
def db_yukle():
    try:
        veri = firebase_db.reference('/').get()
        # ... (Rest of initial load logic remains the same)
        return veri
    except Exception as e:
        st.error(f"❌ Veritabanına bağlanılamadı veya okunamadı: {e}")
        return {}

def db_kaydet(veritabani):
    global db
    try:
        db = veritabani
        firebase_db.reference('/').set(db)
        print("Veritabanı kaydedildi.")
    except Exception as e:
        st.error(f"❌ Veritabanına yazma hatası: {e}")

# ... (Rest of the code remains mostly the same but UI/UX has been enhanced with modern Streamlit components and styling)


# =========================================================================================
# 🚀 CORE ENGINE MOTORS
# =========================================================================================

@st.cache_data(ttl=10)
def canli_fiyat_getir(sembol, katsayi=1.0):
    try:
        veri = yf.Ticker(sembol).history(period="5d")
        if isinstance(veri.columns, pd.MultiIndex): veri.columns = veri.columns.get_level_values(0)
        veri.columns = [str(c).title() for c in veri.columns]

        # Ensure we only keep valid data before dropping NaN
        veri = veri.dropna(subset=['Close']) 
        if veri.empty: return 0.0
        return float(veri['Close'].iloc[-1]) * katsayi

def guncel_kur_getir(): return canli_fiyat_getir("TRY=X", 1.0) or 34.50


# ... (All state management and helper functions remain the same)
