import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# Sayfa Ayarları
st.set_page_config(page_title="meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu", page_icon="✨", layout="wide")

# --- Hafıza (Session State) ---
if "boyutlar" not in st.session_state:
    st.session_state.boyutlar = []
if "renkler" not in st.session_state:
    st.session_state.renkler = []

def boyut_ekle():
    val = st.session_state.boyut_input.strip()
    if val and val not in st.session_state.boyutlar:
        st.session_state.boyutlar.append(val)
    st.session_state.boyut_input = "" 

def renk_ekle():
    val = st.session_state.renk_input.strip()
    if val and val not in st.session_state.renkler:
        st.session_state.renkler.append(val)
    st.session_state.renk_input = ""

def parse_blocks(text):
    blocks = {"BASLIK": "", "ACIKLAMA": "", "ETIKETLER": "", "TR_BASLIK": "", "TR_ACIKLAMA": "", "TR_ETIKETLER": ""}
    pattern = r"\[(BASLIK|ACIKLAMA|ETIKETLER|TR_BASLIK|TR_ACIKLAMA|TR_ETIKETLER)\]"
    matches = list(re.finditer(pattern, text))
    for i, match in enumerate(matches):
        tag_name = match.group(1)
        start_pos = match.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
        blocks[tag_name] = text[start_pos:end_pos].strip()
    return blocks

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
                st.error("Yanlış şifre, tekrar dene!")
        return False
    return True

