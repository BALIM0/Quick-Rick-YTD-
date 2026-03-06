import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
import json
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Pro-Yatırım Terminali", layout="wide", page_icon="📈")
st.title("🛡️ Profesyonel Algoritmik Yatırım Karargahı")

# --- VERİTABANI (JSON) FONKSİYONLARI ---
DOSYA_ADI = "sanal_cuzdan.json"

def cuzdan_yukle():
    if os.path.exists(DOSYA_ADI):
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            veri = json.load(f)
            # Eğer eski dosyada izleme listesi yoksa, çökmemesi için otomatik ekle
            if "izleme_listesi" not in veri:
                veri["izleme_listesi"] = ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)"]
            return veri
    # İlk kez giriyorsa varsayılan verileri oluştur
    return {
        "nakit": 100000.0, 
        "varliklar": {}, 
        "izleme_listesi": ["Türk Hava Yolları", "Bitcoin", "Altın (Ons)"]
    }

def cuzdan_kaydet(veri):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4)

# Uygulama başlarken hafızayı (JSON) yükle
cuzdan = cuzdan_yukle()

# --- PİYASA SÖZLÜKLERİ (TÜM VARLIKLAR) ---
bist_100 = {
    "Akbank": "AKBNK.IS", "Alarko Holding": "ALARK.IS", "Alfa Solar": "ALFAS.IS", "Arçelik": "ARCLK.IS", 
    "Aselsan": "ASELS.IS", "Astor Enerji": "ASTOR.IS", "BİM Mağazalar": "BIMAS.IS", "Brisa": "BRISA.IS", 
    "Borusan": "BRSAN.IS", "Coca Cola İçecek": "CCOLA.IS", "Çimsa": "CIMSA.IS", "CW Enerji": "CWENE.IS", 
    "Doğuş Otomotiv": "DOAS.IS", "Doğan Holding": "DOHOL.IS", "Eczacıbaşı İlaç": "ECILC.IS", 
    "Ege Endüstri": "EGEEN.IS", "Emlak Konut GYO": "EKGYO.IS", "Enerjisa": "ENJSA.IS", "Enka İnşaat": "ENKAI.IS", 
    "Erdemir (Ereğli)": "EREGL.IS", "Europower Enerji": "EUPWR.IS", "Ford Otosan": "FROTO.IS", 
    "Garanti BBVA": "GARAN.IS", "Girişim Elektrik": "GESAN.IS", "Gübre Fabrikaları": "GUBRF.IS", 
    "Halkbank": "HALKB.IS", "Hektaş": "HEKTS.IS", "İş Bankası (C)": "ISCTR.IS", "İskenderun Demir Çelik": "ISDMR.IS", 
    "İş GYO": "ISGYO.IS", "İş Yatırım": "ISMEN.IS", "Koç Holding": "KCHOL.IS", "Kontrolmatik": "KONTR.IS", 
    "Konya Çimento": "KONYA.IS", "Kordsa": "KORDS.IS", "Koza Anadolu": "KOZAA.IS", "Koza Altın": "KOZAL.IS", 
    "Kardemir (D)": "KRDMD.IS", "Mavi Giyim": "MAVI.IS", "Migros": "MGROS.IS", "Mia Teknoloji": "MIATK.IS", 
    "Odaş Elektrik": "ODAS.IS", "Otokar": "OTKAR.IS", "Oyak Çimento": "OYAKC.IS", "Petkim": "PETKM.IS", 
    "Pegasus": "PGSUS.IS", "Qua Granite": "QUAGR.IS", "Sabancı Holding": "SAHOL.IS", "Sasa Polyester": "SASA.IS", 
    "Şişecam": "SISE.IS", "Şekerbank": "SKBNK.IS", "Smart Güneş Tek.": "SMRTG.IS", "Şok Marketler": "SOKM.IS", 
    "TAV Havalimanları": "TAVHL.IS", "Turkcell": "TCELL.IS", "Türk Hava Yolları": "THYAO.IS", 
    "Tekfen Holding": "TKFEN.IS", "Tofaş": "TOASO.IS", "TSKB": "TSKB.IS", "Türk Telekom": "TTKOM.IS", 
    "Türk Traktör": "TTRAK.IS", "Tukaş": "TUKAS.IS", "Tüpraş": "TUPRS.IS", "Ülker Bisküvi": "ULKER.IS", 
    "Vakıfbank": "VAKBN.IS", "Vestel Beyaz Eşya": "VESBE.IS", "Vestel": "VESTL.IS", "Yeo Teknoloji": "YEOTK.IS", 
    "Yapı Kredi": "YKBNK.IS", "Zorlu Enerji": "ZOREN.IS"
}
kripto = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "Binance Coin": "BNB-USD", "Ripple (XRP)": "XRP-USD", "Cardano": "ADA-USD", "Avalanche (AVAX)": "AVAX-USD", "Dogecoin": "DOGE-USD", "Chainlink": "LINK-USD"}
madenler = {"Altın (Ons)": "GC=F", "Gümüş (Ons)": "SI=F", "Bakır": "HG=F", "Platin": "PL=F", "Paladyum": "PA=F", "Ham Petrol (WTI)": "CL=F", "Doğal Gaz": "NG=F"}

