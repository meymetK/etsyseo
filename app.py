import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Etsy Asistanım", page_icon="✨")

# --- Hafıza (Session State) Tanımlamaları ---
if "boyutlar" not in st.session_state:
    st.session_state.boyutlar = []

def boyut_ekle():
    yeni_boyut = st.session_state.yeni_boyut_input
    # Eğer kutu boş değilse ve daha önce eklenmemişse listeye ekle
    if yeni_boyut and yeni_boyut not in st.session_state.boyutlar:
        st.session_state.boyutlar.append(yeni_boyut)
    st.session_state.yeni_boyut_input = "" # Kutuyu temizle

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
    
    API_KEY = st.secrets["GEMINI_API_KEY"] 
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')

    # --- 1. Dil Seçimi ---
    st.subheader("1. Hedef Pazar / Dil Seçimi")
    dil_secimi = st.radio(
        "İçerik hangi dilde yazılsın?",
        ["İngilizce (Etsy, Amazon vb.)", "Türkçe (Trendyol, Hepsiburada, Shopier vb.)"]
    )
    dil = "İngilizce" if "İngilizce" in dil_secimi else "Türkçe"

    # --- 2. Boyut Ekleme Alanı ---
    st.subheader("2. Ürün Boyutları Varyantları")
    st.text_input("Eklenecek boyutu yazıp Ekle butonuna basın (Örn: 35cm genişlik):", key="yeni_boyut_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.button("➕ Boyutu Ekle", on_click=boyut_ekle)
    with col2:
        if len(st.session_state.boyutlar) > 0:
            st.button("🗑️ Hepsini Temizle", on_click=boyutlari_temizle)

    if st.session_state.boyutlar:
        st.success("✅ Eklenen Boyutlar: " + " | ".join(st.session_state.boyutlar))

    # --- 3. Ekstra Notlar (Opsiyonel) ---
    st.subheader("3. Ekstra Not (Opsiyonel)")
    ekstra_not = st.text_area("İçeriğin en sonuna eklenecek özel notunuz (Örn: Kargo süresi, kişiselleştirme şartları vb.):", height=100)

    # --- 4. Görsel Yükleme ve Üretim ---
    st.subheader("4. Ürün Görseli")
    uploaded_file = st.file_uploader("Ürün Görselini Yükle (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_container_width=True)

        if st.button("✨ İçerikleri Üret"):
            with st.spinner(f"Görsel analiz ediliyor, {dil} dilinde içerikler yazılıyor..."):
                try:
                    boyut_metni = ""
                    if len(st.session_state.boyutlar) > 0:
                        boyut_metni = f"\nÜrünün müşteriye sunulan boyut varyantları şunlardır: {', '.join(st.session_state.boyutlar)}. Lütfen bu boyut seçeneklerini açıklama kısmında liste halinde belirt."

                    prompt = f"""
                    Sen profesyonel bir e-ticaret SEO uzmanı ve metin yazarısın. Görseldeki ana ürünü detaylıca analiz et. 
                    Bu ürün kendi atölyemizden çıkan, el emeği ve kendi çizimlerimizden oluşan özel bir tasarım.
                    {boyut_metni}
                    
                    ÖNEMLİ KURAL: Çıktının tamamını (Başlık, Açıklama ve Etiketler) **{dil.upper()}** dilinde yazacaksın.
                    
                    Bana şu formatta bir çıktı ver:
                    
                    **BAŞLIK:** Ürünü anlatan, dikkat çekici ve SEO uyumlu bir e-ticaret başlığı.
                    
                    **AÇIKLAMA:** Samimi bir dille, hikayesi olan, arama motorlarında organik bulunmayı sağlayacak anahtar kelimeler içeren metin.
                    
                    **ETİKETLER (TAGS):** Tam olarak 13 adet, aralarına virgül konmuş etiket. Her bir etiket maksimum 20 karakter uzunluğunda olmalı.
                    """
                    response = model.generate_content([prompt, image])
                    st.success("İşlem Tamam!")
                    
                    # Nihai metni oluşturuyoruz
                    nihai_metin = response.text
                    
                    # Eğer ekstra not yazıldıysa, bozmadan en sona ekliyoruz
                    if ekstra_not:
                        nihai_metin += f"\n\n---\n**Not:** {ekstra_not}"
                        
                    st.markdown(nihai_metin)
                    
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
