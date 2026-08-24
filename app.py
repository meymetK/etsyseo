import streamlit as st
import google.generativeai as genai
from PIL import Image

# Sayfa Ayarları
st.set_page_config(page_title="Etsy Asistanım", page_icon="✨")

# Şifre Ekranı
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
    st.title("🎨 Atölye - Etsy Yükleme Asistanı")
    st.markdown("Ürünün fotoğrafını yükle, gerisini bana bırak!")

    API_KEY = st.secrets["GEMINI_API_KEY"] 
    genai.configure(api_key=API_KEY)
    
    # Listenden bulduğumuz en güçlü modeli ekledik
    model = genai.GenerativeModel('gemini-2.5-pro')

    uploaded_file = st.file_uploader("Ürün Görselini Yükle (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_container_width=True)

        if st.button("✨ Başlık, Açıklama ve Etiketleri Üret"):
            with st.spinner("Görsel analiz ediliyor, harika içerikler yazılıyor..."):
                try:
                    prompt = """
                    Sen profesyonel bir Etsy SEO uzmanı ve metin yazarısın. Görseldeki ana ürünü detaylıca analiz et. 
                    Bu ürün kendi atölyemizden çıkan, el emeği ve kendi çizimlerimizden oluşan özel bir tasarım. (Özellikle beyaz vinil düğün arabası çıkartmaları, şık yeni doğan bebek kapı süsleri veya özenle hazırlanmış dekoratif objeler olabilir). 
                    Bana şu formatta bir çıktı ver:
                    
                    **BAŞLIK:** Ürünü anlatan, dikkat çekici ve SEO uyumlu bir Etsy başlığı.
                    
                    **AÇIKLAMA:** Samimi bir dille, hikayesi olan, arama motorlarında organik bulunmayı sağlayacak anahtar kelimeler içeren metin. Müşteriye güven veren, atölye üretiminin doğallığını yansıtan bir dil kullan.
                    
                    **ETİKETLER (TAGS):** Tam olarak 13 adet, aralarına virgül konmuş etiket. Her bir etiket maksimum 20 karakter uzunluğunda olmalı.
                    """
                    response = model.generate_content([prompt, image])
                    st.success("İşlem Tamam!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
