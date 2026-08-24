import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Etsy Asistanım", page_icon="✨", layout="wide")

# --- Hafıza (Session State) ---
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
    
    # YENİLİK 1: Temperature ayarını 0.9 yaparak yapay zekanın yaratıcılığını ve kelime çeşitliliğini artırdık
    model = genai.GenerativeModel(
        model_name='gemini-3.5-flash',
        generation_config=genai.GenerationConfig(temperature=0.9)
    )

    sol_sutun, sag_sutun = st.columns([1, 2], gap="large")

    # ================= SOL SÜTUN =================
    with sol_sutun:
        st.header("1. Yükleme & Ayarlar")
        
        uploaded_file = st.file_uploader("Ürün Görselini Yükle (JPG, PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            image.thumbnail((150, 150))
            st.image(image, caption="Yüklenen Görsel")
            
        st.markdown("---")
        
        # YENİLİK 2: Yapay zekaya ipucu vermek için "Ürün Nedir?" alanı eklendi
        urun_tanimi = st.text_input("Bu ürün nedir? (Yapay zekaya ufak bir ipucu verin):", placeholder="Örn: Gelin arabası için beyaz vinil çıkartma...")
        
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

    # ================= SAĞ SÜTUN =================
    with sag_sutun:
        st.header("2. Üretilen İçerikler")
        
        if uret_btn and uploaded_file is not None:
            with st.spinner(f"Görsel analiz ediliyor, {dil} dilinde içerikler yazılıyor..."):
                try:
                    # İngilizce komutlar için dinamik değişkenleri hazırlıyoruz
                    target_language = "ENGLISH" if dil == "İngilizce" else "TURKISH"
                    
                    product_hint = f"\nThe user describes this product as: '{urun_tanimi}'." if urun_tanimi else ""
                    
                    size_hint = ""
                    if len(st.session_state.boyutlar) > 0:
                        size_hint = f"\nThe available size variants are: {', '.join(st.session_state.boyutlar)}. Include these sizes as a clear list in the description."

                    # YENİLİK 3: Tamamen İngilizce, kesin kurallı ve yaratıcılığa zorlayan Prompt
                    prompt = f"""
                    You are an expert e-commerce SEO specialist and a highly creative copywriter. Analyze the provided image of a handmade/custom-designed product.
                    {product_hint}
                    {size_hint}
                    
                    CRITICAL INSTRUCTIONS:
                    1. Output Language: You MUST write the ENTIRE output (Title, Description, Tags) in {target_language}.
                    2. Creativity & Variety: Do NOT use generic, repetitive boilerplate phrases. Craft a unique, engaging, and heartfelt story for the description. Use diverse vocabulary and vary your sentence structures to ensure the text stands out.
                    3. Tone: Warm, trustworthy, highlighting the handmade/workshop nature of the item.
                    4. Strict Format: You MUST use the exact bracketed tags below to separate the sections. Do not add any conversational filler before or after.

                    [BASLIK]
                    Write a highly clickable, SEO-optimized e-commerce title here.

                    [ACIKLAMA]
                    Write the engaging, unique, and SEO-friendly description here.

                    [ETIKETLER]
                    Write exactly 13 SEO tags separated by commas. STRICT REQUIREMENT: EACH INDIVIDUAL TAG MUST BE 20 CHARACTERS OR LESS.
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    sonuc = response.text
                    baslik = sonuc.split("[ACIKLAMA]")[0].replace("[BASLIK]", "").strip()
                    kalan = sonuc.split("[ACIKLAMA]")[1]
                    aciklama = kalan.split("[ETIKETLER]")[0].strip()
                    ham_etiketler = kalan.split("[ETIKETLER]")[1].strip()

                    # 20 Karakter Güvenlik Filtresi (Makas)
                    temiz_etiketler = []
                    for etiket in ham_etiketler.split(','):
                        etiket = etiket.strip()
                        if len(etiket) > 20:
                            etiket = etiket[:20]
                        temiz_etiketler.append(etiket)
                    son_etiketler = ", ".join(temiz_etiketler)

                    if ekstra_not:
                        aciklama += f"\n\n---\n**Not:** {ekstra_not}"

                    st.subheader("📌 Başlık")
                    st.text_area("Başlık", baslik, label_visibility="collapsed")
                    
                    st.subheader("📖 Açıklama")
                    st.text_area("Açıklama", aciklama, height=250, label_visibility="collapsed")
                    
                    st.subheader("🏷️ Etiketler")
                    st.text_area("Etiketler", son_etiketler, label_visibility="collapsed")
                        
                    st.success("İşlem Tamam! Kutuların içine tıklayıp metni kolayca kopyalayabilirsiniz.")

                except Exception as e:
                    st.error("Bir hata oluştu. Lütfen görseli ve ayarları kontrol edip tekrar deneyin.")
        
        elif not uploaded_file:
            st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
