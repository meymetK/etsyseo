import streamlit as st
import google.generativeai as genai
from PIL import Image

# Sayfanın daha ferah görünmesi için 'wide' (geniş) düzeni aktif ettik
st.set_page_config(page_title="Etsy Asistanım", page_icon="✨", layout="wide")

# --- Hafıza (Session State) Tanımlamaları ---
if "boyutlar" not in st.session_state:
    st.session_state.boyutlar = []

def boyut_ekle():
    yeni_boyut = st.session_state.yeni_boyut_input
    if yeni_boyut and yeni_boyut not in st.session_state.boyutlar:
        st.session_state.boyutlar.append(yeni_boyut)
    st.session_state.yeni_boyut_input = "" 

def boyutlari_temizle():
    st.session_state.boyutlar = []

# --- Şifre Ekranı ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Giriş Yapın")
        pwd = st.text_input("Şifreniz:", type="password")
        if st.button("Giriş"):
            if pwd == st.secrets.get("APP_PASSWORD", "123456"): 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Yanlış şifre kanka, tekrar dene!")
        return False
    return True

if check_password():
    st.title("🎨 Atölye - Ürün Yükleme Asistanı")
    st.markdown("---")
    
    API_KEY = st.secrets["GEMINI_API_KEY"] 
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')

    # Ekranı Sol (1 birim) ve Sağ (2 birim) olarak bölüyoruz
    sol_sutun, sag_sutun = st.columns([1, 2], gap="large")

    # ================= SOL SÜTUN (AYARLAR) =================
    with sol_sutun:
        st.header("1. Yükleme & Ayarlar")
        
        uploaded_file = st.file_uploader("Ürün Görselini Yükle (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Yüklenen Görsel", use_container_width=True)
            
        st.markdown("---")
        
        dil_secimi = st.radio("Hedef Pazar / Dil Seçimi", ["İngilizce (Etsy, Amazon)", "Türkçe (Trendyol, Shopier)"])
        dil = "İngilizce" if "İngilizce" in dil_secimi else "Türkçe"
        
        st.markdown("---")
        
        st.text_input("Eklenecek boyutu yazıp Ekle'ye basın:", key="yeni_boyut_input")
        c1, c2 = st.columns(2)
        with c1:
            st.button("➕ Boyut Ekle", on_click=boyut_ekle, use_container_width=True)
        with c2:
            if len(st.session_state.boyutlar) > 0:
                st.button("🗑️ Temizle", on_click=boyutlari_temizle, use_container_width=True)

        if st.session_state.boyutlar:
            st.success("Boyutlar: " + " | ".join(st.session_state.boyutlar))
            
        st.markdown("---")
        
        ekstra_not = st.text_area("Ekstra Not (Opsiyonel):", height=80)
        
        st.markdown("---")
        uret_btn = st.button("✨ İçerikleri Üret", type="primary", use_container_width=True)


    # ================= SAĞ SÜTUN (SONUÇLAR) =================
    with sag_sutun:
        st.header("2. Üretilen İçerikler")
        
        if uret_btn and uploaded_file is not None:
            with st.spinner(f"Görsel analiz ediliyor, {dil} dilinde içerikler yazılıyor..."):
                try:
                    boyut_metni = ""
                    if len(st.session_state.boyutlar) > 0:
                        boyut_metni = f"\nÜrünün boyut varyantları şunlardır: {', '.join(st.session_state.boyutlar)}. Bunu açıklamada liste halinde belirt."

                    prompt = f"""
                    Sen profesyonel bir e-ticaret SEO uzmanı ve metin yazarısın. Görseldeki el emeği atölye ürününü analiz et. 
                    {boyut_metni}
                    
                    Lütfen çıktıyı **{dil.upper()}** dilinde yaz ve tam olarak aşağıdaki GİZLİ AYRAÇLARI kullanarak bölümlere ayır. Başka hiçbir giriş cümlesi kurma.
                    
                    [BASLIK]
                    Buraya SEO uyumlu başlık.
                    [ACIKLAMA]
                    Buraya samimi açıklama metni.
                    [ETIKETLER]
                    Buraya 13 adet, aralarına virgül konmuş etiket.
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    # Metni ayraçlardan bölüyoruz
                    sonuc = response.text
                    baslik = sonuc.split("[ACIKLAMA]")[0].replace("[BASLIK]", "").strip()
                    kalan = sonuc.split("[ACIKLAMA]")[1]
                    aciklama = kalan.split("[ETIKETLER]")[0].strip()
                    etiketler = kalan.split("[ETIKETLER]")[1].strip()

                    if ekstra_not:
                        aciklama += f"\n\n---\n**Not:** {ekstra_not}"

                    # Sağ tarafı kendi içinde 3 farklı sütuna bölüyoruz
                    sonuc_col1, sonuc_col2, sonuc_col3 = st.columns(3)
                    
                    with sonuc_col1:
                        st.subheader("📌 Başlık")
                        st.code(baslik, language="markdown")
                        
                    with sonuc_col2:
                        st.subheader("📖 Açıklama")
                        st.code(aciklama, language="markdown")
                        
                    with sonuc_col3:
                        st.subheader("🏷️ Etiketler")
                        st.code(etiketler, language="markdown")
                        
                    st.success("İşlem Tamam! Metin kutularının sağ üst köşesindeki ikona tıklayarak kopyalayabilirsiniz.")

                except Exception as e:
                    st.error("Bir hata oluştu veya yapay zeka metni doğru formatta bölmedi. Lütfen tekrar deneyin.")
        
        elif not uploaded_file:
            st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
