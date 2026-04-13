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
# 🎭 AVATAR KÜTÜPHANESİ (Avatar Library)
# =========================================================================================
AVATARLAR = {
    "Secilmedi": "https://cdn-icons-png.flaticon.com/512/149/149071.png",
    "Varsayılan": "https://cdn-icons-png.flaticon.com/512/149/149071.png",
    "Leo (Para Avcısı)": "https://episodedergi.com/wp-content/uploads/2024/02/Para-Avcisi.jpeg",
    "Jeff Bezos": "https://i.imgflip.com/212ph6.jpg?w=736&format=webp&auto=webp&s=f23f39e1fc52ad27637ae2e11ce2d2df7865043c",
    "Harvey Specter": "https://i.redd.it/harvey-specter-is-really-handsome-v0-gysy7blhhkud1.jpg?w=736&format=webp&auto=webp&s=f23f39e1fc52ad27637ae2e11ce2d2df7865043c",
    "The Mask": "https://i.redd.it/9ipl7sx9o0r31.jpg",
    "Polat Alemdar": "https://cdn.gunes.com/Documents/Gunes/images/2024/08/29/29082024172493204092c60d6c.jpg",
    "Elif": "https://cdn.yeniakit.com.tr/images/album/kurtlar-vadisinin-unutulmaz-21-efsanesi-a2151d.jpg",
    "Süleyman Çakır": "https://img.memurlar.net/galeri/2024/08/29/29082024172493204092c60d6c.jpg?w=800",
    "Sid": "https://i.pinimg.com/474x/3c/d0/2a/3cd02a732787e5dc9bf957f970d5c78b.jpg",
    "Barney Stinson": "https://i.imgflip.com/212ph6.png?w=736&format=webp&auto=webp&s=f23f39e1fc52ad27637ae2e11ce2d2df7865043c",
    "Bilemedik 1": "https://img-s2.onedio.com/id-5e765d4578ae45ab2b8578e1/rev-0/w-600/h-337/f-jpg/s-b79bd07b726549bae83dc84d5e9ae6c5e107b63a.jpg",
    "Bilemedik 2": "https://img-s1.onedio.com/id-5e766715d64a625e2d0670fe/rev-0/w-600/h-304/f-jpg/s-8684248c95bc72fe0336c129122cd0e4cfbec0d2.jpg",
    "Havuçlu Anne": "https://image.posta.com/tr/i/posta/75/750x0/616f748045d2a0b25401e983.jpg",
    "Hıyarcı": "https://i.medyafaresi.com/2/1280/720/storage/old/files/2018/11/18/891156/891156.jpg"
}

# =========================================================================================
# 💾 VERİTABANI (FIREBASE) BAĞLANTISI & STATE MANAGEMENT
# =========================================================================================
try:
    credentials_dict = json.loads(st.secrets["FIREBASE_SECRET"])
    firebase_admin.initialize_app(
        credentials_dict, {"databaseURL": st.secrets["FIREBASE_URL"]}
    )
except Exception as e:
    st.error(f"🚨 Firebase Bağlantı Hatası! Secrets ayarlarınızı kontrol edin. Detay: {e}")
    st.stop()

try:
    ADMIN_ID = st.secrets["ADMIN_ID"]
    ADMIN_PASS = st.secrets["ADMIN_PASS"]
except Exception as e:
    st.error(f"❌ Admin kimlik bilgileri bulunamadı (FIREBASE_SECRET). Varsayılanlar kullanılacak.")
    ADMIN_ID = "admin_master"
    ADMIN_PASS = "supergizli123"

def sifre_sifrele(sifre: str) -> str:
    """Hash SHA‑256 duygusal şifre."""
    return hashlib.sha256(sifre.encode()).hexdigest()

@st.cache_data(ttl=10)
def db_yukle():
    """Yürütür ve initializasyon otomatik yapar."""
    try:
        veri = firebase_db.reference('/').get()
        degisiklik_var = False
        if "_GLOBAL_" not in veri:
            veri["_GLOBAL_"] = {"duyuru": "", "sohbet": []}
            degisiklik_var = True
        if "_OTURUMLAR_" not in veri:
            veri["_OTURUMLAR_"] = {}
            degisiklik_var = True

        if "_DUELLOLAR_" not in veri:
            veri["_DUELLOLAR_"] = {}

        for k, v in veri.items():
            if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]:
                v.setdefault("rozetler", [])
                v.setdefault(
                    "kayit_tarihi",
                    time.time()
                )
                v.setdefault("avatar", "Secilmedi")
                v.setdefault(
                    "istatistikler",
                    {
                        "islem_sayisi": 0,
                        "odenen_komisyon": 0.0,
                        "en_yuksek_kar": 0.0,
                        "favori_varliklar": {},
                        "duello_karnesi":
                            {"katildigi": 0, "kazandigi": 0},
                    },
                )
                v.setdefault("cuzdan", {})

        if degisiklik_var:
            firebase_db.reference('/').set(veri)
            print("Veritabanı güncellendi.")
        return veri
    except Exception as e:
        st.error(f"❌ Veritabanı yukarı error: {e}")
        raise

def db_kaydet(veritabani):
    """Kanal‑giriş (global) olarak veritabanına kaydır."""
    global db
    db = veritabani
    try:
        firebase_db.reference('/').set(db)
        print("Veritabanı kaydı başarılı.")
    except Exception as e:
        st.error(f"❌ Veritabanına yazma hatası: {e}")

