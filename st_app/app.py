# app.py
import io
import pandas as pd
import streamlit as st

from scrapers.shopify_generic import scrape_shopify_all_products, DEFAULT_HEADERS
from scrapers.ariika import scrape_ariika, ARIika_CATEGORIES

st.set_page_config(page_title="Multi-site Shopify Scraper", layout="wide")

st.title("🧵 Multi-site Product Scraper (Streamlit)")
st.write("Pick a website, run the scraper, preview results, then download CSV.")

SITES = {
    "Heba Linens": {"type": "shopify", "base_url": "https://hebalinens.com"},
    "Lilly Home (EG)": {"type": "shopify", "base_url": "https://eg.lilly-home.com"},
    "Malaika Linens": {"type": "shopify", "base_url": "https://malaikalinens.com"},
    "More Cottons": {"type": "shopify", "base_url": "https://morecottons.com"},
    "Nillens": {"type": "shopify", "base_url": "https://nillens.com"},
    "Ariika": {"type": "ariika", "base_url": "https://ariika.com"},
}

with st.sidebar:
    st.header("Controls")
    site_name = st.selectbox("Select site", list(SITES.keys()))

    st.subheader("Scrape options")
    per_product_delay = st.slider("Delay per product (seconds)", 0.0, 3.0, 1.0, 0.1)
    retries = st.slider("Retries per product", 1, 5, 2, 1)
    backoff_sec = st.slider("Retry backoff (seconds)", 0.5, 5.0, 2.0, 0.5)

    if SITES[site_name]["type"] == "shopify":
        max_pages = st.number_input("Max collection pages", min_value=1, max_value=1000, value=200, step=10)
    else:
        max_pages_per_category = st.number_input("Max pages per category", min_value=1, max_value=500, value=100, step=10)
        categories = st.multiselect("Ariika categories", ARIika_CATEGORIES, default=ARIika_CATEGORIES)

    st.subheader("HTTP")
    use_custom_ua = st.checkbox("Use custom User-Agent", value=True)
    custom_ua = st.text_input(
        "User-Agent",
        value=DEFAULT_HEADERS["User-Agent"],
        disabled=not use_custom_ua
    )
    headers = {"User-Agent": custom_ua} if use_custom_ua else DEFAULT_HEADERS

run = st.button("Run scrape", type="primary")

if "df" not in st.session_state:
    st.session_state.df = None
if "failed_df" not in st.session_state:
    st.session_state.failed_df = None

if run:
    with st.status("Scraping in progress...", expanded=True) as status:
        st.write(f"Site: **{site_name}**")

        try:
            if SITES[site_name]["type"] == "shopify":
                rows, failed = scrape_shopify_all_products(
                    SITES[site_name]["base_url"],
                    max_pages=int(max_pages),
                    per_product_delay=float(per_product_delay),
                    retries=int(retries),
                    backoff_sec=float(backoff_sec),
                    headers=headers,
                )
            else:
                rows, failed = scrape_ariika(
                    categories=categories,
                    max_pages_per_category=int(max_pages_per_category),
                    per_product_delay=float(per_product_delay),
                    retries=int(retries),
                    backoff_sec=float(backoff_sec),
                    headers=headers,
                )

            df = pd.DataFrame(rows)
            failed_df = pd.DataFrame({"Handle": failed})

            st.session_state.df = df
            st.session_state.failed_df = failed_df

            status.update(label="Scrape complete ✅", state="complete", expanded=False)

        except Exception as e:
            status.update(label="Scrape failed ❌", state="error", expanded=True)
            st.exception(e)

df = st.session_state.df
failed_df = st.session_state.failed_df

if df is not None:
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader("Results preview")
        st.caption(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        st.dataframe(df, use_container_width=True, height=520)

    with col2:
        st.subheader("Failed handles")
        if failed_df is not None and len(failed_df) > 0:
            st.dataframe(failed_df, use_container_width=True, height=520)
        else:
            st.write("No failures 🎉")

    with col3:
        st.subheader("Download")
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download results CSV",
            data=csv_bytes,
            file_name=f"{site_name.lower().replace(' ', '_')}_variants.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if failed_df is not None and len(failed_df) > 0:
            failed_bytes = failed_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download failed handles CSV",
                data=failed_bytes,
                file_name=f"{site_name.lower().replace(' ', '_')}_failed_handles.csv",
                mime="text/csv",
                use_container_width=True,
            )
else:
    st.info("Pick a site and click **Run scrape**.")
