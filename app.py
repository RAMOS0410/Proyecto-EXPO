# --- 4. CATÁLOGO Y TRATAMIENTOS (CULTIVOS DE EL SALVADOR) ---
    elif opcion == "Catálogo y Tratamientos":
        st.title("Catálogo de Soluciones")
        st.caption("Tratamientos orgánicos y biológicos diseñados para los principales cultivos de El Salvador.")
        
        # Pestañas estructuradas por los cultivos más comunes de El Salvador
        tab_maiz, tab_frijol, tab_cafe, tab_cana = st.tabs(["🌽 Maíz", "🫘 Frijol", "☕ Café", "🌾 Caña de Azúcar"])
        
        # --- CULTIVO 1: MAÍZ ---
        with tab_maiz:
            st.subheader("Soluciones para Maíz (Milpa)")
            
            # Producto 1
            col_img1, col_info1 = st.columns([1, 2])
            with col_img1:
                st.image("https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=400", caption="TRICHO-MAÍZ", use_container_width=True)
            with col_info1:
                st.markdown("### TRICHO-MAÍZ: Control Foliar y de Raíz")
                st.caption("FUNGICIDA BIOLÓGICO (Trichoderma)")
                st.write("""
                * Controla el achaparramiento y el hongo del carbón de la espiga.
                * Protege la raíz contra podredumbre por exceso de lluvia.
                * **100% Orgánico y amigable con el suelo.**
                """)
                st.markdown("**Precio:** $10.00 USD")
                st.button("Solicitar Información", key="btn_maiz1")
            
            st.write("---")
            
            # Producto 2
            col_img2, col_info2 = st.columns([1, 2])
            with col_img2:
                st.image("https://images.unsplash.com/photo-1628771065518-0d82f1938462?w=400", caption="BIO-MAÍZ NUTRICIÓN", use_container_width=True)
            with col_info2:
                st.markdown("### BIO-MAÍZ NUTRICIÓN")
                st.caption("FERTILIZANTE BIOESTIMULANTE CON AMINOÁCIDOS")
                st.write("""
                * Estimula el llenado completo de la elotera.
                * Incrementa la resistencia durante el periodo de canícula.
                * Mejora la absorción de nutrientes del suelo salvadoreño.
                """)
                st.markdown("**Precio:** $13.00 USD")
                st.button("Solicitar Información", key="btn_maiz2")

        # --- CULTIVO 2: FRIJOL ---
        with tab_frijol:
            st.subheader("Soluciones para Frijol Rojo")
            
            # Producto 1
            col_img1, col_info1 = st.columns([1, 2])
            with col_img1:
                st.image("https://images.unsplash.com/photo-1592417817098-8f3d6ef23a81?w=400", caption="RHIZO-FRIJOL", use_container_width=True)
            with col_info1:
                st.markdown("### RHIZO-FRIJOL: Inoculante de Nitrógeno")
                st.caption("INOCULANTE BACTERIANO (Rhizobium)")
                st.write("""
                * Captura el nitrógeno del aire y lo fija en la tierra.
                * Aumenta el engorde del grano de frijol rojo.
                * Fortalece la planta ante variaciones de humedad.
                """)
                st.markdown("**Precio:** $13.00 USD")
                st.button("Solicitar Información", key="btn_frijol1")
                
            st.write("---")
            
            # Producto 2
            col_img2, col_info2 = st.columns([1, 2])
            with col_img2:
                st.image("https://images.unsplash.com/photo-1615811361523-6bd03d7748e7?w=400", caption="BEAUVERIA-FRIJOL", use_container_width=True)
            with col_info2:
                st.markdown("### BEAUVERIA-FRIJOL: Manejo de Plagas")
                st.caption("INSECTICIDA BIOLÓGICO PARA ÁFIDOS Y MOSCA BLANCA")
                st.write("""
                * Control de la mosca blanca transmisora del mosaico dorado.
                * Previene plagas de ácaros y chinche verde.
                * No tóxico para polinizadores ni animales de granja.
                """)
                st.markdown("**Precio:** $12.00 USD")
                st.button("Solicitar Información", key="btn_frijol2")

        # --- CULTIVO 3: CAFÉ ---
        with tab_cafe:
            st.subheader("Soluciones para Café de Cordillera")
            
            # Producto 1
            col_img1, col_info1 = st.columns([1, 2])
            with col_img1:
                st.image("https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400", caption="NATURE-CAFÉ", use_container_width=True)
            with col_info1:
                st.markdown("### NATURE-CAFÉ: Control de Broca y Roya")
                st.caption("INSECTICIDA Y FUNGICIDA MICROBIANO (Beauveria y Bacillus)")
                st.write("""
                * Elimina la Broca del Café y frena la difusión de Roya.
                * Protege las zonas cafetaleras sin contaminar mantos acuíferos.
                * Ideal para fincas de café orgánico y de altura.
                """)
                st.markdown("**Precio:** $120.00 USD")
                st.button("Solicitar Información", key="btn_cafe1")
                
            st.write("---")
            
            # Producto 2
            col_img2, col_info2 = st.columns([1, 2])
            with col_img2:
                st.image("https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=400", caption="ORGA-CAFÉ FOLIARE", use_container_width=True)
            with col_info2:
                st.markdown("### ORGA-CAFÉ FOLIARE")
                st.caption("NUTRIENTE FOLIAR A BASE DE ALGAS MARINAS")
                st.write("""
                * Favorece la maduración uniforme de las uvas de café.
                * Evita la caída prematura del fruto por viento o lluvia.
                * Aumenta la densidad y sabor de la taza.
                """)
                st.markdown("**Precio:** $50.00 USD")
                st.button("Solicitar Información", key="btn_cafe2")

        # --- CULTIVO 4: CAÑA DE AZÚCAR ---
        with tab_cana:
            st.subheader("Soluciones para Caña de Azúcar")
            
            # Producto 1
            col_img1, col_info1 = st.columns([1, 2])
            with col_img1:
                st.image("https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=400", caption="BIO-CAÑA BARRENADOR", use_container_width=True)
            with col_info1:
                st.markdown("### BIO-CAÑA: Control de Barrenador")
                st.caption("INSECTICIDA BIOLÓGICO (Trichogramma & Metarhizium)")
                st.write("""
                * Combate el gusano barrenador del tallo en la caña.
                * Mantiene la pureza y los grados Brix de la sacarosa.
                * Aplicable de forma manual o con dron agrícola.
                """)
                st.markdown("**Precio:** $35.00 USD")
                st.button("Solicitar Información", key="btn_cana1")
                
            st.write("---")
            
            # Producto 2
            col_img2, col_info2 = st.columns([1, 2])
            with col_img2:
                st.image("https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=400", caption="CAÑA-MAX RAÍZ", use_container_width=True)
            with col_info2:
                st.markdown("### CAÑA-MAX: Nutrición y Enraizamiento")
                st.caption("BIOESTIMULANTE DE DESARROLLO")
                st.write("""
                * Promueve el brote rápido del socollón después de la zafra.
                * Maximiza el grosor y altura del tallo.
                * Fortalece la cepa para ciclos de corte más prolongados.
                """)
                st.markdown("**Precio:** $28.00 USD")
                st.button("Solicitar Información", key="btn_cana2")