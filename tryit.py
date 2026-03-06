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

# --- SAYFA AYARLARI VE ÖZEL NEON CSS ---
st.set_page_config(page_title="Pro-Yatırım Terminali", layout="wide", page_icon="📈")

# Görsel Makyaj (Özel Tasarım CSS)
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0, 255, 255, 0.05);
        transition: transform 0.3s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 15px rgba(0, 255, 255, 0.15);
    }
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        border-color: #00ffff;
        box-shadow: 0 0 10px rgba(0,255,255,0.3);
        color: #00ffff;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Profesyonel Algoritmik Yatırım Karargahı")

# --- VERİTABANI (JSON) FONKSİYONLARI ---
DOSYA_ADI = "sanal_cuzdan.json"

def cuzdan_yukle():
    if os.path.exists(DOSYA_ADI):
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            if "izleme_listesi" not in veri:
                veri["izleme_listesi"] = ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)"]
            return veri
    return {"nakit": 1000000.0, "varliklar": {}, "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)"]}

def cuzdan_kaydet(veri):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4)

cuzdan = cuzdan_yukle()

# =========================================================================================
# --- MEGA PİYASA SÖZLÜKLERİ ---
# =========================================================================================
bist_30 = {
    "Akbank": "AKBNK.IS", "Alarko": "ALARK.IS", "Aselsan": "ASELS.IS", "Astor": "ASTOR.IS", 
    "BİM": "BIMAS.IS", "Borusan": "BRSAN.IS", "Coca Cola": "CCOLA.IS", "Emlak Konut": "EKGYO.IS", 
    "Enka": "ENKAI.IS", "Ereğli": "EREGL.IS", "Ford": "FROTO.IS", "Garanti": "GARAN.IS", 
    "Gübre Fab": "GUBRF.IS", "Hektaş": "HEKTS.IS", "İş Bankası": "ISCTR.IS", "Koç Hol": "KCHOL.IS", 
    "Kontrolmatik": "KONTR.IS", "Koza Altın": "KOZAL.IS", "Kardemir": "KRDMD.IS", "Odaş": "ODAS.IS", 
    "Petkim": "PETKM.IS", "Pegasus": "PGSUS.IS", "Sabancı Hol": "SAHOL.IS", "Sasa": "SASA.IS", 
    "Şişecam": "SISE.IS", "Turkcell": "TCELL.IS", "THY": "THYAO.IS", "Tofaş": "TOASO.IS", 
    "Tüpraş": "TUPRS.IS", "Yapı Kredi": "YKBNK.IS"
}

bist_100 = {**bist_30, **{
    "Alfa Solar": "ALFAS.IS", "Arçelik": "ARCLK.IS", "Brisa": "BRISA.IS", "Çimsa": "CIMSA.IS", 
    "CW Enerji": "CWENE.IS", "Doğuş Oto": "DOAS.IS", "Doğan Hol": "DOHOL.IS", "Eczacıbaşı": "ECILC.IS", 
    "Ege Endüstri": "EGEEN.IS", "Enerjisa": "ENJSA.IS", "Europower": "EUPWR.IS", "Girişim Elk": "GESAN.IS", 
    "Halkbank": "HALKB.IS", "İskenderun D.": "ISDMR.IS", "İş GYO": "ISGYO.IS", "İş Yatırım": "ISMEN.IS", 
    "Konya Çimento": "KONYA.IS", "Kordsa": "KORDS.IS", "Koza Anadolu": "KOZAA.IS", "Mavi": "MAVI.IS", 
    "Migros": "MGROS.IS", "Mia Teknoloji": "MIATK.IS", "Otokar": "OTKAR.IS", "Oyak Çimento": "OYAKC.IS", 
    "Qua Granite": "QUAGR.IS", "Şekerbank": "SKBNK.IS", "Smart Güneş": "SMRTG.IS", "Şok Market": "SOKM.IS", 
    "TAV": "TAVHL.IS", "Tekfen": "TKFEN.IS", "TSKB": "TSKB.IS", "Türk Telekom": "TTKOM.IS", 
    "Türk Traktör": "TTRAK.IS", "Tukaş": "TUKAS.IS", "Ülker": "ULKER.IS", "Vakıfbank": "VAKBN.IS", 
    "Vestel Beyaz": "VESBE.IS", "Vestel": "VESTL.IS", "Yeo Teknoloji": "YEOTK.IS", "Zorlu Enerji": "ZOREN.IS"
}}