tum_varliklar_mega = {**bist_100, **kripto, **madenler}

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
    piyasa_secimi = st.sidebar.radio("2. İncelenecek Piyasa:", ["🇹🇷 BIST 100 Hisseleri", "🪙 Majör Kripto Paralar", "⛏️ Değerli Madenler", "👤 Kendi İzleme Listem"])

    aktif_varliklar = {}
    if piyasa_secimi == "👤 Kendi İzleme Listem":
        st.sidebar.info("Buradaki seçimleriniz otomatik olarak kaydedilir:")
        
        # Sadece mega sözlükte olan geçerli isimleri varsayılan olarak yükle (Hata önleyici)
        kayitli_liste = [v for v in cuzdan.get("izleme_listesi", []) if v in tum_varliklar_mega]
        
        secilen_isimler = st.sidebar.multiselect(
            "Varlıkları Seçin:", 
            options=list(tum_varliklar_mega.keys()), 
            default=kayitli_liste
        )
        
        # Eğer kullanıcı listede bir ekleme/çıkarma yaptıysa JSON dosyasına kaydet
        if set(secilen_isimler) != set(kayitli_liste):
            cuzdan["izleme_listesi"] = secilen_isimler
            cuzdan_kaydet(cuzdan)
            
        aktif_varliklar = {isim: tum_varliklar_mega[isim] for isim in secilen_isimler}
        
    elif piyasa_secimi == "🇹🇷 BIST 100 Hisseleri": aktif_varliklar = bist_100
    elif piyasa_secimi == "🪙 Majör Kripto Paralar": aktif_varliklar = kripto
    else: aktif_varliklar = madenler

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

    if not st.session_state.df_sonuc.empty:
        st.success("✅ Tarama Tamamlandı!")
        st.dataframe(st.session_state.df_sonuc, use_container_width=True)
        st.markdown("---")
        
        # Markowitz Portföy Optimizasyonu
        if piyasa_secimi == "👤 Kendi İzleme Listem" and not st.session_state.ozel_portfoy_verisi.empty:
            st.write("### ⚖️ Markowitz Portföy Optimizasyonu")
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
                    st.info("💡 **Optimizasyon Analizi:** Bu dağılım, riski dengeleyecek en ideal matematiksel kurguyu sunar.")
                    st.write(f"**Beklenen Yıllık Getiri:** %{round(results[0,max_sharpe_idx]*100, 2)}")
                    st.write(f"**Tahmini Yıllık Risk (Volatilite):** %{round(results[1,max_sharpe_idx]*100, 2)}")
                    st.write(f"**Sharpe Oranı:** {round(results[2,max_sharpe_idx], 2)}")
            st.markdown("---")
        
        st.write("### 🤖 Gelişmiş Analiz ve 📰 Haber Akışı")
        liste = st.session_state.df_sonuc['Varlık Adı'].tolist()
        secilen_isim = st.selectbox("Detayları görmek istediğiniz varlığı seçin:", liste)
        secilen_sembol = tum_varliklar_mega.get(secilen_isim)
        
        if secilen_sembol:
            col1, col2 = st.columns([2, 1])
            with col1:
                with st.spinner("Analizler hazırlanıyor..."):
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
                st.write("### 📰 Son Haberler")
                try:
                    for h in yf.Ticker(secilen_sembol).news[:5]:
                        t = h.get('title') or h.get('content', {}).get('title', 'Başlık Yok')
                        if t != "Başlık Yok":
                            l = h.get('link') or h.get('url') or h.get('content', {}).get('clickThroughUrl', {}).get('url', '#')
                            st.markdown(f"**[{t}]({l})**"); st.markdown("---")
                except: st.info("Haber bulunamadı.")


