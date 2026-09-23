import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import json
import os
from datetime import date, datetime

# =========================================================
# SAYFA AYARLARI
# =========================================================
st.set_page_config(page_title="meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu", page_icon="✨", layout="wide")

# =========================================================
# MODEL FALLBACK LİSTESİ
# Google modelleri sık değiştiriyor / kotaları farklı.
# İlk model 429 (kota) veya 404 (model kaldırıldı) hatası verirse,
# otomatik olarak bir sonrakine geçilir.
# =========================================================
# NOT: 3.5-flash listede önce geliyor çünkü test sürecinde güvenilir şekilde
# çalıştığı görüldü. 3.6-flash bazı isteklerde "düşünme" (thinking) bütçesini
# tüketip hiç cevap üretmeden bitirebiliyor (bilinen bir Gemini 3.x davranışı) —
# bu yüzden onu ikinci sıraya aldık, boş cevap gelirse otomatik atlanacak.
MODEL_FALLBACK_LIST = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-2.0-flash",
]

# =========================================================
# GÜNLÜK KULLANIM SAYACI (basit dosya tabanlı)
# =========================================================
COUNTER_FILE = "usage_counter.json"

def _load_counter_data():
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def get_today_count():
    data = _load_counter_data()
    return data.get(date.today().isoformat(), 0)

def increment_today_count():
    today_key = date.today().isoformat()
    data = _load_counter_data()
    data[today_key] = data.get(today_key, 0) + 1
    # sadece son 14 günü tut, dosya şişmesin
    if len(data) > 14:
        for k in sorted(data.keys())[:-14]:
            data.pop(k, None)
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)
    return data[today_key]

# =========================================================
# HAFIZA (Session State)
# =========================================================
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

# =========================================================
# YARDIMCI FONKSİYONLAR
# =========================================================
def parse_blocks(text):
    blocks = {"BASLIK": "", "ACIKLAMA": "", "ETIKETLER": "", "TR_BASLIK": "", "TR_ACIKLAMA": "", "TR_ETIKETLER": ""}
    pattern = r"\[(BASLIK|ACIKLAMA|ETIKETLER|TR_BASLIK|TR_ACIKLAMA|TR_ETIKETLER)\]"
    matches = list(re.finditer(pattern, text))
    for i, match in enumerate(matches):
        tag_name = match.group(1)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks[tag_name] = text[start_pos:end_pos].strip()
    return blocks

def clean_tags(tag_str):
    return ", ".join([t.strip()[:20] for t in tag_str.split(',') if t.strip()])

def trim_title(title, max_len=76):
    """Başlığı 76 karakteri geçmeyecek şekilde, kelime ortasından kesmeden kısaltır."""
    title = title.strip()
    if len(title) <= max_len:
        return title
    cut = title[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.strip(" ,.-")

def _build_generation_config():
    """Yüklü SDK sürümüne göre en uygun ayarı dener; desteklenmeyen parametrede
    bir alt seçeneğe sessizce düşer (versiyon farklarına karşı güvenli)."""
    attempts = []

    # 1) Thinking'i kısıp bol token payı ver (destekleniyorsa en ideali)
    try:
        attempts.append(genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=8192,
            thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
        ))
    except Exception:
        pass

    # 2) Sadece bol token payı
    try:
        attempts.append(genai.GenerationConfig(temperature=0.7, max_output_tokens=8192))
    except Exception:
        pass

    # 3) En sade hali (her SDK sürümünde çalışır)
    attempts.append(genai.GenerationConfig(temperature=0.7))

    return attempts[0]

def generate_with_fallback(prompt_parts):
    """Modeller arasında sırayla dener. Kota/kaldırılma hatasında VEYA
    modelin (thinking bütçesi yüzünden) BOŞ cevap döndürmesi durumunda
    otomatik olarak bir sonraki modele geçer."""
    last_error = None
    for model_name in MODEL_FALLBACK_LIST:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=_build_generation_config(),
            )
            response = model.generate_content(prompt_parts)
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                last_error = RuntimeError(
                    f"'{model_name}' boş cevap döndürdü (muhtemelen thinking bütçesi tükendi)."
                )
                continue  # sıradaki modele geç
            return response, model_name
        except Exception as e:
            last_error = e
            continue  # her türlü hatada sıradaki modele geç, en sona kadar dene
    raise last_error