bist_genis = {**bist_100, **{
    "Agrotech": "AGROT.IS", "Akfen Yenilenebilir": "AKFYE.IS", "Anadolu Efes": "AEFES.IS", 
    "Anadolu Sigorta": "ANSGR.IS", "Aygaz": "AYGAZ.IS", "Bera Holding": "BERA.IS", 
    "Bien Seramik": "BIENY.IS", "Biotrend": "BIOEN.IS", "Borusan Yatırım": "BRYAT.IS", 
    "Bülbüloğlu Vinç": "BVSAN.IS", "Can Termik": "CANTE.IS", "Çan2 Termik": "CANTE.IS", 
    "CVK Maden": "CVKMD.IS", "Eksun Gıda": "EKSUN.IS", "Esenboğa Elektrik": "ESEN.IS", 
    "Forte Bilgi": "FORTE.IS", "Galata Wind": "GWIND.IS", "GSD Holding": "GSDHO.IS", 
    "Hat-San Gemi": "HATSN.IS", "İmaş Makina": "IMASM.IS", "İnfo Yatırım": "INFO.IS", 
    "İzdemir Enerji": "IZENR.IS", "Kaleseramik": "KLSER.IS", "Kayseri Şeker": "KAYSE.IS", 
    "Kocaer Çelik": "KCAER.IS", "Kuştur Kuşadası": "KSTUR.IS", "Margün Enerji": "MAGEN.IS", 
    "Mercan Kimya": "MERCN.IS", "Naten": "NATEN.IS", "Oyak Yatırım": "OYYAT.IS", 
    "Özsu Balık": "OZSUB.IS", "Penta": "PENTA.IS", "Reeder Teknoloji": "REEDR.IS", 
    "Rubenis Tekstil": "RUBNS.IS", "SDT Uzay": "SDTTR.IS", "Tarkim": "TARKM.IS", 
    "Tatlıpınar Enerji": "TATEN.IS", "Tezol": "TEZOL.IS", "VBT Yazılım": "VBTYZ.IS", 
    "Ziraat GYO": "ZRGYO.IS"
}}

kripto = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Binance Coin": "BNB-USD", 
    "Ripple (XRP)": "XRP-USD", "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Dogecoin": "DOGE-USD", 
    "Chainlink": "LINK-USD", "Polkadot": "DOT-USD", "Polygon": "MATIC-USD", "Shiba Inu": "SHIB-USD"
}

madenler_emtia = {
    "Altın (Ons)": "GC=F", "Gümüş (Ons)": "SI=F", "Bakır": "HG=F", "Platin": "PL=F", 
    "Paladyum": "PA=F", "Alüminyum": "ALI=F", "Ham Petrol (WTI)": "CL=F", "Brent Petrol": "BZ=F", 
    "Doğal Gaz": "NG=F", "Isıtma Yakıtı": "HO=F", "Buğday": "ZW=F", "Mısır": "ZC=F", 
    "Soya Fasulyesi": "ZS=F", "Kahve": "KC=F", "Şeker": "SB=F", "Pamuk": "CT=F", "Kakao": "CC=F"
}

tum_varliklar_mega = {**bist_genis, **kripto, **madenler_emtia}

# --- SOL MENÜ ---
st.sidebar.header("🕹️ Uygulama Modu")
uygulama_modu = st.sidebar.radio("Mod Seçiniz:", ["🔍 Algoritmik Piyasa Tarama", "💼 Sanal Portföy (Oyun)"])
st.sidebar.markdown("---")