if check_password():
    st.title("meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu")
    
    API_KEY = st.secrets["GEMINI_API_KEY"] 
    genai.configure(api_key=API_KEY)
    
    model = genai.GenerativeModel(
        model_name='gemini-3.5-flash',
        generation_config=genai.GenerationConfig(temperature=0.9)
    )

    sol_sutun, sag_sutun = st.columns([1, 2], gap="large")

    # ================= SOL SÜTUN =================
    with sol_sutun:
        r1, r2 = st.columns(2)
        with r1:
            urun_tipi_secimi = st.radio("📦 Ürün Tipi:", ["Fiziksel Ürün", "Dijital İndirme"])
            is_digital = "Dijital" in urun_tipi_secimi
        with r2:
            dil_secimi = st.radio("🌍 Hedef Pazar / Dil", ["İngilizce", "Türkçe"])
            is_english = "İngilizce" in dil_secimi

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

        i1, i2 = st.columns([1, 2])
        with i1:
            uploaded_file = st.file_uploader("Görsel Yükle", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                image.thumbnail((120, 120))
                st.image(image)
        with i2:
            ipucu = "Örn: Dünya temalı logo..." if is_digital else "Örn: Beyaz vinil çıkartma..."
            urun_tanimi = st.text_area("Bu ürün nedir? (İpucu):", placeholder=ipucu, height=100)
        
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        
        col_b_input, col_b_list = st.columns(2)
        with col_b_input:
            boyut_lbl = "Format/Oran (Enter'a bas):" if is_digital else "Ebat/Boyut (Enter'a bas):"
            st.text_input(boyut_lbl, key="boyut_input", on_change=boyut_ekle)
        with col_b_list:
            st.caption("Eklenenler:")
            for item in st.session_state.boyutlar:
                c_text, c_btn = st.columns([4, 1])
                c_text.write(f"▪️ {item}")
                if c_btn.button("❌", key=f"del_b_{item}"):
                    st.session_state.boyutlar.remove(item)
                    st.rerun()

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

        col_r_input, col_r_list = st.columns(2)
        with col_r_input:
            renk_lbl = "Dosya Türü (Enter'a bas):" if is_digital else "Renk Seçeneği (Enter'a bas):"
            st.text_input(renk_lbl, key="renk_input", on_change=renk_ekle)
        with col_r_list:
            st.caption("Eklenenler:")
            for item in st.session_state.renkler:
                c_text, c_btn = st.columns([4, 1])
                c_text.write(f"▪️ {item}")
                if c_btn.button("❌", key=f"del_r_{item}"):
                    st.session_state.renkler.remove(item)
                    st.rerun()

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        
        ekstra_not = st.text_area("Ekstra Not (Opsiyonel):", height=60)
        
        uret_btn = st.button("✨ İçerikleri Üret", type="primary", use_container_width=True)

    # ================= SAĞ SÜTUN =================
    with sag_sutun:
        if uret_btn and uploaded_file is not None:
            with st.spinner("Görsel analiz ediliyor, harika içerikler yazılıyor..."):
                try:
                    target_language = "ENGLISH" if is_english else "TURKISH"
                    product_hint = f"\nThe user describes this product as: '{urun_tanimi}'." if urun_tanimi else ""
                    
                    size_hint = f"\nAvailable sizes/ratios: {', '.join(st.session_state.boyutlar)}." if st.session_state.boyutlar else ""
                    color_hint = f"\nAvailable colors/formats: {', '.join(st.session_state.renkler)}." if st.session_state.renkler else ""

                    if is_digital:
                        base_instruction = "You are an expert e-commerce SEO specialist focusing on DIGITAL DOWNLOAD products. CRITICAL: Emphasize that this is an INSTANT DIGITAL DOWNLOAD. NO physical item will be shipped."
                    else:
                        base_instruction = "You are an expert e-commerce SEO specialist and a creative artisan copywriter analyzing a handmade/custom-designed physical product."

                    translation_instruction = ""
                    if is_english:
                        translation_instruction = """
                        5. Translation (CRITICAL): Since the target language is ENGLISH, you MUST ALSO provide the exact TURKISH translation of your generated Title, Description, and Tags. Append them at the very end using these exact tags: [TR_BASLIK], [TR_ACIKLAMA], [TR_ETIKETLER].
                        """

                    # YENİ KURAL: "4. NO HALLUCINATIONS" kuralı eklendi.
                    prompt = f"""
                    {base_instruction}
                    {product_hint}
                    {size_hint}
                    {color_hint}
                    
                    CRITICAL INSTRUCTIONS:
                    1. Output Language: You MUST write the output in {target_language}.
                    2. Description Rules (AVOID COOKIE-CUTTER TEMPLATES):
                       - PARAGRAPH 1 (The Hook): Write a warm, sensory-rich, emotional opening that hooks the reader. Tell a miniature story about why this item is special.
                       - PARAGRAPH 2 & 3: Detail the features, craftsmanship, or digital quality. Vary your sentence lengths. Be persuasive, natural, and friendly. Include the size/color options naturally or as a clean list.
                    3. Tag Rules (Long-Tail SEO): Write exactly 13 SEO tags separated by commas. Use multi-word long-tail keywords. EACH TAG MUST BE 20 CHARACTERS OR LESS.
                    4. NO HALLUCINATIONS (CRITICAL): DO NOT invent, assume, or add ANY file formats (e.g., SVG, PDF, EPS), colors, or sizes that are not explicitly provided by the user in the lists above. If the user did not specify a format, DO NOT mention one.
                    {translation_instruction}
                    
                    FORMAT STRICTLY AS FOLLOWS (DO NOT add any conversational text outside these tags):
                    [BASLIK]
                    ...
                    [ACIKLAMA]
                    ...
                    [ETIKETLER]
                    ...
                    """
                    
                    response = model.generate_content([prompt, image])
                    blocks = parse_blocks(response.text)

                    if blocks["BASLIK"]:
                        blocks["BASLIK"] = blocks["BASLIK"].title()
                    
                    if is_english and blocks["TR_BASLIK"]:
                        blocks["TR_BASLIK"] = blocks["TR_BASLIK"].title()

                    def clean_tags(tag_str):
                        return ", ".join([t.strip()[:20] for t in tag_str.split(',') if t.strip()])
                    
                    blocks["ETIKETLER"] = clean_tags(blocks["ETIKETLER"])
                    if blocks["TR_ETIKETLER"]:
                        blocks["TR_ETIKETLER"] = clean_tags(blocks["TR_ETIKETLER"])

                    if ekstra_not:
                        note_prefix_en = "**Note:** " if is_english else "**Not:** "
                        blocks["ACIKLAMA"] += f"\n\n---\n{note_prefix_en}{ekstra_not}"
                        if is_english and blocks["TR_ACIKLAMA"]:
                            blocks["TR_ACIKLAMA"] += f"\n\n---\n**Not:** {ekstra_not}"

                    st.info("💡 Yapay zeka aracılığıyla yüklediğiniz görsel analiz edilerek oluşturulan ürün bilgileri otomasyonudur. Lütfen kullanmadan önce okuyarak gerekli revize işlemlerinden sonra içerikleri uygulayınız.")

                    if is_english and blocks["TR_BASLIK"]:
                        tab1, tab2 = st.tabs(["🇬🇧 İngilizce (Orijinal)", "🇹🇷 Türkçe Çevirisi (Kontrol İçin)"])
                        
                        with tab1:
                            st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                            st.text_area("Açıklama", blocks["ACIKLAMA"], height=250, label_visibility="collapsed")
                            st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")
                            
                        with tab2:
                            st.text_area("TR Başlık", blocks["TR_BASLIK"], label_visibility="collapsed")
                            st.text_area("TR Açıklama", blocks["TR_ACIKLAMA"], height=250, label_visibility="collapsed")
                            st.text_area("TR Etiketler", blocks["TR_ETIKETLER"], label_visibility="collapsed")
                    else:
                        st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                        st.text_area("Açıklama", blocks["ACIKLAMA"], height=250, label_visibility="collapsed")
                        st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")

                except Exception as e:
                    st.error(f"Bir hata oluştu. Hata: {e}")
        
        elif not uploaded_file:
            st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