# =========================================================
# ÜST BAŞLIK + TARİH/SAAT + GÜNLÜK SAYAÇ
# =========================================================
st.title("meymet.com | Görsel Analiziyle Ücretsiz Hızlı SEO Otomasyonu")

simdi = datetime.now()
bugun_sayac = get_today_count()
st.caption(f"📅 {simdi.strftime('%d.%m.%Y %H:%M')}  •  Bugün {bugun_sayac} kez kullanıldı")

API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

sol_sutun, sag_sutun = st.columns([1, 2], gap="large")

# =========================================================
# SOL SÜTUN
# =========================================================
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
            preview = image.copy()
            preview.thumbnail((120, 120))
            st.image(preview)
    with i2:
        ipucu = "Örn: Dünya temalı logo..." if is_digital else "Örn: Beyaz vinil çıkartma..."
        urun_tanimi = st.text_area("Bu ürün nedir? (İpucu):", placeholder=ipucu, height=100)

    focus_keyword = st.text_input(
        "🎯 Odak Anahtar Kelime (Focus Keyword):",
        placeholder="Örn: personalized dog necklace",
        help="Başlığın en başında ve açıklamanın ilk 140 karakterinde bu kelime geçecek. Etsy'de en çok aranan, ürünü en iyi tanımlayan kelimeyi yaz."
    )

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

