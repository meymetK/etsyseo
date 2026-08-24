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
                    Buraya 13 adet, aralarına virgül konmuş etiket. (KESİNLİKLE HER BİR ETİKET EN FAZLA 20 KARAKTER OLMALIDIR).
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
                            etiket = etiket[:20] # 20'den uzunsa kes
                        temiz_etiketler.append(etiket)
                    son_etiketler = ", ".join(temiz_etiketler)

                    if ekstra_not:
                        aciklama += f"\n\n---\n**Not:** {ekstra_not}"

                    # Sonuçları okunaklı metin kutularında gösteriyoruz
                    st.subheader("📌 Başlık")
                    st.text_area("Başlık", baslik, label_visibility="collapsed")
                    
                    st.subheader("📖 Açıklama")
                    st.text_area("Açıklama", aciklama, height=250, label_visibility="collapsed")
                    
                    st.subheader("🏷️ Etiketler")
                    st.text_area("Etiketler", son_etiketler, label_visibility="collapsed")
                        
                    st.success("İşlem Tamam! Kutuların içine tıklayıp metni kolayca kopyalayabilirsiniz.")

                except Exception as e:
                    st.error("Bir hata oluştu veya yapay zeka metni doğru formatta bölmedi. Lütfen tekrar deneyin.")
        
        elif not uploaded_file:
            st.info("👈 Önce sol taraftan ürün görselini yükleyin ve ayarlarınızı yapın.")
