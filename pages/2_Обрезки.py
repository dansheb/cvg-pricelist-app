"""
Страница обрезков — просмотр и редактирование обрезков со склада Балтийская.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Обрезки", page_icon="✂️", layout="wide")

# ── Инициализация ────────────────────────────────────────────────────────────

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

cfg = st.session_state.config

st.title("Обрезки — склад Балтийская")
st.caption("Остатки кабелей на складе Балтийская (Google Sheets)")

# ── Загрузка ─────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 3])
with col1:
    load_btn = st.button("Загрузить из Google Sheets", use_container_width=True)
with col2:
    st.caption(f"Sheet ID: `{cfg['cuts_sheet_id'][:20]}...`")

if load_btn:
    try:
        from logic import read_gsheet
        df = read_gsheet(cfg["cuts_sheet_id"], "CutsLeftover")
        # Убираем пробелы в начале названия столбца
        df.columns = [c.strip() for c in df.columns]
        st.session_state["cuts_df"] = df
        st.success(f"Загружено {len(df)} обрезков")
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")

# ── Отображение ──────────────────────────────────────────────────────────────

if "cuts_df" in st.session_state:
    df = st.session_state["cuts_df"]

    # Статистика
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Всего обрезков", len(df))
    col2.metric("Уникальных артикулов", df["Артикул"].nunique())
    col3.metric("Общая длина, м", f"{df['Остаток'].sum():.0f}")

    # Сводка по артикулам
    st.divider()
    st.subheader("Сводка по артикулам")
    summary = df.groupby("Артикул").agg(
        Обрезков=("Остаток", "count"),
        Суммарная_длина=("Остаток", "sum"),
        Мин=("Остаток", "min"),
        Макс=("Остаток", "max"),
    ).sort_values("Суммарная_длина", ascending=False)
    summary.columns = ["Обрезков (шт)", "Суммарная длина (м)", "Мин (м)", "Макс (м)"]
    st.dataframe(summary, use_container_width=True)

    # Детальная таблица с редактированием
    st.divider()
    st.subheader("Все обрезки")

    # Фильтр по артикулу
    articles = ["Все"] + sorted(df["Артикул"].unique().tolist())
    selected = st.selectbox("Фильтр по артикулу", articles)

    display_df = df if selected == "Все" else df[df["Артикул"] == selected]

    edited = st.data_editor(
        display_df.reset_index(drop=True),
        use_container_width=True,
        num_rows="dynamic",
        height=500,
        column_config={
            "Артикул": st.column_config.TextColumn("Артикул", width="large"),
            "Остаток": st.column_config.NumberColumn("Остаток (м)", min_value=0, format="%.1f"),
        },
    )

    # Обновляем данные в session_state
    if selected == "Все":
        st.session_state["cuts_df"] = edited
    else:
        # Обновляем только отфильтрованные строки
        df_copy = df.copy()
        mask = df_copy["Артикул"] == selected
        df_copy.loc[mask] = edited.values
        st.session_state["cuts_df"] = df_copy

else:
    st.info("Нажмите «Загрузить из Google Sheets» чтобы загрузить данные обрезков.")
