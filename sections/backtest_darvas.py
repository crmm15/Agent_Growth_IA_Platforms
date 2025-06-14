    # … después de descargar y preparar df_hist …

    # 4) ═════════ Tabla de históricos ═══════════════════════════════
    df_hist = df.copy().reset_index().rename(columns={"index":"Date"})
    df_hist["Date"] = pd.to_datetime(df_hist["Date"]).dt.tz_localize(None)

    st.dataframe(
        df_hist,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date":   st.column_config.DateColumn("Fecha",     format="DD-MM-YYYY"),
            "Open":   st.column_config.NumberColumn("Apertura", format=",.2f"),
            "High":   st.column_config.NumberColumn("Máximo",   format=",.2f"),
            "Low":    st.column_config.NumberColumn("Mínimo",   format=",.2f"),
            "Close":  st.column_config.NumberColumn("Cierre",   format=",.2f"),
            "Volume": st.column_config.NumberColumn("Volumen",  format="0,"),
        }
    )

    # … aquí calculas señales y generas df_signals …

    # 11) ═════════ Tabla de señales ════════════════════════════════
    df_signals["Date"] = pd.to_datetime(df_signals["Date"]).dt.tz_localize(None)

    st.dataframe(
        df_signals,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date":          st.column_config.DateColumn("Fecha",       format="DD-MM-YYYY"),
            "Close":         st.column_config.NumberColumn("Cierre",     format=",.2f"),
            "darvas_high":   st.column_config.NumberColumn("Darvas High",format=",.2f"),
            "darvas_low":    st.column_config.NumberColumn("Darvas Low", format=",.2f"),
            "mavilimw":      st.column_config.NumberColumn("MavilimW",   format=",.2f"),
            "wae_trendUp":   st.column_config.NumberColumn("WAE↑",       format=",.2f"),
            "wae_e1":        st.column_config.NumberColumn("Explosión",  format=",.2f"),
            "wae_deadzone":  st.column_config.NumberColumn("DeadZone",   format=",.2f"),
            "wae_trendDown": st.column_config.NumberColumn("WAE↓",       format=",.2f"),
        }
    )
