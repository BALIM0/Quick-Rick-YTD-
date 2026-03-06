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

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Pro-Yatırım Terminali", layout="wide", page_icon="📈")

st.markdown("""
<style>
    div[data-testid="metric-container"] {background-color: #1e1e1e; border: 1px solid #333; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0, 255, 255, 0.05); transition: transform 0.3s;}
    div[data-testid="metric-container"]:hover {transform: translateY(-5px); box-shadow: 0 6px 15px rgba(0, 255, 255, 0.15);}
    div.stButton > button {border-radius: 8px; font-weight: bold; transition: all 0.3s ease;}
    div.stButton > button:hover {border-color: #00ffff; box-shadow: 0 0 10px rgba(0,255,255,0.3); color: #00ffff;}
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
            return json.load(f)
    return {}

def db_kaydet(db):
    with open(DB_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

if 'aktif_kullanici' not in st.session_state:
    st.session_state.aktif_kullanici = None

db = db_yukle()

# GİRİŞ EKRANI (Enter Tuşu Duyarlı)
if st.session_state.aktif_kullanici is None:
    st.title("🛡️ Pro-Yatırım Kulübüne Hoş Geldiniz")
    st.markdown("Sanal 1.000.000 TL bakiye ile kendi fonunuzu yönetmek ve yapay zeka analizlerine ulaşmak için giriş yapın.")
    tab_giris, tab_kayit = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    
    with tab_giris:
        # Form mantığı ile Enter tuşunu aktifleştirdik
        with st.form("giris_formu"):
            g_kullanici = st.text_input("Kullanıcı Adı")
            g_sifre = st.text_input("Şifre", type="password")
            giris_buton = st.form_submit_button("Giriş Yap", use_container_width=True)
            
        if giris_buton:
            if g_kullanici in db and db[g_kullanici]["sifre"] == sifre_sifrele(g_sifre):
                st.session_state.aktif_kullanici = g_kullanici
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
                
    with tab_kayit:
        with st.form("kayit_formu"):
            k_kullanici = st.text_input("Yeni Kullanıcı Adı")
            k_sifre = st.text_input("Yeni Şifre", type="password")
            kayit_buton = st.form_submit_button("Hesap Oluştur", use_container_width=True)
            
        if kayit_buton:
            if k_kullanici in db:
                st.error("Bu kullanıcı adı zaten alınmış!")
            elif len(k_kullanici) < 3 or len(k_sifre) < 4:
                st.warning("Kullanıcı adı en az 3, şifre en az 4 karakter olmalıdır.")
            else:
                db[k_kullanici] = {"sifre": sifre_sifrele(k_sifre), "cuzdan": {"nakit": 1000000.0, "varliklar": {}, "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)"]}}
                db_kaydet(db)
                st.success("Hesabınız oluşturuldu! Şimdi giriş yapabilirsiniz.")
    st.stop()

aktif_kullanici = st.session_state.aktif_kullanici
cuzdan = db[aktif_kullanici]["cuzdan"]

def aktif_cuzdan_kaydet():
    db[aktif_kullanici]["cuzdan"] = cuzdan
    db_kaydet(db)

st.title("🛡️ Profesyonel Algoritmik Yatırım Karargahı")
st.caption(f"👤 Fon Yöneticisi: **{aktif_kullanici.upper()}** | 💵 Güncel Kur (USD/TRY): **{guncel_kur_getir():.2f} ₺**")

bist_30 = {"Akbank": "AKBNK.IS", "Alarko": "ALARK.IS", "Aselsan": "ASELS.IS", "Astor": "ASTOR.IS", "BİM": "BIMAS.IS", "Borusan": "BRSAN.IS", "Coca Cola": "CCOLA.IS", "Emlak Konut": "EKGYO.IS", "Enka": "ENKAI.IS", "Ereğli": "EREGL.IS", "Ford": "FROTO.IS", "Garanti": "GARAN.IS", "Gübre Fab": "GUBRF.IS", "Hektaş": "HEKTS.IS", "İş Bankası": "ISCTR.IS", "Koç Hol": "KCHOL.IS", "Kontrolmatik": "KONTR.IS", "Koza Altın": "KOZAL.IS", "Kardemir": "KRDMD.IS", "Odaş": "ODAS.IS", "Petkim": "PETKM.IS", "Pegasus": "PGSUS.IS", "Sabancı Hol": "SAHOL.IS", "Sasa": "SASA.IS", "Şişecam": "SISE.IS", "Turkcell": "TCELL.IS", "THY": "THYAO.IS", "Tofaş": "TOASO.IS", "Tüpraş": "TUPRS.IS", "Yapı Kredi": "YKBNK.IS"}
bist_100 = {**bist_30, **{"Alfa Solar": "ALFAS.IS", "Arçelik": "ARCLK.IS", "Brisa": "BRISA.IS", "Çimsa": "CIMSA.IS", "CW Enerji": "CWENE.IS", "Doğuş Oto": "DOAS.IS", "Doğan Hol": "DOHOL.IS", "Eczacıbaşı": "ECILC.IS", "Ege Endüstri": "EGEEN.IS", "Enerjisa": "ENJSA.IS", "Europower": "EUPWR.IS", "Girişim Elk": "GESAN.IS", "Halkbank": "HALKB.IS", "İskenderun D.": "ISDMR.IS", "İş GYO": "ISGYO.IS", "İş Yatırım": "ISMEN.IS", "Konya Çimento": "KONYA.IS", "Kordsa": "KORDS.IS", "Koza Anadolu": "KOZAA.IS", "Mavi": "MAVI.IS", "Migros": "MGROS.IS", "Mia Teknoloji": "MIATK.IS", "Otokar": "OTKAR.IS", "Oyak Çimento": "OYAKC.IS", "Qua Granite": "QUAGR.IS", "Şekerbank": "SKBNK.IS", "Smart Güneş": "SMRTG.IS", "Şok Market": "SOKM.IS", "TAV": "TAVHL.IS", "Tekfen": "TKFEN.IS", "TSKB": "TSKB.IS", "Türk Telekom": "TTKOM.IS", "Türk Traktör": "TTRAK.IS", "Tukaş": "TUKAS.IS", "Ülker": "ULKER.IS", "Vakıfbank": "VAKBN.IS", "Vestel Beyaz": "VESBE.IS", "Vestel": "VESTL.IS", "Yeo Teknoloji": "YEOTK.IS", "Zorlu Enerji": "ZOREN.IS"}}
bist_genis = {**bist_100, **{"Agrotech": "AGROT.IS", "Akfen Yenilenebilir": "AKFYE.IS", "Anadolu Efes": "AEFES.IS", "Anadolu Sigorta": "ANSGR.IS", "Aygaz": "AYGAZ.IS", "Bera Holding": "BERA.IS", "Bien Seramik": "BIENY.IS", "Biotrend": "BIOEN.IS", "Borusan Yatırım": "BRYAT.IS", "Bülbüloğlu Vinç": "BVSAN.IS", "Can Termik": "CANTE.IS", "Çan2 Termik": "CANTE.IS", "CVK Maden": "CVKMD.IS", "Eksun Gıda": "EKSUN.IS", "Esenboğa Elektrik": "ESEN.IS", "Forte Bilgi": "FORTE.IS", "Galata Wind": "GWIND.IS", "GSD Holding": "GSDHO.IS", "Hat-San Gemi": "HATSN.IS", "İmaş Makina": "IMASM.IS", "İnfo Yatırım": "INFO.IS", "İzdemir Enerji": "IZENR.IS", "Kaleseramik": "KLSER.IS", "Kayseri Şeker": "KAYSE.IS", "Kocaer Çelik": "KCAER.IS", "Kuştur Kuşadası": "KSTUR.IS", "Margün Enerji": "MAGEN.IS", "Mercan Kimya": "MERCN.IS", "Naten": "NATEN.IS", "Oyak Yatırım": "OYYAT.IS", "Özsu Balık": "OZSUB.IS", "Penta": "PENTA.IS", "Reeder Teknoloji": "REEDR.IS", "Rubenis Tekstil": "RUBNS.IS", "SDT Uzay": "SDTTR.IS", "Tarkim": "TARKM.IS", "Tatlıpınar Enerji": "TATEN.IS", "Tezol": "TEZOL.IS", "VBT Yazılım": "VBTYZ.IS", "Ziraat GYO": "ZRGYO.IS"}}
kripto = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Binance Coin": "BNB-USD", "Ripple (XRP)": "XRP-USD", "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Dogecoin": "DOGE-USD", "Chainlink": "LINK-USD", "Polkadot": "DOT-USD", "Polygon": "MATIC-USD", "Shiba Inu": "SHIB-USD"}
madenler_emtia = {"Altın (Ons)": "GC=F", "Gümüş (Ons)": "SI=F", "Bakır": "HG=F", "Platin": "PL=F", "Paladyum": "PA=F", "Alüminyum": "ALI=F", "Ham Petrol (WTI)": "CL=F", "Brent Petrol": "BZ=F", "Doğal Gaz": "NG=F", "Isıtma Yakıtı": "HO=F", "Buğday": "ZW=F", "Mısır": "ZC=F", "Soya Fasulyesi": "ZS=F", "Kahve": "KC=F", "Şeker": "SB=F", "Pamuk": "CT=F", "Kakao": "CC=F"}

tum_varliklar_mega = {**bist_genis, **kripto, **madenler_emtia}

st.sidebar.header("🕹️ Uygulama Modu")
uygulama_modu = st.sidebar.radio("Mod Seçiniz:", ["🔍 Algoritmik Piyasa Tarama", "💼 Sanal Portföy (Oyun)"])
st.sidebar.markdown("---")

if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.aktif_kullanici = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.warning("**⚠️ YASAL UYARI (YTD)**\nBurada yer alan yatırım bilgi, yorum ve yapay zeka tahminleri yatırım danışmanlığı kapsamında değildir. Sistem tarafından üretilen sinyaller kesin getiri vaat etmez.")

usd_kuru = guncel_kur_getir()

if uygulama_modu == "🔍 Algoritmik Piyasa Tarama":
    st.sidebar.header("⚙️ Tarama Ayarları")
    vade_secimi = st.sidebar.radio("1. Yatırım Vadesi:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"])
    piyasa_secimi = st.sidebar.radio("2. İncelenecek Piyasa:", ["🇹🇷 BIST 30 (En Büyükler)", "🇹🇷 BIST 100", "🇹🇷 BIST Tüm (Genişletilmiş)", "🪙 Kripto Paralar", "⛏️ Tüm Emtia ve Madenler", "👤 Kendi İzleme Listem"])

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
    elif piyasa_secimi == "🪙 Kripto Paralar": aktif_varliklar = kripto
    else: aktif_varliklar = madenler_emtia

    if 'df_sonuc' not in st.session_state: st.session_state.df_sonuc = pd.DataFrame()
    if 'ozel_portfoy_verisi' not in st.session_state: st.session_state.ozel_portfoy_verisi = pd.DataFrame()

    if st.button("🚀 Algoritmayı Çalıştır"):
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
                    if veri.empty or len(veri) < 20: continue
                    
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
                        pozitif_mf = pd.Series(np.where(tipik_fiyat > tipik_fiyat.shift(1), para_akisi, 0)).rolling(14).sum()
                        negatif_mf = pd.Series(np.where(tipik_fiyat < tipik_fiyat.shift(1), para_akisi, 0)).rolling(14).sum()
                        mfi = 100 - (100 / (1 + (pozitif_mf / negatif_mf)))
                        son_mfi = float(mfi.iloc[-1])
                        
                        delta = veri['Close'].diff()
                        rsi = 100 - (100 / (1 + ((delta.where(delta > 0, 0)).rolling(14).mean() / (-delta.where(delta < 0, 0)).rolling(14).mean())))
                        son_rsi = float(rsi.iloc[-1])
                        
                        macd = veri['Close'].ewm(span=12, adjust=False).mean() - veri['Close'].ewm(span=26, adjust=False).mean()
                        macd_sinyal = macd.ewm(span=9, adjust=False).mean()
                        
                        sma_20 = veri['Close'].rolling(20).mean()
                        son_alt_bant = float(sma_20.iloc[-1] - (veri['Close'].rolling(20).std().iloc[-1] * 2))
                        if not sembol.endswith(".IS"): son_alt_bant *= usd_kuru

                        if son_mfi < 20: puan += 3; durum_notu.append("Hacim: Para Girişi")
                        elif son_mfi > 80: puan -= 2; durum_notu.append("Hacim: Para Çıkışı")
                        if son_rsi < 30: puan += 2; durum_notu.append("RSI: Dipte")
                        if float(macd.iloc[-1]) > float(macd_sinyal.iloc[-1]): puan += 1; durum_notu.append("MACD: Pozitif")
                        if son_fiyat < son_alt_bant: puan += 2; durum_notu.append("BB: Aşırı Düştü")
                            
                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": round(son_fiyat, 2), "RSI": round(son_rsi, 1), "MFI (Hacim)": round(son_mfi, 1), "Puan": puan, "Durum": " | ".join(durum_notu)})

                    else:
                        sma_50 = veri['Close'].rolling(50).mean()
                        sma_200 = veri['Close'].rolling(200).mean()
                        if len(veri) < 200 or pd.isna(sma_200.iloc[-1]): continue
                        
                        sma_200_deger = float(sma_200.iloc[-1])
                        if not sembol.endswith(".IS"): sma_200_deger *= usd_kuru
                            
                        fk_orani = ticker.info.get('trailingPE', None)
                        if son_fiyat > sma_200_deger: puan += 3; durum_notu.append("Boğa Piyasası")
                        else: puan -= 2; durum_notu.append("Ayı Piyasası")
                        if float(sma_50.iloc[-1]) > float(sma_200.iloc[-1]): puan += 2; durum_notu.append("Altın Kesişim")
                        else: puan -= 1; durum_notu.append("Ölüm Kesişimi")
                        
                        fk_metni = "N/A"
                        if fk_orani and isinstance(fk_orani, (int, float)):
                            fk_metni = str(round(fk_orani, 2)); puan += 2 if fk_orani < 15 else -2 if fk_orani > 30 else 0
                            if fk_orani < 15: durum_notu.append("F/K Ucuz")

                        sonuclar.append({"Varlık": isim, "Fiyat (₺)": round(son_fiyat, 2), "200G Ort (₺)": round(sma_200_deger, 2), "F/K": fk_metni, "Puan": puan, "Durum": " | ".join(durum_notu)})
                except: pass 
                finally:
                    islenen += 1
                    ilerleme_cubugu.progress(min(islenen / toplam_varlik, 1.0))
            durum_metni.empty() 
            ilerleme_cubugu.empty() 
            
            if sonuclar:
                st.session_state.df_sonuc = pd.DataFrame(sonuclar).sort_values(by="Puan", ascending=False).reset_index(drop=True)
                st.session_state.ozel_portfoy_verisi = pd.DataFrame(portfoy_fiyat_gecmisi) if piyasa_secimi == "👤 Kendi İzleme Listem" and len(portfoy_fiyat_gecmisi) > 1 else pd.DataFrame()
            else: st.error("Geçerli veri bulunamadı.")
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
                    tab1, tab2 = st.tabs(["🤖 AI Trend", "⏪ Backtest"])
                    with tab1:
                        df_ml = grafik_veri[['Close']].dropna().copy()
                        df_ml['Gunler'] = np.arange(len(df_ml))
                        model = LinearRegression().fit(df_ml[['Gunler']], df_ml['Close'])
                        y_tahmin = model.predict(np.array([[len(df_ml) + i] for i in range(1, 16)]))
                        gelecek_tarihler = [df_ml.index[-1] + pd.Timedelta(days=i) for i in range(1, 16)]
                        fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
                        fig1.add_trace(go.Candlestick(x=grafik_veri.index, open=grafik_veri['Open'], high=grafik_veri['High'], low=grafik_veri['Low'], close=grafik_veri['Close'], name='Fiyat'), row=1, col=1)
                        fig1.add_trace(go.Scatter(x=gelecek_tarihler, y=y_tahmin, mode='lines', name='AI Rotası', line=dict(color='cyan', width=4, dash='dot')), row=1, col=1)
                        fig1.add_trace(go.Bar(x=grafik_veri.index, y=grafik_veri['Volume'], marker_color=['green' if c >= o else 'red' for o, c in zip(grafik_veri['Open'], grafik_veri['Close'])]), row=2, col=1)
                        fig1.update_layout(xaxis_rangeslider_visible=False, height=500, template="plotly_dark", margin=dict(t=10, b=10))
                        st.plotly_chart(fig1, use_container_width=True)
                    with tab2:
                        df_bt = grafik_veri[['Close']].copy()
                        delta_bt = df_bt['Close'].diff()
                        df_bt['RSI'] = 100 - (100 / (1 + ((delta_bt.where(delta_bt > 0, 0)).rolling(14).mean() / (-delta_bt.where(delta_bt < 0, 0)).rolling(14).mean())))
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
        islem_tipi = st.radio("İşlem Yönü:", ["AL", "SAT"], horizontal=True)
        secili_varlik = st.selectbox("Varlık Seçin:", list(tum_varliklar_mega.keys()))
        sembol_islem = tum_varliklar_mega[secili_varlik]
        
        try:
            anlik_fiyat = float(yf.Ticker(sembol_islem).history(period="1d")['Close'].iloc[-1])
            if not sembol_islem.endswith(".IS"): anlik_fiyat *= usd_kuru
            st.write(f"Birim Fiyat: **{anlik_fiyat:,.2f} ₺**")
        except:
            anlik_fiyat = 0
            st.warning("Fiyat çekilemedi.")

        islem_miktari = st.number_input("Adet / Miktar:", min_value=0.01, step=1.0)
        islem_tutari = islem_miktari * anlik_fiyat
        st.write(f"Tutar: **{islem_tutari:,.2f} ₺**")

        if st.button(f"Onayla ({islem_tipi})", use_container_width=True) and anlik_fiyat > 0:
            if islem_tipi == "AL":
                if cuzdan["nakit"] >= islem_tutari:
                    cuzdan["nakit"] -= islem_tutari
                    mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                    yeni_adet = mevcut_veri["adet"] + islem_miktari
                    yeni_maliyet = ((mevcut_veri["adet"] * mevcut_veri["maliyet"]) + islem_tutari) / yeni_adet
                    cuzdan["varliklar"][secili_varlik] = {"adet": yeni_adet, "maliyet": yeni_maliyet}
                    aktif_cuzdan_kaydet()
                    st.success("Başarılı!")
                    time.sleep(1); st.rerun() 
                else: st.error("Yetersiz bakiye!")
            elif islem_tipi == "SAT":
                mevcut_veri = cuzdan["varliklar"].get(secili_varlik, {"adet": 0.0, "maliyet": 0.0})
                if mevcut_veri["adet"] >= islem_miktari:
                    yeni_adet = mevcut_veri["adet"] - islem_miktari
                    cuzdan["nakit"] += islem_tutari
                    if yeni_adet <= 0.000001: del cuzdan["varliklar"][secili_varlik]
                    else: cuzdan["varliklar"][secili_varlik]["adet"] = yeni_adet
                    aktif_cuzdan_kaydet()
                    st.success("Başarılı!")
                    time.sleep(1); st.rerun() 
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
            if st.button("🗑️ Sıfırla"): cuzdan["nakit"], cuzdan["varliklar"] = 1000000.0, {}; aktif_cuzdan_kaydet(); st.rerun()
        else: st.info("Cüzdan boş.")
