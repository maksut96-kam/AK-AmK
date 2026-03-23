with tab1:
    if st.button('🔄 Обновить расчет планет'):
        st.cache_data.clear()

    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df, ayan_val = get_planet_data(t_now)
    
    st.info(f"ℹ️ **Текущая Айанамша Лахири (динамическая):** {format_deg_to_min(ayan_val)}")
    
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x / (360/27)) % 27])
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])
    
    st.markdown("---")
    st.subheader("🚀 Мониторинг ротаций (АК / AmK)")
    
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    col1, col2 = st.columns(2)

    # --- ПОИСК ПРЕДЫДУЩЕЙ РОТАЦИИ (назад на 24 часа) ---
    with col1:
        st.write("⬅️ **Предыдущая смена:**")
        found_prev = False
        for m in range(1, 1440, 5):
            past_time = now - timedelta(minutes=m)
            t_p = ts.utc(past_time.year, past_time.month, past_time.day, past_time.hour, past_time.minute)
            df_p, _ = get_planet_data(t_p)
            if df_p.iloc[0]['Planet'] != ak_now or df_p.iloc[1]['Planet'] != amk_now:
                dt_p = (past_time + timedelta(hours=3))
                st.warning(f"{dt_p.strftime('%d.%m.%Y %H:%M')}")
                st.caption(f"Было: АК {df_p.iloc[0]['Planet']} / AmK {df_p.iloc[1]['Planet']}")
                found_prev = True
                break
        if not found_prev: st.write("Не найдено в пределах 24ч")

    # --- ПОИСК СЛЕДУЮЩЕЙ РОТАЦИИ (вперед на 24 часа) ---
    with col2:
        st.write("➡️ **Следующая смена:**")
        found_next = False
        for m in range(1, 1440, 5):
            future_time = now + timedelta(minutes=m)
            t_f = ts.utc(future_time.year, future_time.month, future_time.day, future_time.hour, future_time.minute)
            df_f, _ = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
                dt_f = (future_time + timedelta(hours=3))
                st.success(f"{dt_f.strftime('%d.%m.%Y %H:%M')}")
                st.caption(f"Будет: АК {df_f.iloc[0]['Planet']} / AmK {df_f.iloc[1]['Planet']}")
                found_next = True
                break
        if not found_next: st.write("Не найдено в пределах 24ч")

    st.info(f"💎 **Текущий активный период:** АК {ak_now} / AmK {amk_now}")