# =========================================================================================
# MOD 1: ALGORİTMİK PİYASA TARAMA
# =========================================================================================
if uygulama_modu == "🔍 Algoritmik Piyasa Tarama":
    st.sidebar.header("⚙️ Tarama Ayarları")
    vade_secimi = st.sidebar.radio("1. Yatırım Vadesi:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"])
    piyasa_secimi = st.sidebar.radio("2. İncelenecek Piyasa:", [
        "🇹🇷 BIST 30 (En Büyükler)", "🇹🇷 BIST 100", "🇹🇷 BIST Tüm (Genişletilmiş)", 
        "🪙 Kripto Paralar", "⛏️ Tüm Emtia ve Madenler", "👤 Kendi İzleme Listem"
    ])

    aktif_varliklar = {}
    if piyasa_secimi == "👤 Kendi İzleme Listem":
        st.sidebar.info("Buradaki seçimleriniz otomatik olarak kaydedilir:")
        
        if "ilk_liste" not in st.session_state:
            st.session_state.ilk_liste = [v for v in cuzdan.get("izleme_listesi", []) if v in tum_varliklar_mega]
            
        secilen_isimler = st.sidebar.multiselect(
            "Varlıkları Seçin:", 
            options=list(tum_varliklar_mega.keys()), 
            default=st.session_state.ilk_liste
        )
        
        if set(secilen_isimler) != set(st.session_state.ilk_liste):
            st.session_state.ilk_liste = secilen_isimler
            cuzdan["izleme_listesi"] = secilen_isimler
            cuzdan_kaydet(cuzdan)
            
        aktif_varliklar = {isim: tum_varliklar_mega[isim] for isim in secilen_isimler}
        
    elif piyasa_secimi == "🇹🇷 BIST 30 (En Büyükler)": aktif_varliklar = bist_30
    elif piyasa_secimi == "🇹🇷 BIST 100": aktif_varliklar = bist_100
    elif piyasa_secimi == "🇹🇷 BIST Tüm (Genişletilmiş)": aktif_varliklar = bist_genis
    elif piyasa_secimi == "🪙 Kripto Paralar": aktif_varliklar = kripto
    else: aktif_varliklar = madenler_emtia

    if 'df_sonuc' not in st.session_state: st.session_state.df_sonuc = pd.DataFrame()
    if 'ozel_portfoy_verisi' not in st.session_state: st.session_state.ozel_portfoy_verisi = pd.DataFrame()

    if st.button("🚀 Algoritmayı Çalıştır"):
        if len(aktif_varliklar) > 100:
            st.warning("⚠️ Çok geniş bir piyasa seçtiniz. Verilerin çekilmesi 1-2 dakika sürebilir, lütfen bekleyin.")
            
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
                    veri_araligi = "2y" if vade_secimi == "📅 Uzun Vadeli (1+ Yıl / Yatırım)" else "6mo"
                    veri = ticker.history(period=veri_araligi)
                    
                    if veri.empty or len(veri) < 20: continue
                    
                    if piyasa_secimi == "👤 Kendi İzleme Listem":
                        temiz_veri = veri['Close'].copy()
                        temiz_veri.index = pd.to_datetime(temiz_veri.index).tz_localize(None).normalize()
                        portfoy_fiyat_gecmisi[isim] = temiz_veri
                        
                    son_fiyat = float(veri['Close'].iloc[-1])
                    puan = 0
                    durum_notu = []

                    if vade_secimi == "⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)":
                        tipik_fiyat = (veri['High'] + veri['Low'] + veri['Close']) / 3
                        para_akisi = tipik_fiyat * veri['Volume']
                        pozitif_akis = np.where(tipik_fiyat > tipik_fiyat.shift(1), para_akisi, 0)
                        negatif_akis = np.where(tipik_fiyat < tipik_fiyat.shift(1), para_akisi, 0)
                        pozitif_mf = pd.Series(pozitif_akis).rolling(window=14).sum()
                        negatif_mf = pd.Series(negatif_akis).rolling(window=14).sum()
                        mfi = 100 - (100 / (1 + (pozitif_mf / negatif_mf)))
                        son_mfi = float(mfi.iloc[-1])
                        
                        delta = veri['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rsi = 100 - (100 / (1 + (gain / loss)))
                        son_rsi = float(rsi.iloc[-1])
                        
                        ema_12 = veri['Close'].ewm(span=12, adjust=False).mean()
                        ema_26 = veri['Close'].ewm(span=26, adjust=False).mean()
                        macd = ema_12 - ema_26
                        macd_sinyal = macd.ewm(span=9, adjust=False).mean()
                        
                        sma_20 = veri['Close'].rolling(window=20).mean()
                        std_20 = veri['Close'].rolling(window=20).std()
                        son_alt_bant = float(sma_20.iloc[-1] - (std_20.iloc[-1] * 2))

                        if son_mfi < 20: puan += 3; durum_notu.append("Hacim: Para Girişi 💸")
                        elif son_mfi > 80: puan -= 2; durum_notu.append("Hacim: Para Çıkışı 📉")
                        if son_rsi < 30: puan += 2; durum_notu.append("RSI: Dipte")
                        if float(macd.iloc[-1]) > float(macd_sinyal.iloc[-1]): puan += 1; durum_notu.append("MACD: Pozitif")
                        if son_fiyat < son_alt_bant: puan += 2; durum_notu.append("BB: Aşırı Düştü")
                            
                        sonuclar.append({"Varlık Adı": isim, "Fiyat": round(son_fiyat, 2), "RSI": round(son_rsi, 1), "MFI (Hacim)": round(son_mfi, 1), "Kısa Vade Puanı": puan, "Teknik Özet": " | ".join(durum_notu)})

                    else:
                        sma_50 = veri['Close'].rolling(window=50).mean()
                        sma_200 = veri['Close'].rolling(window=200).mean()
                        if len(veri) < 200 or pd.isna(sma_200.iloc[-1]): continue
                        fk_orani = ticker.info.get('trailingPE', None)
                        if son_fiyat > float(sma_200.iloc[-1]): puan += 3; durum_notu.append("Boğa Piyasası")
                        else: puan -= 2; durum_notu.append("Ayı Piyasası")
                        if float(sma_50.iloc[-1]) > float(sma_200.iloc[-1]): puan += 2; durum_notu.append("Altın Kesişim")
                        else: puan -= 1; durum_notu.append("Ölüm Kesişimi")
                        fk_metni = "Uygulanamaz"
                        if fk_orani and isinstance(fk_orani, (int, float)):
                            fk_metni = str(round(fk_orani, 2)); puan += 2 if fk_orani < 15 else -2 if fk_orani > 30 else 0
                            if fk_orani < 15: durum_notu.append(f"F/K Ucuz ({fk_metni})")

                        sonuclar.append({"Varlık Adı": isim, "Fiyat": round(son_fiyat, 2), "200 Günlük Ort.": round(float(sma_200.iloc[-1]), 2), "F/K Oranı": fk_metni, "Uzun Vade Puanı": puan, "Teknik Özet": " | ".join(durum_notu)})
                except Exception as e: pass 
                finally:
                    islenen += 1
                    ilerleme_cubugu.progress(min(islenen / toplam_varlik, 1.0))
                    if toplam_varlik > 100: time.sleep(0.05)

            durum_metni.empty() 
            ilerleme_cubugu.empty() 
            
            if sonuclar:
                df_temp = pd.DataFrame(sonuclar)
                puan_sutunu = "Uzun Vade Puanı" if vade_secimi == "📅 Uzun Vadeli (1+ Yıl / Yatırım)" else "Kısa Vade Puanı"
                st.session_state.df_sonuc = df_temp.sort_values(by=puan_sutunu, ascending=False).reset_index(drop=True)
                
                if piyasa_secimi == "👤 Kendi İzleme Listem" and len(portfoy_fiyat_gecmisi) > 1:
                    st.session_state.ozel_portfoy_verisi = pd.DataFrame(portfoy_fiyat_gecmisi)
                else:
                    st.session_state.ozel_portfoy_verisi = pd.DataFrame()
            else: st.error("Geçerli veri bulunamadı.")
        else:
            st.warning("Lütfen sol menüden en az bir varlık seçin.")

    # --- ANALİZ SONUÇLARI VE AKILLI TABLO (HEATMAP) ---
    if not st.session_state.df_sonuc.empty:
        st.success("✅ Tarama Tamamlandı!")
        
        try:
            if "Kısa" in vade_secimi:
                def style_rsi(val):
                    try:
                        v = float(val)
                        if v < 35: return 'background-color: rgba(0, 255, 0, 0.2); font-weight: bold; color: #00ff00;'
                        elif v > 65: return 'background-color: rgba(255, 0, 0, 0.2); font-weight: bold; color: #ff4444;'
                    except: pass
                    return ''
                if hasattr(st.session_state.df_sonuc.style, "map"):
                    styled_df = st.session_state.df_sonuc.style.map(style_rsi, subset=['RSI'])
                else:
                    styled_df = st.session_state.df_sonuc.style.applymap(style_rsi, subset=['RSI'])
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.dataframe(st.session_state.df_sonuc, use_container_width=True)
        except:
            st.dataframe(st.session_state.df_sonuc, use_container_width=True)
            
        st.markdown("---")
        
        # FERAH TASARIM: Markowitz Portföy Optimizasyonu
        if piyasa_secimi == "👤 Kendi İzleme Listem" and not st.session_state.ozel_portfoy_verisi.empty:
            with st.expander("⚖️ Markowitz Optimum Portföy Dağılımını Göster", expanded=False):
                st.write("Sistem, seçtiğiniz varlıkların geçmiş korelasyonlarını analiz ederek riski minimumda tutan altın oranları hesapladı.")
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
                    pie_data = pd.DataFrame({'Varlık': df_port.columns, 'Oran': opt_weights * 100})
                    col_pie, col_text = st.columns([1, 1])
                    with col_pie:
                        fig_pie = px.pie(pie_data, values='Oran', names='Varlık', title="Optimum Sermaye Dağılımı", hole=0.4, template="plotly_dark")
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col_text:
                        st.info("💡 **Analiz:** Bu dağılım, sadece en çok kazandıranı seçmez. Riski dengeleyecek en ideal matematiksel kurguyu sunar.")
                        st.write(f"**Beklenen Yıllık Getiri:** %{round(results[0,max_sharpe_idx]*100, 2)}")
                        st.write(f"**Tahmini Yıllık Risk (Volatilite):** %{round(results[1,max_sharpe_idx]*100, 2)}")
                        st.write(f"**Sharpe Oranı:** {round(results[2,max_sharpe_idx], 2)}")
                else:
                    st.warning("Geçmiş veri optimizasyon için yeterli değil.")
        
        # Grafikler ve Sekmeler
        st.write("### 🤖 Gelişmiş Analiz Paneli")
        liste = st.session_state.df_sonuc['Varlık Adı'].tolist()
        secilen_isim = st.selectbox("Detaylı grafik analizi için varlık seçin:", liste)
        secilen_sembol = tum_varliklar_mega.get(secilen_isim)
        
        if secilen_sembol:
            col1, col2 = st.columns([2, 1])
            with col1:
                with st.spinner("Yapay Zeka modelleri hesaplanıyor..."):
                    grafik_veri = yf.Ticker(secilen_sembol).history(period="6mo")
                    if not grafik_veri.empty:
                        tab1, tab2, tab3 = st.tabs(["🤖 Yapay Zeka (Trend)", "🎲 Monte Carlo", "⏪ Backtest"])
                        with tab1:
                            df_ml = grafik_veri[['Close']].dropna().copy()
                            df_ml['Gunler'] = np.arange(len(df_ml))
                            model = LinearRegression().fit(df_ml[['Gunler']], df_ml['Close'])
                            y_tahmin = model.predict(np.array([[len(df_ml) + i] for i in range(1, 16)]))
                            gelecek_tarihler = [df_ml.index[-1] + pd.Timedelta(days=i) for i in range(1, 16)]
                            fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=('Fiyat & AI Tahmini', 'Hacim'), row_width=[0.3, 0.7])
                            fig1.add_trace(go.Candlestick(x=grafik_veri.index, open=grafik_veri['Open'], high=grafik_veri['High'], low=grafik_veri['Low'], close=grafik_veri['Close'], name='Fiyat'), row=1, col=1)
                            fig1.add_trace(go.Scatter(x=gelecek_tarihler, y=y_tahmin, mode='lines', name='🤖 AI Rotası', line=dict(color='cyan', width=4, dash='dot')), row=1, col=1)
                            renkler = ['green' if c >= o else 'red' for o, c in zip(grafik_veri['Open'], grafik_veri['Close'])]
                            fig1.add_trace(go.Bar(x=grafik_veri.index, y=grafik_veri['Volume'], marker_color=renkler, name='Hacim'), row=2, col=1)
                            fig1.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark", margin=dict(t=30, b=10))
                            st.plotly_chart(fig1, use_container_width=True)
                        with tab2:
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
                            fig2.update_layout(height=550, template="plotly_dark", margin=dict(t=10, b=10))
                            st.plotly_chart(fig2, use_container_width=True)
                        with tab3:
                            st.write("**Strateji:** RSI 30 Altı AL, 70 Üstü SAT. (10.000 TL Sanal Başlangıç)")
                            df_bt = grafik_veri[['Close']].copy()
                            delta_bt = df_bt['Close'].diff()
                            df_bt['RSI'] = 100 - (100 / (1 + ((delta_bt.where(delta_bt > 0, 0)).rolling(14).mean() / (-delta_bt.where(delta_bt < 0, 0)).rolling(14).mean())))
                            nakit, adet = 10000, 0
                            al_t, al_f, sat_t, sat_f = [], [], [], []
                            for index, row in df_bt.iterrows():
                                if pd.isna(row['RSI']): continue
                                if row['RSI'] < 30 and adet == 0: adet, nakit = nakit / row['Close'], 0; al_t.append(index); al_f.append(row['Close'])
                                elif row['RSI'] > 70 and adet > 0: nakit, adet = adet * row['Close'], 0; sat_t.append(index); sat_f.append(row['Close'])
                            son_deger = nakit if adet == 0 else adet * df_bt['Close'].iloc[-1]
                            col_bt1, col_bt2 = st.columns(2)
                            col_bt1.metric("Algoritma (Al-Sat) Getirisi", f"%{round(((son_deger - 10000) / 10000) * 100, 2)}")
                            col_bt2.metric("Sadece Bekleseydin", f"%{round(((df_bt['Close'].iloc[-1] - df_bt['Close'].dropna().iloc[0]) / df_bt['Close'].dropna().iloc[0]) * 100, 2)}")
                            fig3 = go.Figure()
                            fig3.add_trace(go.Scatter(x=df_bt.index, y=df_bt['Close'], mode='lines', name='Fiyat', line=dict(color='white')))
                            if al_t: fig3.add_trace(go.Scatter(x=al_t, y=al_f, mode='markers', name='AL Sinyali', marker=dict(color='green', size=12, symbol='triangle-up')))
                            if sat_t: fig3.add_trace(go.Scatter(x=sat_t, y=sat_f, mode='markers', name='SAT Sinyali', marker=dict(color='red', size=12, symbol='triangle-down')))
                            fig3.update_layout(height=450, template="plotly_dark", margin=dict(t=10, b=10))
                            st.plotly_chart(fig3, use_container_width=True)
            with col2:
                # --- YENİ EKLENEN: NLP DUYGU ANALİZİ (SENTIMENT) ---
                st.write("### 🧠 Piyasa Psikolojisi (Yapay Zeka)")
                try:
                    haberler = yf.Ticker(secilen_sembol).news
                    if haberler:
                        toplam_duygu = 0
                        gecerli_haber = 0
                        
                        for h in haberler[:10]:
                            baslik = h.get('title') or h.get('content', {}).get('title', '')
                            if baslik:
                                analiz = TextBlob(baslik)
                                toplam_duygu += analiz.sentiment.polarity
                                gecerli_haber += 1
                        
                        if gecerli_haber > 0:
                            ortalama_duygu = toplam_duygu / gecerli_haber
                            
                            # Gösterge (Gauge) Grafiği
                            fig_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number",
                                value = ortalama_duygu,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Medya Hissi (Sentiment)", 'font': {'size': 16, 'color': 'white'}},
                                gauge = {
                                    'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "white"},
                                    'bar': {'color': "white", 'thickness': 0.25},
                                    'bgcolor': "rgba(0,0,0,0)",
                                    'steps': [
                                        {'range': [-1, -0.2], 'color': "rgba(255, 68, 68, 0.6)"}, # Kırmızı (Ayı)
                                        {'range': [-0.2, 0.2], 'color': "rgba(150, 150, 150, 0.4)"}, # Gri (Nötr)
                                        {'range': [0.2, 1], 'color': "rgba(0, 200, 83, 0.6)"} # Yeşil (Boğa)
                                    ],
                                }
                            ))
                            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20), template="plotly_dark")
                            st.plotly_chart(fig_gauge, use_container_width=True)
                            
                            if ortalama_duygu > 0.2: st.success("📈 **AI Yorumu:** Haber akışı şu an **POZİTİF (Boğa)** yönde.")
                            elif ortalama_duygu < -0.2: st.error("📉 **AI Yorumu:** Haber akışı şu an **NEGATİF (Ayı)** yönde.")
                            else: st.info("⚖️ **AI Yorumu:** Haber akışı dengeli, **NÖTR (Belirsiz)**.")
                    else:
                        st.info("Haber bulunamadığı için duygu analizi yapılamadı.")
                except Exception as e:
                    st.warning("NLP Motoru başlatılamadı. (TextBlob yüklü olmayabilir)")
                
                st.markdown("---")
                
                # FERAH TASARIM: Haberler için Açılır-Kapanır Panel
                with st.expander("📰 Son Dakika Haberlerini Oku", expanded=True):
                    try:
                        if haberler:
                            for h in haberler[:5]:
                                t = h.get('title') or h.get('content', {}).get('title', 'Başlık Yok')
                                if t != "Başlık Yok":
                                    l = h.get('link') or h.get('url') or h.get('content', {}).get('clickThroughUrl', {}).get('url', '#')
                                    st.markdown(f"🔗 **[{t}]({l})**"); st.markdown("---")
                        else:
                            st.info("Haber bulunamadı.")
                    except: st.error("Haber servisi yüklenemedi.")