# =========================================================================================
# MOD 2: SANAL PORTFÖY (PAPER TRADING OYUNU)
# =========================================================================================
elif uygulama_modu == "💼 Sanal Portföy (Oyun)":
    st.header("💼 Sanal Portföy Yönetimi")
    st.write("Sanal 100.000 TL bakiye ile yatırım stratejilerinizi risksiz bir şekilde test edin!")
    
    # Anlık fiyatları çekip portföyün güncel değerini hesapla
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
    kar_zarar_yuzdesi = ((toplam_portfoy_buyuklugu - 100000.0) / 100000.0) * 100

    # Metrikleri Göster
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Portföy Değeri", f"{toplam_portfoy_buyuklugu:,.2f} ₺", f"% {kar_zarar_yuzdesi:.2f}")
    col2.metric("Boş Nakit Bakiye", f"{cuzdan['nakit']:,.2f} ₺")
    col3.metric("Yatırımdaki Varlıklar", f"{toplam_varlik_degeri:,.2f} ₺")
    st.markdown("---")

    # AL - SAT EKRANI
    col_islem, col_durum = st.columns([1, 1])
    
    with col_islem:
        st.subheader("🛒 İşlem Yap")
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

        if st.button(f"Onayla ({islem_tipi})"):
            if islem_tipi == "AL":
                if cuzdan["nakit"] >= islem_tutari:
                    cuzdan["nakit"] -= islem_tutari
                    mevcut_adet = cuzdan["varliklar"].get(secili_varlik, 0)
                    cuzdan["varliklar"][secili_varlik] = mevcut_adet + islem_miktari
                    cuzdan_kaydet(cuzdan)
                    st.success(f"{islem_miktari} adet {secili_varlik} başarıyla alındı!")
                    st.rerun() 
                else:
                    st.error("Yetersiz bakiye!")
                    
            elif islem_tipi == "SAT":
                mevcut_adet = cuzdan["varliklar"].get(secili_varlik, 0)
                if mevcut_adet >= islem_miktari:
                    cuzdan["varliklar"][secili_varlik] -= islem_miktari
                    cuzdan["nakit"] += islem_tutari
                    if cuzdan["varliklar"][secili_varlik] <= 0:
                        del cuzdan["varliklar"][secili_varlik]
                    cuzdan_kaydet(cuzdan)
                    st.success(f"{islem_miktari} adet {secili_varlik} başarıyla satıldı!")
                    st.rerun() 
                else:
                    st.error(f"Elinde yeterli {secili_varlik} yok! (Mevcut: {mevcut_adet})")

    with col_durum:
        st.subheader("📋 Elinizdeki Varlıklar")
        if cuzdan["varliklar"]:
            portfoy_listesi = []
            for v_isim, v_adet in cuzdan["varliklar"].items():
                g_fiyat = guncel_fiyatlar.get(v_isim, 0)
                toplam_deger = v_adet * g_fiyat
                portfoy_listesi.append({
                    "Varlık": v_isim, "Adet": round(v_adet, 4),
                    "Güncel Fiyat": round(g_fiyat, 2), "Toplam Değer (₺)": round(toplam_deger, 2)
                })
            df_portfoy = pd.DataFrame(portfoy_listesi).sort_values(by="Toplam Değer (₺)", ascending=False)
            st.dataframe(df_portfoy, use_container_width=True)
            
            if st.button("🗑️ Portföyü Sıfırla (Bastan Başla)"):
                # Sıfırlarken izleme listesini silmiyoruz, sadece bakiyeyi ve varlıkları sıfırlıyoruz
                cuzdan_kaydet({"nakit": 100000.0, "varliklar": {}, "izleme_listesi": cuzdan.get("izleme_listesi", [])})
                st.rerun()
        else:
            st.info("Portföyünüz şu an boş. Sol taraftan piyasa taraması yapıp buraya yatırım yapmaya başlayabilirsiniz!")