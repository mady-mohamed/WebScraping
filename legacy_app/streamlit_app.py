import streamlit as st
import pandas as pd
import time
from datetime import datetime
from functions import get_handles_from_page, extract_product_data

# Page Config
st.set_page_config(page_title="Heba Linens Scraper", page_icon="🛍️")

st.title("🛍️ Heba Linens Product Scraper")
st.markdown("""
This app scrapes product data from **hebalinens.com**. 
It iterates through all collection pages, extracts product handles, and fetches variant details.
""")

BASE_URL = "https://hebalinens.com"

# Initialize session state for data persistence
if 'df' not in st.session_state:
    st.session_state.df = None

# Sidebar controls
st.sidebar.header("Settings")
scrape_button = st.sidebar.button("🚀 Start Scraping")

if scrape_button:
    page = 1
    all_product_data = []
    all_handles_seen = set()
    total_failed_handles = []
    
    # Progress placeholders
    status_text = st.empty()
    progress_bar = st.progress(0)
    table_placeholder = st.empty()
    
    try:
        while True:
            status_text.info(f"Scanning Page {page} for handles...")
            handles_on_page = get_handles_from_page(BASE_URL, page)
            
            # Determine which handles are actually new
            new_handles = handles_on_page - all_handles_seen
            
            if not new_handles:
                status_text.success("✅ No more new products found. Scrape complete!")
                break
            
            status_text.warning(f"Found {len(new_handles)} new products on page {page}. Fetching details...")
            
            # Update our master "seen" set
            all_handles_seen.update(new_handles)
            
            # Scrape the specific data for these new handles
            page_data, page_failed = extract_product_data(BASE_URL, new_handles)
            
            all_product_data.extend(page_data)
            total_failed_handles.extend(page_failed)
            
            # Update the UI table live
            current_df = pd.DataFrame(all_product_data)
            table_placeholder.dataframe(current_df, use_container_width=True)
            
            page += 1
            # Small break to prevent Streamlit UI lag
            time.sleep(0.1)

        # Store in session state
        st.session_state.df = pd.DataFrame(all_product_data)
        
        if total_failed_handles:
            st.sidebar.error(f"Failed to fetch {len(total_failed_handles)} handles.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Display results and download button if data exists
if st.session_state.df is not None:
    df = st.session_state.df
    
    st.divider()
    st.subheader("Data Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Variants", len(df))
    col2.metric("Unique Products", df['Handle'].nunique())
    col3.metric("Avg. Price", f"{df['Price'].mean():.2f} EGP")

    # Final Dataframe Display
    st.dataframe(df, use_container_width=True)

    # Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f"heba_linens_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime='text/csv',
    )
else:
    st.info("Click 'Start Scraping' in the sidebar to begin.")