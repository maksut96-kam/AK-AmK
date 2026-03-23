st.markdown("---")
    st.subheader("🚀 Мониторинг ротаций (АК / AmK)")
    
    # Словари пиктограмм
    P_ICONS = {
        'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 
        'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'
    }
    Z_ICONS = {
        "Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", 
        "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", 
        "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"
    }

    def get_full_info(row):
        """Вспомогательная функция для красивого вывода в ротации"""
        nak_idx = int(row['Lon'] / (360/27)) % 27
        nak = NAKSHATRAS[nak_idx]
        sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
        p_name = row['Planet']
        return f"{P_ICONS.get(p_name, p_name)} | {Z_ICONS.get(sign, sign)} | ☸️ {nak}"

    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    col1, col2 = st.columns(2)

    with col1:
        st.write("⬅️ **Предыдущая смена:**")
        found_prev = False
        for m in range(1, 2880, 10):
            past_time = now - timedelta(minutes=m)
            t_p = ts.utc(past_time.year, past_time.month, past_time.day, past_time.hour, past_time.minute)
            df_p, _ = get_planet_data(t_p)
            if df_p.iloc[0]['Planet'] != ak_now or df_p.iloc[1]['Planet'] != amk_now:
                dt_p = (past_time + timedelta(hours=3))
                st.warning(f"📅 {dt_p.strftime('%d.%m.%Y %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_p.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_p.iloc[1])}")
                found_prev = True
                break
        if not found_prev: st.write("Не найдено")

    with col2:
        st.write("➡️ **Следующая смена:**")
        found_next = False
        for m in range(1, 2880, 10):
            future_time = now + timedelta(minutes=m)
            t_f = ts.utc(future_time.year, future_time.month, future_time.day, future_time.hour, future_time.minute)
            df_f, _ = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
                dt_f = (future_time + timedelta(hours=3))
                st.success(f"📅 {dt_f.strftime('%d.%m.%Y %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_f.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_f.iloc[1])}")
                found_next = True
                break
        if not found_next: st.write("Не найдено")

    st.markdown("---")
    st.info(f"💎 **Текущий активный период:**")
    c_ak, c_amk = st.columns(2)
    c_ak.metric("Текущая АК", get_full_info(df.iloc[0]))
    c_amk.metric("Текущая AmK", get_full_info(df.iloc[1]))
