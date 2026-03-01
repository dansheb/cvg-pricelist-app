"""
CVG PriceList Worker — Streamlit App
Главная страница: генерация прайс-листа.
"""
import streamlit as st

st.set_page_config(
    page_title="CVG PriceList Worker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Инициализация конфигурации в session_state ───────────────────────────────

DEFAULT_CONFIG = {
    "xml_url": "https://www.cvg.ru/xml/CVGAUDIO_DEALER_pricelist.xml",
    "settings_sheet_id": "10Zvm5aJ2yy4AXuVpQYTK_XKKy6680Ub3u42eoLvZ3Bg",
    "cuts_sheet_id": "1TnS6bF_X1hXZduf2miWdFP7tmXXIHNE98gXZXYjx7co",
    "vi_sheet_id": "1lt-APdCurjXxJ9H6zAsDtaYS1wtfXA4M",
    "dealer_margin": 0.25,
    "wb_margin": 0.17,
    "vi_coefficient": 1.25,
}

if "config" not in st.session_state:
    st.session_state.config = DEFAULT_CONFIG.copy()

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "history" not in st.session_state:
    st.session_state.history = []


# ── UI ───────────────────────────────────────────────────────────────────────

st.title("CVG PriceList Worker")
st.caption("Генерация прайс-листов CVGAUDIO / PROCAST cable")

st.divider()

# Статус подключения
cfg = st.session_state.config
with st.expander("Текущая конфигурация", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**XML URL:** `{cfg['xml_url'][:60]}...`")
        st.markdown(f"**Settings Sheet:** `{cfg['settings_sheet_id'][:20]}...`")
        st.markdown(f"**Обрезки Sheet:** `{cfg['cuts_sheet_id'][:20]}...`")
    with col2:
        st.markdown(f"**Прикат ВИ Sheet:** `{cfg['vi_sheet_id'][:20]}...`")
        st.markdown(f"**Маржа дилера:** {cfg['dealer_margin']*100:.0f}%")
        st.markdown(f"**Маржа WB:** {cfg['wb_margin']*100:.0f}%")
        st.markdown(f"**Коэфф. ВИ:** {cfg['vi_coefficient']}")

st.divider()

# Кнопка генерации
if st.button("Генерировать прайс-лист", type="primary", use_container_width=True):
    from logic import run_pipeline

    log_container = st.container()
    progress_bar = st.progress(0, text="Запуск...")
    steps_total = 9
    step_count = [0]

    def on_progress(msg):
        step_count[0] += 1
        pct = min(step_count[0] / steps_total, 1.0)
        progress_bar.progress(pct, text=msg)

    try:
        result = run_pipeline(cfg, progress_callback=on_progress)
        progress_bar.progress(1.0, text="Готово!")

        st.session_state.last_result = result
        st.session_state.history.insert(0, {
            "date": result["date"],
            "pricelist_bytes": result["pricelist_bytes"],
            "prikat_bytes": result["prikat_bytes"],
            "items": len(result["final_df"]),
        })

        # Лог
        with log_container.expander("Лог выполнения", expanded=False):
            for line in result["log"]:
                st.text(line)

    except Exception as e:
        progress_bar.empty()
        st.error(f"Ошибка: {e}")
        st.exception(e)

# Результаты
if st.session_state.last_result:
    res = st.session_state.last_result
    st.subheader("Результаты")

    col1, col2, col3 = st.columns(3)
    col1.metric("Дата прайса", res["date"])
    col2.metric("Позиций", len(res["final_df"]))
    col3.metric("Файлы", "2" if res["prikat_bytes"] else "1")

    st.divider()

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label=f"Скачать {res['date']} Прайс Лист.xlsx",
            data=res["pricelist_bytes"],
            file_name=f"{res['date']} Прайс Лист.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with dl2:
        if res["prikat_bytes"]:
            st.download_button(
                label=f"Скачать {res['date']} Прикат_ЛК_ВсеИнструменты.xlsx",
                data=res["prikat_bytes"],
                file_name=f"{res['date']} Прикат_ЛК_ВсеИнструменты.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.warning("Прикат ВИ не сформирован (см. лог)")

    # Превью данных
    with st.expander("Превью прайс-листа", expanded=False):
        st.dataframe(res["final_df"].head(50), use_container_width=True)

# История
if st.session_state.history:
    st.divider()
    st.subheader("История генераций")
    for i, h in enumerate(st.session_state.history[:10]):
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1, 3, 3])
            c1.write(f"**{h['date']}**")
            c2.write(f"{h['items']} поз.")
            with c3:
                st.download_button(
                    "Прайс",
                    h["pricelist_bytes"],
                    f"{h['date']} Прайс Лист.xlsx",
                    key=f"hist_pl_{i}",
                )
            with c4:
                if h["prikat_bytes"]:
                    st.download_button(
                        "Прикат ВИ",
                        h["prikat_bytes"],
                        f"{h['date']} Прикат_ЛК_ВсеИнструменты.xlsx",
                        key=f"hist_vi_{i}",
                    )