# =========================================================================================
# MOD 2: SANAL PORTFÖY (PAPER TRADING OYUNU)
# =========================================================================================
elif uygulama_modu == "💼 Sanal Portföy (Oyun)":
    st.header("💼 Sanal Hedge Fon Yönetimi")
    st.write("Sanal 1.000.000 TL bakiye ile yatırım stratejilerinizi risksiz bir şekilde test edin!")
    
    toplam_varlik_degeri = 0
    guncel_fiyatlar = {}
    
    if cuzdan["varliklar"]:
        st.info("Portföyünüzdeki varlıkların güncel canlı fiyatları çekiliyor...")
        for varlik_ismi, adet in cuzdan["varliklar"].items():
            sembol = tum_varliklar_mega.get(varlik_ismi)
            if sembol:
                try:
                    fiyat = yf.Ticker(sembol).history(period="1d")['Close'].iloc[-1]
                    guncel_fiyatlar[varlik_ismi] = fiyat
                    toplam_varlik_degeri += (fiyat * adet)
                except:
                    guncel_fiyatlar[varlik_ismi] = 0.0

    toplam_portfoy_buyuklugu = cuzdan["nakit"] + toplam_varlik_degeri
    kar_zarar_yuzdesi = ((toplam_portfoy_buyuklugu - 1000000.0) / 1000000.0) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Portföy Değeri", f"{toplam_portfoy_buyuklugu:,.2f} ₺", f"% {kar_zarar_yuzdesi:.2f}")
    col2.metric("Boş Nakit Bakiye", f"{cuzdan['nakit']:,.2f} ₺")
    col3.metric("Yatırımdaki Varlıklar", f"{toplam_varlik_degeri:,.2f} ₺")
    st.markdown("---")

    col_islem, col_durum = st.columns([1, 1])
    
    with col_islem:
        st.subheader("🛒 Hızlı İşlem Masası")
        islem_tipi = st.radio("İşlem Yönü:", ["AL", "SAT"], horizontal=True)
        secili_varlik = st.selectbox("Varlık Seçin:", list(tum_varliklar_mega.keys()))
        sembol_islem = tum_varliklar_mega[secili_varlik]
        
        try:
            anlik_fiyat = yf.Ticker(sembol_islem).history(period="1d")['Close'].iloc[-1]
            st.write(f"Anlık Fiyat: **{anlik_fiyat:,.2f}**")
        except:
            anlik_fiyat = 0
            st.warning("Fiyat çekilemedi. Piyasalar kapalı olabilir.")

        islem_miktari = st.number_input("Adet / Miktar:", min_value=0.01, step=1.0)
        islem_tutari = islem_miktari * anlik_fiyat
        st.write(f"Toplam Tutar: **{islem_tutari:,.2f} ₺**")

        if st.button(f"Siparişi Onayla ({islem_tipi})", use_container_width=True):
            if islem_tipi == "AL":
                if cuzdan["nakit"] >= islem_tutari:
                    cuzdan["nakit"] -= islem_tutari
                    cuzdan["varliklar"][secili_varlik] = cuzdan["varliklar"].get(secili_varlik, 0) + islem_miktari
                    cuzdan_kaydet(cuzdan)
                    st.success(f"✅ {islem_miktari} adet {secili_varlik} başarıyla alındı!")
                    time.sleep(1) 
                    st.rerun() 
                else: st.error("❌ Yetersiz bakiye!")
                    
            elif islem_tipi == "SAT":
                mevcut_adet = cuzdan["varliklar"].get(secili_varlik, 0)
                if mevcut_adet >= islem_miktari:
                    cuzdan["varliklar"][secili_varlik] -= islem_miktari
                    cuzdan["nakit"] += islem_tutari
                    if cuzdan["varliklar"][secili_varlik] <= 0: del cuzdan["varliklar"][secili_varlik]
                    cuzdan_kaydet(cuzdan)
                    st.success(f"✅ {islem_miktari} adet {secili_varlik} başarıyla satıldı!")
                    time.sleep(1)
                    st.rerun() 
                else: st.error(f"❌ Elinde yeterli {secili_varlik} yok! (Mevcut: {mevcut_adet})")

    with col_durum:
        st.subheader("📋 Elinizdeki Varlıklar")
        if cuzdan["varliklar"]:
            portfoy_listesi = [{"Varlık": v, "Adet": round(a, 4), "Güncel Fiyat": round(guncel_fiyatlar.get(v, 0), 2), "Toplam Değer (₺)": round(a * guncel_fiyatlar.get(v, 0), 2)} for v, a in cuzdan["varliklar"].items()]
            st.dataframe(pd.DataFrame(portfoy_listesi).sort_values(by="Toplam Değer (₺)", ascending=False), use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Portföyü Sıfırla (Baştan Başla)", use_container_width=True):
                cuzdan_kaydet({"nakit": 1000000.0, "varliklar": {}, "izleme_listesi": cuzdan.get("izleme_listesi", [])})
                st.rerun()
        else:
            st.info("Portföyünüz şu an boş. Sol taraftan işlem yaparak yatırım yapmaya başlayabilirsiniz!")