# =========================================================
# SAĞ SÜTUN
# =========================================================
with sag_sutun:
    if uret_btn and uploaded_file is not None:
        if not focus_keyword.strip():
            st.warning("⚠️ Odak anahtar kelime girmeden de devam edebilirsin, ama başlık ve açıklama SEO açısından daha güçlü olsun istiyorsan doldurman önerilir.")

        try:
            with st.spinner("Görsel analiz ediliyor, içerikler hazırlanıyor..."):
                target_language = "ENGLISH" if is_english else "TURKISH"
                product_hint = f"\nThe user describes this product as: '{urun_tanimi}'." if urun_tanimi else ""
                focus_hint = f"\nFOCUS KEYWORD: '{focus_keyword.strip()}'." if focus_keyword.strip() else ""

                size_hint = f"\nAvailable sizes/ratios: {', '.join(st.session_state.boyutlar)}." if st.session_state.boyutlar else ""
                color_hint = f"\nAvailable colors/formats: {', '.join(st.session_state.renkler)}." if st.session_state.renkler else ""

                if is_digital:
                    base_instruction = "You are an expert Etsy SEO copywriter focusing on DIGITAL DOWNLOAD products. CRITICAL: Emphasize that this is an INSTANT DIGITAL DOWNLOAD. NO physical item will be shipped."
                else:
                    base_instruction = "You are an expert Etsy SEO copywriter and a creative artisan copywriter analyzing a handmade/custom-designed physical product."

                translation_instruction = ""
                if is_english:
                    translation_instruction = """
                    6. Translation (CRITICAL): Since the target language is ENGLISH, you MUST ALSO provide the exact TURKISH translation of your generated Title, Description, and Tags. Append them at the very end using these exact tags: [TR_BASLIK], [TR_ACIKLAMA], [TR_ETIKETLER].
                    """

                prompt = f"""
                {base_instruction}
                {product_hint}
                {focus_hint}
                {size_hint}
                {color_hint}

                === TITLE RULES ===
                - Maximum 76 characters, no exceptions.
                - The FOCUS KEYWORD must appear at the very beginning of the title.
                - The first 30 characters alone must already make it clear what the product is.
                - Write it so a human reads it naturally — this is NOT a keyword list, it's a real title.
                - Do NOT repeat the same word twice. Do NOT stuff keywords back to back.
                - Avoid generic "spammy AI title" patterns (e.g. excessive pipes "|", ALL CAPS words, redundant phrases like "Best Gift Ever Unique Special").
                - Keep it clean, simple, and readable.

                === DESCRIPTION RULES ===
                Write EXACTLY 3 paragraphs, structured as follows:
                - PARAGRAPH 1 (Product description): The FOCUS KEYWORD must appear within the first 140 characters of the whole description. Clearly and naturally explain what the product is and its main purpose. Warm, human, non-generic opening — avoid cliché AI phrases like "Elevate your space" or "Looking for the perfect gift?". Make it specific to what is visible in the uploaded reference image.
                - PARAGRAPH 2 (Technical specifications, AS A BULLET LIST): Start with one short intro sentence, then list technical details as bullet points (each line starting with "• "). Naturally include materials, sizes, and colors/formats provided by the user in these bullets. Every important word used in the tags should appear at least once somewhere across the full description.
                - PARAGRAPH 3 (Why / who should choose this, AS A BULLET LIST): Start with one short intro sentence, then list bullet points (each line starting with "• ") explaining why customers should buy this and who it's ideal for (e.g. occasions, recipients, use cases). End the LAST bullet or the line right after the bullets with one short, warm, sincere call-to-action sentence encouraging the buyer to save/favorite the listing — written naturally, not like generic marketing copy. Example tone to draw inspiration from (do not copy verbatim, write an original sentence in the same spirit): "If this little detail made you smile, save it to your favorites so you don't lose it."
                - Do NOT use keyword stuffing anywhere. Do NOT repeat the same word unnecessarily across paragraphs.

                === TAG RULES (Long-Tail SEO) ===
                - Write exactly 13 SEO tags separated by commas.
                - Use multi-word long-tail keywords, each 20 characters or less.
                - Every tag must be genuinely relevant to this specific product — no generic, randomly-generated filler tags.
                - Avoid overly competitive one-word tags; prefer natural longer phrases a real buyer would search.

                === NO HALLUCINATIONS (CRITICAL) ===
                Do NOT invent, assume, or add ANY file formats (e.g., SVG, PDF, EPS), colors, or sizes that are not explicitly provided by the user in the lists above. If the user did not specify a format, DO NOT mention one.
                {translation_instruction}

                FORMAT STRICTLY AS FOLLOWS (DO NOT add any conversational text outside these tags):
                [BASLIK]
                ...
                [ACIKLAMA]
                ...
                [ETIKETLER]
                ...
                """

                response, used_model = generate_with_fallback([prompt, image])
                blocks = parse_blocks(response.text)

                if blocks["BASLIK"]:
                    blocks["BASLIK"] = trim_title(blocks["BASLIK"].title())

                if is_english and blocks["TR_BASLIK"]:
                    blocks["TR_BASLIK"] = trim_title(blocks["TR_BASLIK"].title())

                blocks["ETIKETLER"] = clean_tags(blocks["ETIKETLER"])
                if blocks["TR_ETIKETLER"]:
                    blocks["TR_ETIKETLER"] = clean_tags(blocks["TR_ETIKETLER"])

                if ekstra_not:
                    note_prefix_en = "**Note:** " if is_english else "**Not:** "
                    blocks["ACIKLAMA"] += f"\n\n---\n{note_prefix_en}{ekstra_not}"
                    if is_english and blocks["TR_ACIKLAMA"]:
                        blocks["TR_ACIKLAMA"] += f"\n\n---\n**Not:** {ekstra_not}"

                yeni_sayac = increment_today_count()

                st.info("💡 Yapay zeka aracılığıyla yüklediğiniz görsel analiz edilerek oluşturulan ürün bilgileri otomasyonudur. Lütfen kullanmadan önce okuyarak gerekli revize işlemlerinden sonra içerikleri uygulayınız.")
                st.caption(f"🔧 Kullanılan model: `{used_model}`  •  Bugünkü toplam kullanım: {yeni_sayac}  •  Başlık uzunluğu: {len(blocks['BASLIK'])}/76")

                if is_english and blocks["TR_BASLIK"]:
                    tab1, tab2 = st.tabs(["🇬🇧 İngilizce (Orijinal)", "🇹🇷 Türkçe Çevirisi (Kontrol İçin)"])

                    with tab1:
                        st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                        st.text_area("Açıklama", blocks["ACIKLAMA"], height=300, label_visibility="collapsed")
                        st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")

                    with tab2:
                        st.text_area("TR Başlık", blocks["TR_BASLIK"], label_visibility="collapsed")
                        st.text_area("TR Açıklama", blocks["TR_ACIKLAMA"], height=300, label_visibility="collapsed")
                        st.text_area("TR Etiketler", blocks["TR_ETIKETLER"], label_visibility="collapsed")
                else:
                    st.text_area("Başlık", blocks["BASLIK"], label_visibility="collapsed")
                    st.text_area("Açıklama", blocks["ACIKLAMA"], height=300, label_visibility="collapsed")
                    st.text_area("Etiketler", blocks["ETIKETLER"], label_visibility="collapsed")

        except Exception as e:
            st.error(f"Bir hata oluştu. Lütfen birkaç saniye bekleyip tekrar deneyin. Hata detayları: {str(e)}")

    elif not uploaded_file:
        st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
