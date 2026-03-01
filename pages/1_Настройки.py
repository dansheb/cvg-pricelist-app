"""
Страница настроек — подключение, модели, нарезка, имена, маркетплейсы.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Настройки", page_icon="⚙️", layout="wide")

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

st.title("Настройки")

# ── Вкладки ──────────────────────────────────────────────────────────────────

tab_conn, tab_models, tab_cuts, tab_names, tab_yandex, tab_market = st.tabs([
    "Подключение", "Модели", "Нарезка", "Имена / Штрих-коды",
    "Яндекс Маркет", "Маркетплейсы",
])

# ── Вкладка: Подключение и URL ───────────────────────────────────────────────

with tab_conn:
    st.subheader("Источники данных")

    cfg["xml_url"] = st.text_input(
        "URL XML-прайслиста CVG",
        value=cfg["xml_url"],
        help="GET-запрос без авторизации",
    )
    cfg["settings_sheet_id"] = st.text_input(
        "Google Sheet ID — Настройки (Models, CutSettings, Names, YandexSettings)",
        value=cfg["settings_sheet_id"],
    )
    cfg["cuts_sheet_id"] = st.text_input(
        "Google Sheet ID — Обрезки (Балтийская)",
        value=cfg["cuts_sheet_id"],
    )
    cfg["vi_sheet_id"] = st.text_input(
        "Google Sheet ID — Прикат ВсеИнструменты",
        value=cfg["vi_sheet_id"],
    )

    st.divider()
    if st.button("Проверить подключение", use_container_width=True):
        import requests
        from logic import read_gsheet

        checks = {
            "XML CVG": cfg["xml_url"],
            "Settings (Models)": None,
            "Обрезки": None,
            "Прикат ВИ": None,
        }

        # XML
        try:
            r = requests.get(cfg["xml_url"], timeout=10)
            r.raise_for_status()
            st.success(f"XML CVG — OK ({len(r.content)} байт)")
        except Exception as e:
            st.error(f"XML CVG — Ошибка: {e}")

        # Settings
        try:
            df = read_gsheet(cfg["settings_sheet_id"], "Models")
            st.success(f"Settings/Models — OK ({len(df)} строк)")
        except Exception as e:
            st.error(f"Settings/Models — Ошибка: {e}")

        # Обрезки
        try:
            df = read_gsheet(cfg["cuts_sheet_id"], "CutsLeftover")
            st.success(f"Обрезки — OK ({len(df)} строк)")
        except Exception as e:
            st.error(f"Обрезки — Ошибка: {e}")

        # Прикат ВИ
        try:
            import urllib.request
            url = f"https://docs.google.com/spreadsheets/d/{cfg['vi_sheet_id']}/export"
            resp = urllib.request.urlopen(url)
            st.success(f"Прикат ВИ — OK ({len(resp.read())} байт)")
        except Exception as e:
            st.error(f"Прикат ВИ — Ошибка: {e}")


# ── Вкладка: Модели ─────────────────────────────────────────────────────────

with tab_models:
    st.subheader("Модели (Models)")
    st.caption("Артикулы товаров, резерв для CVG, флаг нарезки, длина бухты")

    if st.button("Загрузить из Google Sheets", key="load_models"):
        try:
            from logic import read_gsheet
            df = read_gsheet(cfg["settings_sheet_id"], "Models")
            st.session_state["models_df"] = df
            st.success(f"Загружено {len(df)} моделей")
        except Exception as e:
            st.error(f"Ошибка: {e}")

    if "models_df" in st.session_state:
        df = st.session_state["models_df"]
        st.metric("Всего моделей", len(df))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Кабели (нарезка)", len(df[df["Резка"] == True]))
        with col2:
            st.metric("Обычные товары", len(df[df["Резка"] == False]))

        # Фильтр
        show_filter = st.radio("Показать", ["Все", "Только кабели", "Только обычные"], horizontal=True)
        if show_filter == "Только кабели":
            display_df = df[df["Резка"] == True]
        elif show_filter == "Только обычные":
            display_df = df[df["Резка"] == False]
        else:
            display_df = df

        # Поиск
        search = st.text_input("Поиск по артикулу", key="model_search")
        if search:
            display_df = display_df[display_df["Артикул"].str.contains(search, case=False, na=False)]

        edited = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            height=500,
        )
        st.session_state["models_df"] = edited


# ── Вкладка: Настройки нарезки ──────────────────────────────────────────────

with tab_cuts:
    st.subheader("Настройки нарезки (CutSettings)")
    st.caption("cut_length — длина отреза, n_in_coil — макс. отрезов из одной бухты, "
               "cut_margin — наценка за нарезку, pack_price — стоимость упаковки")

    if st.button("Загрузить из Google Sheets", key="load_cuts"):
        try:
            from logic import read_gsheet
            df = read_gsheet(cfg["settings_sheet_id"], "CutSettings")
            st.session_state["cut_settings_df"] = df
            st.success(f"Загружено {len(df)} настроек нарезки")
        except Exception as e:
            st.error(f"Ошибка: {e}")

    if "cut_settings_df" in st.session_state:
        edited = st.data_editor(
            st.session_state["cut_settings_df"],
            use_container_width=True,
            num_rows="dynamic",
        )
        st.session_state["cut_settings_df"] = edited

        st.info("Строки с cut_margin=0 и pack_price=0 (100 м, 200 м) — полные бухты, "
                "продаются без маркетплейс-наценки.")

# ── Вкладка: Имена и штрих-коды ─────────────────────────────────────────────

with tab_names:
    st.subheader("Имена и штрих-коды (Names)")

    if st.button("Загрузить из Google Sheets", key="load_names"):
        try:
            from logic import read_gsheet
            df = read_gsheet(cfg["settings_sheet_id"], "Names")
            st.session_state["names_df"] = df
            st.success(f"Загружено {len(df)} записей")
        except Exception as e:
            st.error(f"Ошибка: {e}")

    if "names_df" in st.session_state:
        df = st.session_state["names_df"]
        st.metric("Всего записей", len(df))

        search = st.text_input("Поиск", key="names_search")
        display_df = df
        if search:
            mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
            display_df = df[mask]

        st.dataframe(display_df, use_container_width=True, height=500)


# ── Вкладка: Яндекс Маркет ──────────────────────────────────────────────────

with tab_yandex:
    st.subheader("Параметры комиссии Яндекс Маркета")

    if st.button("Загрузить из Google Sheets", key="load_yandex"):
        try:
            from logic import read_gsheet
            df = read_gsheet(cfg["settings_sheet_id"], "YandexSettings")
            row = df.iloc[0].to_dict()
            st.session_state["ya_settings"] = row
            st.success("");
        except Exception as e:
            st.error(f"Ошибка: {e}")

    ya = st.session_state.get("ya_settings", {
        "ya_order_processing": 25.0,
        "ya_order_placing": 0.14,
        "ya_delivery_local": 0.05,
        "ya_delivery_local_min": 60.0,
        "ya_delivery_local_max": 350.0,
        "ya_payment_processing": 0.01,
    })

    col1, col2 = st.columns(2)
    with col1:
        ya["ya_order_processing"] = st.number_input(
            "Обработка заказа (руб.)", value=float(ya["ya_order_processing"]), step=1.0
        )
        ya["ya_order_placing"] = st.number_input(
            "Размещение (доля)", value=float(ya["ya_order_placing"]), step=0.01, format="%.2f"
        )
        ya["ya_delivery_local"] = st.number_input(
            "Доставка (доля)", value=float(ya["ya_delivery_local"]), step=0.01, format="%.2f"
        )
    with col2:
        ya["ya_delivery_local_min"] = st.number_input(
            "Доставка мин. (руб.)", value=float(ya["ya_delivery_local_min"]), step=1.0
        )
        ya["ya_delivery_local_max"] = st.number_input(
            "Доставка макс. (руб.)", value=float(ya["ya_delivery_local_max"]), step=1.0
        )
        ya["ya_payment_processing"] = st.number_input(
            "Платёжная обработка (доля)", value=float(ya["ya_payment_processing"]), step=0.01, format="%.2f"
        )
    st.session_state["ya_settings"] = ya

    # Калькулятор комиссии
    st.divider()
    st.caption("Калькулятор комиссии")
    test_price = st.number_input("Цена товара (руб.)", value=1000.0, step=100.0)
    if test_price > 0:
        from logic import ya_commission, market_price
        comm = ya_commission(test_price, ya)
        mp = market_price(test_price, cfg["dealer_margin"], ya)
        st.write(f"Комиссия ЯМ: **{comm:.2f}** руб. ({comm/test_price*100:.1f}%)")
        st.write(f"Маркетплейс-цена: **{mp:.0f}** руб.")


# ── Вкладка: Маркетплейсы ───────────────────────────────────────────────────

with tab_market:
    st.subheader("Параметры маркетплейсов")

    cfg["dealer_margin"] = st.number_input(
        "Маржа дилера (для расчёта маркетплейс-цены)",
        value=cfg["dealer_margin"],
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        format="%.2f",
        help="Используется в GoalSeek для расчёта цены, при которой дилер выходит в 0",
    )
    cfg["wb_margin"] = st.number_input(
        "Наценка Wildberries",
        value=cfg["wb_margin"],
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        format="%.2f",
    )
    cfg["vi_coefficient"] = st.number_input(
        "Коэффициент закупочной цены ВсеИнструменты",
        value=cfg["vi_coefficient"],
        min_value=1.0,
        step=0.01,
        format="%.2f",
        help="Закупочная цена = Рекомендованная цена / коэффициент",
    )