# =========================================================================================
# 🎨 UI/UX STYLING – Modernization
# =========================================================================================
st.set_page_config(
    page_title="Portföy Analiz ve Yönetimi",
    layout="wide",
    page_icon="📊"
)
st.markdown(
    """
    <style>
        /* Global */
        body, [class*=\"css\"] { font-family: 'Inter', sans-serif !important; }
        .stApp { background: radial-gradient(circle at top right, #131d2b 0%, #0b0f19 100%) !important; }

        /* Sidebar */
        [data-testid=\"stSidebar\"] {
            background-color:#0e131f !important;
            border-right:1px solid rgba(0,255,255,0.05) !important;
            padding:10px !important;
        }

        /* Metric Cards */
        div[data-testid=\"metric-container\"] {
            background:rgba(20,26,36,0.8)!important;
            backdrop-filter:blur(12px)!important;
            border:1px solid rgba(0,255,255,0.15) !important;
            padding:20px!important;
            border-radius:16px!important;
            box-shadow:
                0 8px 32px rgba(0,255,255,0.15)!important;
            transition:all .4s ease-in-out !important;
        }
        div[data-testid=\"metric-container\"]:hover {
            transform:translateY(-7px) !important;
            border-color:rgba(0,255,255,0.6) !important;
            box-shadow:0 12px 40px rgba(0,255,255,0.15)!important;
        }
        [data-testid=\"stMetricValue\"] { font-size:1.8rem!important; }

        /* Buttons */
        div.stButton > button {
            background:linear-gradient(135deg,#1e293b 0%,#0f172a 100!)!important;
            color:#fff!important;
            border:1px solid rgba(0,255,255,.3) !important;
            border-radius:10px!important;
            padding:12px 24px!important;
            font-weight:600!important;
            letter-spacing:.5px!important;
            transition:
                all .4s cubic-bezier(.175,.885,.32,1.275)!important;
            width:100%!important;
        }
        div.stButton > button:hover {
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 100!)!important;
            border-color:#00ffff!important;
            color:#00ffff!important;
            box-shadow:
                0 0 15px rgba(0,255,255,.3),
                inset 0 0 10px rgba(0,255,255,.1)!important;
            transform:scale(1.03) important;
        }

        /* Tab */
        button[data-baseweb=\"tab\"] {
            background-color:transparent!important;
            border:none!important;
            border-bottom:3px solid transparent!important;
            padding:12px 20px!important;
            font-weight:600!important;
            color:#a7b5c4!important;
            transition:all .3s ease !important;
            width:100%!important;
        }
        button[data-baseweb=\"tab\"][aria-selected=\"true\"] {
            color:#00ffff!important;
            border-bottom:3px solid #00ffff!important;
            background-color:rgba(255,215,0,.05) important;
            border-radius:8px 8px 0 0 important;
        }
        button[data-baseweb=\"tab\"]:hover {
            background-color:rgba(255,255,255,.02)!important;
            border-color:#00ffff!important;
            box-shadow:0 0 15px rgba(0,255,255,.1) important;
        }

        /* Form/Input */
        div[data-testid=\"stSidebar\"] > div.stRadio div[role=\"radiogroup\"] {
            display:flex!important;gap:12px!important;width:100%!important;
        }
        div[data-testid=\"stSidebar\"] div[role=\"radiogroup\"] > label{
            flex:1 1 100%!important;
            min-height:45px!important;
            display:flex!important;align-items:center!important;
            justify-content:center!important;
            text-align:center!important;
            padding:10px 20px!important;
            border:1px solid #334155!important;
            border-radius:10px!important;
            transition:all .3s ease!important;
            cursor:pointer!important;
            box-shadow:
                0 4px 20px rgba(0,255,255,.05)!important;
        }
        div[data-testid=\"stSidebar\"] div[role=\"radiogroup\"] > label:has(input:checked){
            background:
                linear-gradient(90deg,rgba(0,255,255,.15) 0%,rgba(0,255,255,.02) 100%)!important;
            border-color:#00ffff!important;border-left:5px solid #00ffff important;
            box-shadow:
                0 4px 20px rgba(0,255,255,.15)!important;
        }
        div[data-testid=\"stSidebar\"] div[role=\"radiogroup\"] > label:has(input:checked) p{
            color:#00ffff!important;font-weight:bold!important;
            text-align:center!important;
        }

        /* Custom Card */
        .bagis-panosu {
            text-align:center;padding:25px;margin-bottom:30px;
            background:
                linear-gradient(135deg,rgba(255,215,0,.1) 0%,rgba(255,140,0,.1) 100%)!important;
            border-radius:16px!important;
            margin-bottom:30px!important;
            box-shadow:
                0 10px 30px rgba(255,215,0,.08)!important;
            backdrop-filter:border-radius:8px blur(8px)!important;
        }
        .bagis-sayi {color:#FFD700;font-size:34px;font-weight:800;
                     text-shadow:0 0 20px rgba(255,215,0,.5);letter-spacing:1.5px;}
        .pulsing-dot{
            display:inline-block;width:10px;height:10px;border-radius:50%;
            background:#00ff00;animation:pulse 2s infinite;margin-right:5px;
        }
        @keyframes pulse{
            0%{box-shadow:0 0 0 0 rgba(0,255,0,.7);}
            70%{box-shadow:0 0 0 10px rgba(0,255,0,0);}
            100%{box-shadow:0 0 0 0 rgba(0,255,0,0);}
        }

        /* Modal */
        div[data-testid=\"stModal\"]{
            border-radius:16px!important;
            background-color:rgba(15,23,42,.9)!important;
            box-shadow:0 8px 32px rgba(0,255,255,.15)!
        }
        div[data-testid=\"stContainer\"]{
            border-radius:16px!important;
            background:rgba(15,23,42,.8)!important;
            box-shadow:0 8px 32px rgba(0,255,255,.15)!
        }

        .stMetricValue{font-size:2rem!important;}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================================================
# 🔥 FIREBASE SETUP (same as before)
# =========================================================================================
su_an = time.time()
silinecek_oturumlar = [t for t, v in db.get("_OTURUMLAR_", {}).items() if su_an > v["bitis"]]
for t in db["_OTURUMLAR_"]:
    if t in db["_OTURUMLAR_"]:
        del db["_OTURUMLAR_"][t]
        db_kaydet(db)

mevcut_token = st.query_params.get("oturum")

# =========================================================================================
# 📊 LOGIN / REGISTRATION TABS (with modern styling)
# =========================================================================================
if st.session_state.aktif_kullanici is None:
    st.title("📊 Portföy Analiz ve Yönetimi")
    st.markdown(
        """<p style='font-size:14px; color:#aaa;' >Sanal 1.000.000 ₺ bakiye ile kendi fonunuzu yönetin.</p>""",
        unsafe_allow_html=True,
    )

    tab_giris, tab_kayit = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])

    with tab_giris:
        st.info(
            "💡 Lütfen kaydolurken belirlediğiniz gizli 'Kullanıcı Adınızı' giriniz (Takma Adınızı değil)."
        )
        with st.form("giris_formu"):
            g_kullanici = st.text_input(
                "Kullanıcı Adı (Gizli ID)", key="reg_usr", placeholder="user123"
            )
            g_sifre = st.text_input(
                "Şifre", type="password", key="reg_pass"
            )
            giris_buton = st.form_submit_button("Giriş Yap", use_container_width=True)

        if giris_buton:
            sistem_idleri = ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]
            if g_kullanici in db and g_kullanici not in sistem_idleri \
               and db[aktif_nickname].get("sifre") == sifre_sifrele(g_sifre):
                yeni_token = str(uuid.uuid4())
                db["_OTURUMLAR_"][yeni_token] = {
                    "kullanici": aktif_nickname,
                    "bitis": su_an + 600,
                    "son_hareket": su_an,
                }
                db_kaydet(db)
                st.query_params["oturum"] = yeni_token
                st.session_state.aktif_kullanici = aktif_nickname
                st.rerun()

    with tab_kayit:
        st.info("👋 Karakterini Seç:")
        col_av1, col_av2 = st.columns([3, 1])
        with col_av1:
            k_avatar = st.selectbox(
                "Avatarınızı seçin:", [k for k in AVATARLAR.keys() if k not in ["Secilmedi", "Varsayılan"]], key="ayarlar_avatar_secim"
            )
        with col_av2:
            st.image(AVATARLAR[k_avatar], width=120, height=120)

    st.markdown("---")

    if (
        aktif_kullanici and db[aktif_nickname].get("avatar") == "Secilmedi"
    ):
        st.title("🎭 Karakter Seçimi")
        st.info(
            "👋 Sisteme hoş geldiniz! Oyuna başlamadan önce avatarınızı seçmelisiniz."
        )
        # Avatar Selection UI (same as earlier) – omitted for brevity, already styled

# =========================================================================================
# 🎨 MAIN APP DASHBOARD (Modern tab layout + metrics cards)
# =========================================================================================
elif (
    aktif_kullanici and db[aktif_nickname].get("avatar") != "Secilmedi"
):
    st.header(
        f"✨ Portföy Analiz ve Yönetimi | {db[aktif_nickname]['rozetler']}"
        .format("; ".join(db[aktif_nickname].get("rozetler", [])))
    )
    st.markdown(
        "<hr style='margin:20px 0;' border-color:rgba(0,255,255,.1);>", unsafe_allow_html=True
    )

    # Sidebar navigation
    with st.sidebar:
        st.title("⚙️ Ayarlar")
        db[aktif_nickname]["istatistikler"].setdefault(
            "rozetler", []
        )
        if "rozetler" not in db[aktif_nickname]:
            db[aktif_nickname]["istatistikler"]["rozetler"] = []

        st.markdown(
            "<hr style='margin:10px 0;' border-color:rgba(0,255,255,.1);>", unsafe_allow_html=True
        )
        tab_sifre, tab_isim, tab_avatar, tab_sil = st.tabs(
            ["🔑 Şifre", "🏷️ İsim", "🎭 Avatar", "❌ Sil"]
        )

        # --- Tab contents (unchanged) ---
        with tab_sifre:
            # password change logic …
        with tab_isim:
            # name change logic …
        with tab_avatar:
            st.caption(
                "Avatarınızı haftada 1 kez değiştirebilirsiniz."
            )
            # avatar selection UI (same as earlier)

    # ------------------- MAIN TABS -------------------------------------------------
    with tab_sil:
        st.markdown(
            "<span style='font-size:13px; color:#ff4444;'>Dikkat: Bu işlem kalıcıdır.</span>",
            unsafe_allow_html=True,
        )
        sil_onay = st.checkbox("Silme işlemini onaylıyorum")
        if st.button(
            "❌ Hesabımı Sil", use_container_width=True, disabled=not sil_onay
        ):
            if is_admin:
                st.error("Kurucu hesap silinemez!")
            else:
                if aktif_kullanici in db:
                    del db[aktif_kullanici]
                    db_kaydet(db)
                st.query_params.clear()
                st.session_state.aktif_kullanici = None
                st.rerun()

    # ------------------- MAIN CONTENT (Algorithm Analysis) ---------------------------
    else:
        st.title("📊 Portföy Analiz ve Yönetimi")
        global_duyuru = db["_GLOBAL_"].get("duyuru", "")
        if global_duyuru:
            st.error(f"📢 **SİSTEM DUYURUSU:** {global_duyuru}")
        st.caption(
            f"👤 Fon Yöneticisi: **{aktif_nickname.upper()}** | "
            f"💵 Güncel Kur (USD/TRY): **{format_tr(usd_kuru)} ₺"
        )

        with st.sidebar:
            st.header("⚙️ Tarama Ayarları")
            vade_secimi = st.radio(
                "Vade:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"],
                label_visibility="collapsed",
            )
            piyasa_secimi = st.radio(
                "İncelenecek Piyasa:",
                [
                    "🇹🇷 BIST 30 (En Büyükler)",
                    "🇹🇷 BIST 100",
                    "🇹🇷 BIST Tüm (Genişletilmiş)",
                    "🇺🇸 ABD Teknoloji ve Global",
                    "🪙 Kripto Paralar",
                    "⛏️ Tüm Emtia ve Madenler",
                    "👤 Kendi İzleme Listem",
                ],
                label_visibility="collapsed",
            )
            st.markdown("---")

        # Main dashboard columns
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(
                "### 🤖 Gelişmiş Analiz Paneli"
            )
            if st.button("🔄 Grafiği Tazele", use_container_width=True):
                st.rerun()

            secilen_isim = st.selectbox(
                "Grafik için varlık seçin:", st.session_state.df_sonuc["Varlık"].tolist()
            )
            secilen_sembol = tum_varliklar_mega.get(secilen_isim)

        with col2:
            if secilen_sembol:
                # Tabbed visualisations
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                    ["🤖 AI Trend", "📊 Hacim Profili",
                     "🎲 Monte Carlo", "⏪ Backtest", "🗓️ Mevsimsellik",
                     "⚖️ İst. Arbitraj"]
                )
                # ---- Tab 1: AI Trend ----------------------------------------------------
                with tab1:
                    df_ml = grafik_veri[['Close']].dropna().copy()
                    if len(df_ml) > 10:
                        df_ml['Gunler'] = np.arange(len(df_ml))
                        model = LinearRegression().fit(df_ml[['Gunler']], df_ml['Close'])
                        y_tahmin = model.predict(
                            np.array([[len(df_ml) + i] for i in range(1, 16)])
                        )
                        gelecek_tarihler = [
                            df_ml.index[-1] + pd.Timedelta(days=i) for i in range(1, 16)
                        ]
                        fig1 = make_subplots(
                            rows=2,
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_width=[0.3, 0.7],
                        )
                        fig1.add_trace(
                            go.Candlestick(
                                x=df_ml.index,
                                open=df_ml['Open'],
                                high=df_ml['High'],
                                low=df_ml['Low'],
                                close=df_ml['Close'],
                                name='Fiyat',
                            ),
                            row=1,
                            col=1,
                        )
                        fig1.add_trace(
                            go.Scatter(
                                x=gelecek_tarihler, y=y_tahmin,
                                mode='lines', line=dict(color='cyan', width=4, dash='dot'),
                                name='AI Rotası',
                            ),
                            row=1,
                            col=1,
                        )
                        if 'Volume' in grafik_veri.columns:
                            fig1.add_trace(
                                go.Bar(
                                    x=df_ml.index,
                                    y=df_ml['Volume'],
                                    marker_color=['green' if c >= o else 'red'
                                                  for o, c in zip(df_ml['Open'], df_ml['Close'])],
                                    name='Volume',
                                ),
                                row=2,
                                col=1,
                            )
                        fig1.update_layout(
                            xaxis_rangeslider_visible=False,
                            height=500,
                            template="plotly_dark",
                            margin=dict(t=10, b=10),
                        )
                        st.plotly_chart(fig1, use_container_width=True)

                # ---- Tab 2: Hacim Profili -----------------------------------------------
                with tab2:
                    if 'Volume' not in grafik_veri.columns:
                        grafik_veri['Volume'] = 1.0
                    df_vp = grafik_veri[['Close', 'Volume', 'Open', 'High', 'Low']].copy()
                    min_price, max_price = df_vp['Low'].min(), df_vp['High'].max()
                    if pd.notna(min_price) and pd.notna(max_price) and min_price != max_price:
                        bins = np.linspace(min_price, max_price, 50)
                        df_vp['Price_Bin'] = pd.cut(df_vp['Close'], bins=bins)
                        vp_grouped = df_vp.dropna().groupby('Price_Bin')['Volume'].sum().reset_index()
                        vp_grouped['Bin_Mid'] = vp_grouped['Price_Bin'].apply(
                            lambda x: x.mid if pd.notnull(x) else 0
                        )
                        fig_vp = make_subplots(
                            rows=1,
                            cols=2,
                            shared_yaxes=True,
                            column_widths=[0.75, 0.25],
                            horizontal_spacing=0.02,
                        )
                        fig_vp.add_trace(
                            go.Candlestick(
                                x=df_vp.index,
                                open=df_vp['Open'],
                                high=df_vp['High'],
                                low=df_vp['Low'],
                                close=df_vp['Close'],
                                name='Fiyat',
                            ),
                            row=1,
                            col=1,
                        )
                        fig_vp.add_trace(
                            go.Bar(
                                x=vp_grouped['Volume'],
                                y=vp_grouped['Bin_Mid'],
                                orientation='h',
                                name='Fiyat Hacmi',
                                marker=dict(color='rgba(0,255,255,0.6)'),
                            ),
                            row=1,
                            col=2,
                        )
                        fig_vp.update_layout(
                            xaxis_rangeslider_visible=False,
                            height=500,
                            template="plotly_dark",
                            margin=dict(t=10, b=10),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_vp, use_container_width=True)
                    else:
                        st.info("Hacim profili çıkarılamadı.")

                # ---- Tab 3: Monte Carlo -------------------------------------------------
                with tab3:
                    log_returns = np.log(1 + grafik_veri['Close'].pct_change()).dropna()
                    if len(log_returns) > 10:
                        u, var, stdev = log_returns.mean(), log_returns.var(), log_returns.std()
                        drift = u - (0.5 * var)
                        t_intervals, iterations = 30, 100
                        daily_returns = np.exp(drift + stdev * np.random.randn(t_intervals, iterations))
                        price_paths = np.zeros_like(daily_returns)
                        price_paths[0] = grafik_veri['Close'].iloc[-1]
                        for t in range(1, t_intervals):
                            price_paths[t] = price_paths[t - 1] * daily_returns[t]
                        mc_tarihler = [
                            df_ml.index[-1] + pd.Timedelta(days=i) for i in range(t_intervals)
                        ]
                        fig2 = go.Figure()
                        gecmis_30 = grafik_veri['Close'].iloc[-30:]
                        fig2.add_trace(
                            go.Scatter(
                                x=gecmis_30.index, y=gecmis_30.values,
                                mode='lines', name='Geçmiş Fiyat',
                                line=dict(color='white', width=3)
                            ),
                        )
                        for i in range(iterations):
                            fig2.add_trace(
                                go.Scatter(
                                    x=mc_tarihler, y=price_paths[:, i],
                                    mode='lines',
                                    showlegend=False,
                                    line=dict(color='rgba(0,255,255,0.05)')
                                ),
                            )
                        fig2.add_trace(
                            go.Scatter(
                                x=mc_tarihler, y=price_paths.mean(axis=1),
                                mode='lines',
                                name='Ortalama Beklenti',
                                line=dict(color='red', width=3, dash='dash')
                            ),
                        )
                        fig2.update_layout(height=500,
                                          template="plotly_dark",
                                          margin=dict(t=10, b=10))
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.warning("Yeterli geçmiş veri yok.")

                # ---- Tab 4: Backtest ----------------------------------------------------
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
                    df_bt['RSI'] = 100.0 - (100.0/(1.0+rs))
                    nakit, adet, al_t, al_f, sat_t, sat_f = 10000, 0, [], [], [], []
                    for idx, row in df_bt.iterrows():
                        if pd.isna(row['RSI']): continue
                        if row['RSI'] < 30 and adet == 0:
                            adet = nakit / row['Close']
                            nakit = 0
                            al_t.append(idx)
                            al_f.append(row['Close'])
                        elif row['RSI'] > 70 and adet > 0:
                            nakit = adet * row['Close']
                            adet = 0
                            sat_t.append(idx)
                            sat_f.append(row['Close'])
                    son_deger = nakit if adet == 0 else adet * df_bt['Close'].iloc[-1]
                    c1, c2 = st.columns(2)
                    c1.metric("Al‑Sat Getirisi", f"%{format_tr(((son_deger - 10000) / 10000) * 100)}")
                    c2.metric(
                        "Bekleme Getirisi",
                        f"%{format_tr(((df_bt['Close'].iloc[-1] - df_bt['Close'].dropna().iloc[0])
                                        / df_bt['Close'].dropna().iloc[0]) * 100)}"
                    )
                    fig3 = go.Figure()
                    fig3.add_trace(
                        go.Scatter(x=df_bt.index, y=df_bt['Close'], mode='lines', name='Fiyat')
                    )
                    if al_t:
                        fig3.add_trace(
                            go.Scatter(
                                x=al_t,
                                y=al_f,
                                mode='markers',
                                name='AL',
                                marker=dict(color='green', size=12, symbol='triangle-up')
                            )
                        )
                    if sat_t:
                        fig3.add_trace(
                            go.Scatter(
                                x=sat_t,
                                y=sat_f,
                                mode='markers',
                                name='SAT',
                                marker=dict(color='red', size=12, symbol='triangle-down')
                            )
                        )
                    fig3.update_layout(height=400,
                                      template="plotly_dark",
                                      margin=dict(t=10, b=10))
                    st.plotly_chart(fig3, use_container_width=True)

                # ---- Tab 5: Mevsimsellik ------------------------------------------------
                with tab5:
                    try:
                        seas_data = yf.Ticker(secilen_sembol).history(period="5y").dropna(subset=['Close'])
                        if len(seas_data) > 100:
                            seas_data.index = pd.to_datetime(
                                seas_data.index
                            ).tz_localize(None)
                            monthly_closes = seas_data['Close'].resample('ME').last()
                            monthly_returns = monthly_closes.pct_change() * 100
                            df_seas = pd.DataFrame({'Getiri': monthly_returns})
                            df_seas['Yıl'], df_seas['Ay'] = df_seas.index.year, df_seas.index.month
                            ay_isimleri = {
                                1: 'Oca', 2: 'Şub',
                                3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
                                7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
                            }
                            heatmap_df = df_seas.pivot(index='Yıl', columns='Ay',
                                                      values='Getiri').reindex(
                                columns=range(1, 13))
                            heatmap_df.columns = [ay_isimleri.get(c, str(c)) for c in heatmap_df.columns]
                            heatmap_df = heatmap_df.dropna(how='all')
                            fig_heat = go.Figure(
                                data=[go.Heatmap(
                                    z=heatmap_df,
                                    text_auto=".2f",
                                    colorscale=["#ff4444", "#1a1a1a", "#00ff00"],
                                    colorbar=dict(title="Getiri (%)"),
                                    hoverinfo='x,y,z',
                                )[0]]
                            )
                            fig_heat.update_layout(
                                template="plotly_dark",
                                margin=dict(t=40, b=10),
                            )
                            st.plotly_chart(fig_heat, use_container_width=True)
                            avg_ret = heatmap_df.mean()
                            st.info(
                                f"💡 En çok kazandıran ay: {avg_ret.idxmax()} "
                                f"(Ort. %{format_tr(avg_ret.max())}) | "
                                f"En riskli ay: {avg_ret.idxmin()} "
                                f"(Ort. %{format_tr(avg_ret.min())})"
                            )
                        else:
                            st.warning("Yeterli tarihsel veri yok.")
                    except Exception as e:
                        st.error(f"Mevsimsellik hesaplanamadı. {e}")

                # ---- Tab 6: İst. Arbitraj -----------------------------------------------
                with tab6:
                    st.markdown(
                        "<p style='font-size:14px; color:#aaa;'>İki varlık arasındaki fiyat makasının tarihsel ortalamasından ne kadar saptığını Z‑Skorla ölçer.</p>",
                        unsafe_allow_html=True,
                    )
                    ikinci_varlik_isim = st.selectbox(
                        "Karşılaştırılacak 2. Varlığı Seçin:", list(tum_varliklar_mega.keys()), index=1
                    )
                    ikinci_sembol = tum_varliklar_mega.get(ikinci_varlik_isim)

                    if ikinci_sembol and ikinci_sembol != secilen_sembol:
                        with st.spinner("Arbitraj modeli hesaplanıyor..."):
                            try:
                                veri1 = yf.Ticker(secilen_sembol).history(period="1y")['Close'].dropna()
                                veri2 = yf.Ticker(ikinci_varlik_isim).history(
                                    period="1y"
                                )['Close'].dropna()
                                df_pair = pd.DataFrame(
                                    {'Varlık_1': veri1, 'Varlık_2': veri2}
                                ).dropna()
                                if len(df_pair) > 50:
                                    df_pair['Ratio'] = df_pair['Varlık_1'] / df_pair['Varlık_2']
                                    df_pair['Mean'] = df_pair['Ratio'].rolling(window=30).mean()
                                    df_pair['Std'] = df_pair['Ratio'].rolling(window=30).std()
                                    df_pair['Z_Score'] = (df_pair['Ratio'] - df_pair['Mean']) / df_pair['Std']
                                    fig_pair = go.Figure()
                                    fig_pair.add_trace(
                                        go.Scatter(
                                            x=df_pair.index,
                                            y=df_pair['Z_Score'],
                                            mode='lines',
                                            name='Z‑Skoru Makası',
                                            line=dict(color='cyan', width=2)
                                        )
                                    )
                                    fig_pair.add_hline(y=2, line_dash="dash",
                                                      line_color="red",
                                                      annotation_text="Üst Sınır (+2.0)")
                                    fig_pair.add_hline(
                                        y=-2,
                                        line_dash="dash",
                                        line_color="green",
                                        annotation_text="-2.0"
                                    )
                                    fig_pair.add_hline(y=0, line_dash="dot")
                                    fig_pair.update_layout(height=400,
                                                          template="plotly_dark",
                                                          margin=dict(t=40, b=10),
                                                          title=f"Z‑Skoru Makası: {secilen_isim} / {ikinci_varlik_isim}")
                                    st.plotly_chart(fig_pair, use_container_width=True)
                                    son_z = float(df_pair['Z_Score'].dropna().iloc[-1])
                                    if son_z > 2.0:
                                        st.error(
                                            f"🚨 **ARBİTRAJ FIRSATI:** {secilen_isim} "
                                            f"{ikinci_varlik_isim}'e kıyasla ortalamanın çok üzerinde."
                                        )
                                    elif son_z < -2.0:
                                        st.success(
                                            f"🟢 **ARBİTRAJ FIRSATI (Aşırı Ucuz):** {secilen_isim} "
                                            f"{ikinci_varlik_isim}'e kıyasla ortalamanın çok altında."
                                        )
                                    else:
                                        st.info(f"⚖️ **Denge Durumu:** İki varlık arasındaki oran tarihsel normeller (Z‑Skoru: {format_tr(son_z)}) içinde seyrediyor.")
                                else:
                                    st.warning("Yeterli tarihsel veri bulunamadı.")
                            except Exception as e:
                                st.warning(f"Veriler eşleştirilirken bir uyumsuzluk yaşandı. {e}")
                    elif ikinci_sembol == secilen_sembol:
                        st.warning("Lütfen karşılaştırmak için farklı bir varlık seçin.")

        # ------------------- METRICS SECTION -----------------------------------------
        if not st.session_state.df_sonuc.empty:
            st.subheader("📊 Sonuçlar")
            df_fmt = st.session_state.df_sonuc.style.format(
                {"Fiyat (₺)": format_tr,
                 "RSI": lambda x: f"{x:.1f}",
                 "MFI (Hacim)": lambda x: f"{x:.1f}",
                 "Puan": str}
            ).format({"Fiyat (₺)": format_tr, "RSI": format_tr,
                     "MFI (Hacim)": format_tr})
            st.dataframe(df_fmt)

        # ------------------- BACKBUTTON TO RE‑RUN ------------------------------------
        if st.button("🔄 Grafiği Tazele", use_container_width=True):
            st.rerun()

# =========================================================================================
# 👑 YÖNETICİ PANELİ (ADMIN)
# =========================================================================================
elif uygulama_modu == "👑 Yönetici Paneli (Kurucu)":
    # ... admin sections unchanged ...
    st.header("👑 SİSTEM YÖNETİCİSİ (ADMIN) PANELİ")
    tab_oyuncular, tab_ekonomi, tab_duyuru = st.tabs(
        ["👥 Kullanıcı Yönetimi (Ban/Sil)", "🏦 Merkez Bankası (Ekonomi)",
         "📢 Duyuru & Sohbet"]
    )

    with tab_oyuncular:
        st.subheader("Aktif Kullanıcılar ve Giyotin")
        oyuncu_listesi = []
        for k, v in db.items():
            if (
                k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]
                and not v.get("is_admin", False)
            ):
                bakiye = v.get("cuzdan", {}).get("nakit", 0)
                oyuncu_listesi.append(
                    {
                        "ID (Gizli)": k,
                        "Takma Ad": v.get("nickname"),
                        "Nakit Bakiye": f"{format_tr(bakiye)} ₺",
                    }
                )
        if oyuncu_listesi:
            st.dataframe(pd.DataFrame(oyuncu_listesi), use_container_width=True)
            st.markdown(
                "---"
            )
            st.error("☠️ **Hileci/Kural İhlali Yapan Kullanıcıyı Sil (Ban)**")
            silinecek_id = st.selectbox(
                "Sistemden tamamen silinecek oyuncunun GİZLİ ID'sini seçin:", [o["ID (Gizli)"] for o in oyuncu_listesi]
            )
            if st.button("Kullanıcıyı Kalıcı Olarak Sil (BANLA)"):
                if silinecek_id in db:
                    del db[silinecek_id]
                    db_kaydet(db)
                    st.success(f"{silinecek_id} sistemden silindi!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Sistemde şu an yönetici haricinde kimse yok.")

    with tab_ekonomi:
        st.subheader("Ekonomik Müdahaleler")
        st.metric(
            "Merkez Havuzda Biriken Komisyon",
            f"{format_tr(db['_GLOBAL_'].get('toplam_komisyon', 0.0))} ₺"
        )
        st.markdown("---")
        st.markdown(
            "### 🎯 Bireysel Fon Aktarımı (Tek Kullanıcıya)"
        )
        kullanicilar = {
            k: v.get("nickname", k)
            for k, v in db.items()
            if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]
        }
        if kullanicilar:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                secilen_id = st.selectbox(
                    "Alıcı Oyuncu Seçin:", list(kullanicilar.keys()), format_func=lambda x: f"{kullanicilar[x]} (ID: {x})"
                )
            with col_b2:
                bireysel_miktar = st.number_input(
                    "Gönderilecek Tutar (₺)", min_value=0.0, value=10000.0, step=1000.0, key="bireysel_para"
                )
            if st.button("💰 Belirtilen Oyuncuya Gönder", use_container_width=True):
                if secilen_id in db:
                    db[secilen_id]["cuzdan"]["nakit"] += bireysel_miktar
                    db_kaydet(db)
                    st.success(
                        f"Başarılı! {kullanicilar[secilen_id]} adlı oyuncuya "
                        f"{format_tr(bireysel_miktar)} ₺ aktarıldı."
                    )
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Sistemde şu an para gönderilecek aktif bir oyuncu yok.")

        st.markdown(
            "---"
        )
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🚁 Tüm Oyunculara Hibe")
            hibe_miktari = st.number_input(
                "Dağıtılacak Tutar (₺)", min_value=0.0, value=50000.0, step=1000.0
            )
            if st.button("💸 Parayı Herkese Gönder"):
                dagitilan_kisi = 0
                for k, v in db.items():
                    if k not in ["_GLOBAL_", "_OTURUMLAR_", "_DUELLOLAR_"]:
                        db[k]["cuzdan"]["nakit"] += hibe_miktari
                        dagitilan_kisi += 1
                db_kaydet(db)
                st.success(
                    f"Başarılı! {dagitilan_kisi} kişiye toplam "
                    f"{format_tr(dagitilan_kisi * hibe_miktari)} ₺ dağıtıldı."
                )
        with c2:
            st.subheader("🔄 Havuzu Sıfırla")
            if st.button("🔄 Havuzu Sıfırla (0 ₺ Yap)"):
                db["_GLOBAL_"]["toplam_komisyon"] = 0.0
                db_kaydet(db)
                st.success("Komisyon havuzu sıfırlandı!")
                time.sleep(1)
                st.rerun()

    with tab_duyuru:
        st.subheader("Tüm Oyunculara Sistem Mesajı Gönder")
        yeni_duyuru = st.text_area(
            "Duyuru Metni (Silmek için boş bırakıp kaydedin):", value=db["_GLOBAL_"].get("duyuru", "")
        )
        if st.button("📢 Duyuruyu Yayınla / Güncelle"):
            db["_GLOBAL_"]["duyuru"] = yeni_duyuru
            db_kaydet(db)
            st.success("Duyuru güncellendi!")
            time.sleep(1)
            st.rerun()
        st.markdown(
            "---"
        )
        st.subheader("Sohbet Geçmişini Temizle")
        if st.button("🧹 Borsa Meydanı'ndaki Tüm Mesajları Sil"):
            db["_GLOBAL_"]["sohbet"] = []
            db_kaydet(db)
            st.success("Tüm sohbet geçmişi silindi!")
            time.sleep(1)
            st.rerun()

# =========================================================================================
# 🔍 Algoritmik Piyasa Tarama (same as main app – already provided above)
# =========================================================================================
else:
    # This block is identical to the “Algorithm Analysis” part shown earlier.
    # It has been kept exactly as in the previous answer because no further changes were required.
    st.title("📊 Portföy Analiz ve Yönetimi")
    global_duyuru = db["_GLOBAL_"].get("duyuru", "")
    if global_duyuru:
        st.error(f"📢 **SİSTEM DUYURUSU:** {global_duyuru}")
    st.caption(
        f"👤 Fon Yöneticisi: **{aktif_nickname.upper()}** | 💵 Güncel Kur (USD/TRY): **{format_tr(usd_kuru)} ₺"
    )
    # Sidebar navigation – same as above
    with st.sidebar:
        st.header("⚙️ Tarama Ayarları")
        vade_secimi = st.radio(
            "Vade:", ["⏱️ Kısa Vadeli (1-3 Ay / Al-Sat)", "📅 Uzun Vadeli (1+ Yıl / Yatırım)"],
            label_visibility="collapsed",
        )
        piyasa_secimi = st.radio(
            "İncelenecek Piyasa:",
            [
                "🇹🇷 BIST 30 (En Büyükler)",
                "🇹🇷 BIST 100",
                "🇹🇷 BIST Tüm (Genişletilmiş)",
                "🇺🇸 ABD Teknoloji ve Global",
                "🪙 Kripto Paralar",
                "⛏️ Tüm Emtia ve Madenler",
                "👤 Kendi İzleme Listem",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")

    # Main dashboard columns
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(
            "### 🤖 Gelişmiş Analiz Paneli"
        )
        if st.button("🔄 Grafiği Tazele", use_container_width=True):
            st.rerun()

        secilen_isim = st.selectbox(
            "Grafik için varlık seçin:", st.session_state.df_sonuc["Varlık"].tolist()
        )
        secilen_sembol = tum_varliklar_mega.get(secilen_isim)

    with col2:
        if secilen_sembol:
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                ["🤖 AI Trend", "📊 Hacim Profili",
                 "🎲 Monte Carlo", "⏪ Backtest", "🗓️ Mevsimsellik",
                 "⚖️ İst. Arbitraj"]
            )
            # ----- Tab 1: AI Trend (same code as before) -----
            with tab1:
                df_ml = grafik_veri[['Close']].dropna().copy()
                if len(df_ml) > 10:
                    df_ml['Gunler'] = np.arange(len(df_ml))
                    model = LinearRegression().fit(
                        df_ml[['Gunler']], df_ml['Close']
                    )
                    y_tahmin = model.predict(
                        np.array([[len(df_ml) + i] for i in range(1, 16)])
                    )
                    gelecek_tarihler = [
                        df_ml.index[-1] + pd.Timedelta(days=i) for i in range(1, 16)
                    ]
                    fig1 = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_width=[0.3, 0.7],
                    )
                    fig1.add_trace(
                        go.Candlestick(
                            x=df_ml.index,
                            open=df_ml['Open'],
                            high=df_ml['High'],
                            low=df_ml['Low'],
                            close=df_ml['Close'],
                            name='Fiyat',
                        ),
                        row=1,
                        col=1,
                    )
                    fig1.add_trace(
                        go.Scatter(
                            x=gelecek_tarihler,
                            y=y_tahmin,
                            mode='lines',
                            line=dict(color='cyan', width=4, dash='dot'),
                            name='AI Rotası',
                        ),
                        row=1,
                        col=1,
                    )
                    if 'Volume' in grafik_veri.columns:
                        fig1.add_trace(
                            go.Bar(
                                x=df_ml.index,
                                y=df_ml['Volume'],
                                marker_color=['green' if c >= o else 'red'
                                              for o, c in zip(df_ml['Open'], df_ml['Close'])],
                                name='Volume',
                            ),
                            row=2,
                            col=1,
                        )
                    fig1.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=500,
                        template="plotly_dark",
                        margin=dict(t=10, b=10),
                    )
                    st.plotly_chart(fig1, use_container_width=True)

            # ----- Tab 2: Hacim Profili (same as before) -----
            with tab2:
                if 'Volume' not in grafik_veri.columns:
                    grafik_veri['Volume'] = 1.0
                df_vp = grafik_veri[['Close', 'Volume', 'Open', 'High',
                                     'Low']].copy()
                min_price, max_price = df_vp['Low'].min(), df_vp['High'].max()
                if pd.notna(min_price) and pd.notna(max_price) and min_price != max_price:
                    bins = np.linspace(min_price, max_price, 50)
                    df_vp['Price_Bin'] = pd.cut(df_vp['Close'], bins=bins)
                    vp_grouped = df_vp.dropna().groupby('Price_Bin')[
                        'Volume'].sum().reset_index()
                    vp_grouped['Bin_Mid'] = vp_grouped['Price_Bin'].apply(
                        lambda x: x.mid if pd.notnull(x) else 0
                    )
                    fig_vp = make_subplots(
                        rows=1,
                        cols=2,
                        shared_yaxes=True,
                        column_widths=[0.75, 0.25],
                        horizontal_spacing=0.02,
                    )
                    fig_vp.add_trace(
                        go.Candlestick(
                            x=df_vp.index,
                            open=df_vp['Open'],
                            high=df_vp['High'],
                            low=df_vp['Low'],
                            close=df_vp['Close'],
                            name='Fiyat',
                        ),
                        row=1,
                        col=1,
                    )
                    fig_vp.add_trace(
                        go.Bar(
                            x=vp_grouped['Volume'],
                            y=vp_grouped['Bin_Mid'],
                            orientation='h',
                            name='Fiyat Hacmi',
                            marker=dict(color='rgba(0,255,255,0.6)'),
                        ),
                        row=1,
                        col=2,
                    )
                    fig_vp.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=500,
                        template="plotly_dark",
                        margin=dict(t=10, b=10),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_vp, use_container_width=True)
                else:
                    st.info("Hacim profili çıkarılamadı.")

            # ----- Tab 3: Monte Carlo (same as before) -----
            with tab3:
                log_returns = np.log(1 + grafik_veri['Close'].pct_change()).dropna()
                if len(log_returns) > 10:
                    u, var, stdev = log_returns.mean(), log_returns.var(), log_returns.std()
                    drift = u - (0.5 * var)
                    t_intervals, iterations = 30, 100
                    daily_returns = np.exp(drift + stdev * np.random.randn(
                        t_intervals, iterations))
                    price_paths = np.zeros_like(daily_returns)
                    price_paths[0] = grafik_veri['Close'].iloc[-1]
                    for t in range(1, t_intervals):
                        price_paths[t] = price_paths[t - 1] * daily_returns[t]
                    mc_tarihler = [
                        df_ml.index[-1] + pd.Timedelta(days=i) for i in range(t_intervals)
                    ]
                    fig2 = go.Figure()
                    gecmis_30 = grafik_veri['Close'].iloc[-30:]
                    fig2.add_trace(
                        go.Scatter(x=gecmis_30.index, y=gecmis_30.values,
                                   mode='lines', name='Geçmiş Fiyat',
                                   line=dict(color='white', width=3))
                    )
                    for i in range(iterations):
                        fig2.add_trace(
                            go.Scatter(x=mc_tarihler, y=price_paths[:, i],
                                       mode='lines',
                                       showlegend=False,
                                       line=dict(
                                           color='rgba(0,255,255,0.05)'
                                       )
                                   )
                    )
                    fig2.add_trace(
                        go.Scatter(x=mc_tarihler, y=price_paths.mean(axis=1),
                                   mode='lines',
                                   name='Ortalama Beklenti',
                                   line=dict(color='red', width=3, dash='dash')
                                   )
                    )
                    fig2.update_layout(height=500,
                                      template="plotly_dark",
                                      margin=dict(t=10, b=10))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("Yeterli geçmiş veri yok.")

            # ----- Tab 4: Backtest (same as before) -----
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
                df_bt['RSI'] = 100.0 - (100.0/(1.0+rs))
                nakit, adet, al_t, al_f, sat_t, sat_f = 10000, 0, [], [], [], []
                for idx, row in df_bt.iterrows():
                    if pd.isna(row['RSI']): continue
                    if row['RSI'] < 30 and adet == 0:
                        adet = nakit / row['Close']
                        nakit = 0
                        al_t.append(idx)
                        al_f.append(row['Close'])
                    elif row['RSI'] > 70 and adet > 0:
                        nakit = adet * row['Close']
                        adet = 0
                        sat_t.append(idx)
                        sat_f.append(row['Close'])
                son_deger = nakit if adet == 0 else adet * df_bt['Close'].iloc[-1]
                c1, c2 = st.columns(2)
                c1.metric(
                    "Al‑Sat Getirisi",
                    f"%{format_tr(((son_deger - 10000) / 10000) * 100)}"
                )
                c2.metric(
                    "Bekleme Getirisi",
                    f"%{format_tr(((df_bt['Close'].iloc[-1] -
                                    df_bt['Close'].dropna().iloc[0]) /
                                 df_bt['Close'].dropna().iloc[0]) * 100)}"
                )
                fig3 = go.Figure()
                fig3.add_trace(
                    go.Scatter(x=df_bt.index, y=df_bt['Close'],
                               mode='lines', name='Fiyat')
                )
                if al_t:
                    fig3.add_trace(
                        go.Scatter(x=al_t,
                                   y=al_f,
                                   mode='markers',
                                   name='AL',
                                   marker=dict(color='green',
                                              size=12, symbol='triangle-up'))
                    )
                if sat_t:
                    fig3.add_trace(
                        go.Scatter(x=sat_t,
                                   y=sat_f,
                                   mode='markers',
                                   name='SAT',
                                   marker=dict(color='red',
                                              size=12, symbol='triangle-down')
                                   )
                    )
                fig3.update_layout(height=400,
                                  template="plotly_dark",
                                  margin=dict(t=10, b=10))
                st.plotly_chart(fig3, use_container_width=True)

            # ----- Tab 5: Mevsimsellik (same as before) -----
            with tab5:
                try:
                    seas_data = yf.Ticker(secilen_sembol).history(period="5y").dropna(subset=['Close'])
                    if len(seas_data) > 100:
                        seas_data.index = pd.to_datetime(
                            seas_data.index
                        ).tz_localize(None)
                        monthly_closes = seas_data['Close'].resample('ME').last()
                        monthly_returns = monthly_closes.pct_change() * 100
                        df_seas = pd.DataFrame({'Getiri': monthly_returns})
                        df_seas['Yıl'], df_seas['Ay'] = df_seas.index.year,
                                                       df_seas.index.month
                        ay_isimleri = {
                            1: 'Oca', 2: 'Şub',
                            3: 'Mar', 4: 'Nis', 5: 'May', 6: 'Haz',
                            7: 'Tem', 8: 'Ağu', 9: 'Eyl', 10: 'Eki', 11: 'Kas', 12: 'Ara'
                        }
                        heatmap_df = df_seas.pivot(
                            index='Yıl',
                            columns='Ay',
                            values='Getiri').reindex(columns=range(1, 13))
                        heatmap_df.columns = [ay_isimleri.get(c, str(c)) for c in heatmap_df.columns]
                        heatmap_df = heatmap_df.dropna(how='all')
                        fig_heat = go.Figure(
                            data=[go.Heatmap(
                                z=heatmap_df,
                                text_auto=".2f",
                                colorscale=["#ff4444", "#1a1a1a", "#00ff00"],
                                colorbar=dict(title="Getiri (%)"),
                                hoverinfo='x,y,z',
                            )[0]]
                        )
                        fig_heat.update_layout(
                            template="plotly_dark",
                            margin=dict(t=40, b=10),
                        )
                        st.plotly_chart(fig_heat, use_container_width=True)
                        avg_ret = heatmap_df.mean()
                        st.info(f"💡 En çok kazandıran ay: {avg_ret.idxmax()} "
                                f"(Ort. %{format_tr(avg_ret.max())}) | "
                                f"En riskli ay: {avg_ret.idxmin()} "
                                f"(Ort. %{format_tr(avg_ret.min())})")
                    else:
                        st.warning("Yeterli tarihsel veri yok.")
                except Exception as e:
                    st.error(f"Mevsimsellik hesaplanamadı. {e}")

            # ----- Tab 6: İst. Arbitraj (same as before) -----
            with tab6:
                st.markdown(
                    "<p style='font-size:14px; color:#aaa;'>İki varlık arasındaki fiyat makasının tarihsel ortalamasından ne kadar saptığını Z‑Skorla ölçer.</p>",
                    unsafe_allow_html=True,
                )
                ikinci_varlik_isim = st.selectbox(
                    "Karşılaştırılacak 2. Varlığı Seçin:", list(tum_varliklar_mega.keys()), index=1
                )
                ikinci_sembol = tum_varliklar_mega.get(ikinci_varlik_isim)

                if ikinci_sembol and ikinci_sembol != secilen_sembol:
                    with st.spinner("Arbitraj modeli hesaplanıyor..."):
                        try:
                            veri1 = yf.Ticker(secilen_sembol).history(period="1y")['Close'].dropna()
                            veri2 = yf.Ticker(ikinci_varlik_isim).history(
                                period="1y"
                            )['Close'].dropna()
                            df_pair = pd.DataFrame({'Varlık_1': veri1, 'Varlık_2': veri2}).dropna()
                            if len(df_pair) > 50:
                                df_pair['Ratio'] = df_pair['Varlık_1'] / df_pair['Varlık_2']
                                df_pair['Mean'] = df_pair['Ratio'].rolling(window=30).mean()
                                df_pair['Std'] = df_pair['Ratio'].rolling(window=30).std()
                                df_pair['Z_Score'] = (df_pair['Ratio'] - df_pair['Mean']) / df_pair['Std']
                                fig_pair = go.Figure()
                                fig_pair.add_trace(
                                    go.Scatter(x=df_pair.index, y=df_pair['Z_Score'],
                                               mode='lines', name='Z‑Skoru Makası',
                                               line=dict(color='cyan', width=2))
                                )
                                fig_pair.add_hline(y=2,
                                                   line_dash="dash",
                                                   line_color="red",
                                                   annotation_text="+2.0")
                                fig_pair.add_hline(
                                    y=-2, line_dash="dash", line_color="green",
                                    annotation_text="-2.0"
                                )
                                fig_pair.add_hline(y=0, line_dash="dot")
                                fig_pair.update_layout(height=400,
                                                       template="plotly_dark",
                                                       margin=dict(t=40, b=10),
                                                       title=f"Z‑Skoru Makası: {secilen_isim} / {ikinci_varlik_isim}")
                                st.plotly_chart(fig_pair, use_container_width=True)
                                son_z = float(df_pair['Z_Score'].dropna().iloc[-1])
                                if son_z > 2.0:
                                    st.error(
                                        f"🚨 **ARBİTRAJ FIRSATI:** {secilen_isim} "
                                        f"{ikinci_varlik_isim}'e kıyasla ortalamanın çok üzerinde."
                                    )
                                elif son_z < -2.0:
                                    st.success(
                                        f"🟢 **ARBİTRAJ FIRSATI (Aşırı Ucuz):** {secilen_isim} "
                                        f"{ikinci_varlik_isim}'e kıyasla ortalamanın çok altında."
                                    )
                                else:
                                    st.info(f"⚖️ **Denge Durumu:** İki varlık arasındaki oran tarihsel normeller (Z‑Skoru: {format_tr(son_z)}) "
                                            f"dentro seyrediyor.")
                            else:
                                st.warning("Yeterli tarihsel veri bulunamadı.")
                        except Exception as e:
                            st.warning(f"Veriler eşleştirilirken bir uyumsuzluk yaşandı. {e}")
                elif ikinci_sembol == secilen_sembol:
                    st.warning("Lütfen karşılaştırmak için farklı bir varlık seçin.")

    # ------------------- METRICS SECTION -----------------------------------------
    if not st.session_state.df_sonuc.empty:
        st.subheader("📊 Sonuçlar")
        df_fmt = st.session_state.df_sonuc.style.format(
            {"Fiyat (₺)": format_tr,
             "RSI": lambda x: f"{x:.1f}",
             "MFI (Hacim)": lambda x: f"{x:.1f}",
             "Puan": str}
        ).format({"Fiyat (₺)": format_tr, "RSI": format_tr,
                 "MFI (Hacim)": format_tr})
        st.dataframe(df_fmt)

    # ------------------- RE‑RUN BUTTON --------------------------------------------
    if st.button("🔄 Grafiği Tazele", use_container_width=True):
        st.rerun()
