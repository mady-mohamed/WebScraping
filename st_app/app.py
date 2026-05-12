# import streamlit as st
# import pandas as pd
# import scraping  # This refers to your scraping.py file
# from datetime import datetime

# st.set_page_config(page_title="Product Scraper & Categorizer", layout="wide")

# st.title("🛍️ Web Scraping & Categorization App")

# # Complete list of websites
# websites = {
#     "Applemint": 'https://applemintandcocoa.com/', 
#     "Heba": 'https://hebalinens.com/', 
#     "House Babylon": 'https://me.housebabylon.com/',
#     "Junior": 'https://junior-tex.com/', 
#     "Kiabi": 'https://kiabi.eg/', 
#     "Knana": 'https://knana-eg.com/', 
#     "Lilly Home": 'https://eg.lilly-home.com/', 
#     "Lovely Land": 'http://lovelylandeg.com/',
#     "Malaika": 'http://malaikalinens.com/', 
#     "More Cottons": 'http://morecottons.com/', 
#     "Nillens": 'http://nillens.com/', 
#     "Ninos Kids": 'https://www.ninoskids.com/', 
#     "Triconuts": 'https://www.triconuts.com/',
#     "Relax Home":"https://www.relaxhomelinens.com/"
# }

# website_names = list(websites.keys())

# # --- Sidebar / Selection Logic ---
# st.subheader("Select Websites to Scrape")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("✅ Select All"):
#         for website in website_names:
#             st.session_state[website] = True
#         st.rerun()

# with col2:
#     if st.button("❌ Deselect All"):
#         for website in website_names:
#             st.session_state[website] = False
#         st.rerun()

# # Create a layout for checkboxes (3 columns)
# st.write("---")
# check_cols = st.columns(3)
# selected_sites = []

# for i, website in enumerate(website_names):
#     # Determine which column to place the checkbox in
#     col_idx = i % 3
#     # Link checkbox to session state
#     is_checked = check_cols[col_idx].checkbox(website, key=website)
#     if is_checked:
#         selected_sites.append(website)

# st.write("---")

# # --- Scraping Execution ---
# if st.button("🚀 Start Scraping", type="primary"):
#     if not selected_sites:
#         st.warning("Please select at least one website.")
#     else:
#         df_list = []
#         progress_bar = st.progress(0)
#         status_text = st.empty()

#         for idx, site_name in enumerate(selected_sites):
#             status_text.write(f"Currently Scraping: **{site_name}**...")
            
#             # Update progress
#             progress = (idx) / len(selected_sites)
#             progress_bar.progress(progress)

#             # Call the scrape function from scraping.py
#             try:
#                 scraped_df = scraping.scrape_website(websites[site_name])
#                 if not scraped_df.empty:
#                     df_list.append(scraped_df)
#                     st.success(f"Finished {site_name}: Found {len(scraped_df)} items.")
#                 else:
#                     st.info(f"{site_name} returned no data.")
#             except Exception as e:
#                 st.error(f"Error scraping {site_name}: {e}")

#         progress_bar.progress(1.0)
#         status_text.write("✅ All selected sites processed!")

#         if df_list:
#             # Combine all results
#             combined_raw_df = pd.concat(df_list, ignore_index=True)
            
#             # Run the cleaning and categorization logic
#             with st.spinner("Cleaning and applying Category Keywords..."):
#                 final_df = scraping.clean_df(combined_raw_df)
            
#             st.subheader("Scraped & Categorized Data")
#             st.write(f"Total Unique Products: {len(final_df)}")
#             st.dataframe(final_df, use_container_width=True)

#             # Download Button
#             csv = final_df.to_csv(index=False).encode('utf-8-sig')
#             st.download_button(
#                 label="📥 Download Categorized Data as CSV",
#                 data=csv,
#                 file_name=f"scraped_products_{datetime.now().strftime('%Y%m%d')}.csv",
#                 mime="text/csv",
#             )
#         else: 
#             st.error("No data was collected from any site.")

import streamlit as st
import pandas as pd
import scraping
from datetime import datetime
import json
import os

# --- JSON Utility Functions ---
CONFIG_FILE = r"st_app\save_data.json"

def load_websites():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("websites", {})
    return {}

def save_websites(websites_dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"websites": websites_dict}, f, indent=4)

# --- App Setup ---
st.set_page_config(page_title="Product Scraper & Categorizer", layout="wide")
st.title("🛍️ Web Scraping & Categorization App")

# Load current websites from JSON
websites = load_websites()
website_names = list(websites.keys())

# --- ⚙️ Website Management Section ---
with st.expander("⚙️ Manage Websites (Add/Delete)"):
    m_col1, m_col2 = st.columns(2)
    
    with m_col1:
        st.write("### Add New Website")
        new_name = st.text_input("Website Name", placeholder="e.g. Cottonil")
        new_url = st.text_input("Website URL", placeholder="https://example.com/")
        if st.button("➕ Add Website"):
            if new_name and new_url:
                if not new_url.endswith('/'): new_url += '/'
                websites[new_name] = new_url
                save_websites(websites)
                st.success(f"Added {new_name}!")
                st.rerun()
            else:
                st.error("Please provide both name and URL.")

    with m_col2:
        st.write("### Delete Website")
        to_delete = st.selectbox("Select website to remove", [""] + website_names)
        if st.button("🗑️ Delete Selected"):
            if to_delete:
                del websites[to_delete]
                save_websites(websites)
                st.warning(f"Deleted {to_delete}")
                st.rerun()
            else:
                st.error("Select a website first.")

# --- Selection Logic ---
st.subheader("Select Websites to Scrape")

col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Select All"):
        for name in website_names:
            st.session_state[name] = True
        st.rerun()
with col2:
    if st.button("❌ Deselect All"):
        for name in website_names:
            st.session_state[name] = False
        st.rerun()

st.write("---")
check_cols = st.columns(3)
selected_sites = []

for i, name in enumerate(website_names):
    col_idx = i % 3
    is_checked = check_cols[col_idx].checkbox(name, key=name)
    if is_checked:
        selected_sites.append(name)

st.write("---")

# --- Scraping Execution ---
if st.button("Start Scraping", type="primary"):
    if not selected_sites:
        st.warning("Please select at least one website.")
    else:
        df_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, site_name in enumerate(selected_sites):
            status_text.write(f"Currently Scraping: **{site_name}**...")
            progress = (idx) / len(selected_sites)
            progress_bar.progress(progress)

            try:
                # Use the URL from our loaded JSON dictionary
                scraped_df = scraping.scrape_website(websites[site_name])
                if not scraped_df.empty:
                    df_list.append(scraped_df)
                    st.success(f"Finished {site_name}: Found {len(scraped_df)} items.")
                else:
                    st.info(f"{site_name} returned no data.")
            except Exception as e:
                st.error(f"Error scraping {site_name}: {e}")

        progress_bar.progress(1.0)
        status_text.write("✅ All selected sites processed!")

        if df_list:
            combined_raw_df = pd.concat(df_list, ignore_index=True)
            with st.spinner("Cleaning, Categorizing, and Clustering..."):
                final_df = scraping.clean_df(combined_raw_df)
            
            st.subheader("Scraped & Categorized Data")
            # st.write(f"Total Unique Products: {len(final_df)}")
            st.dataframe(final_df, use_container_width=True)

            csv = final_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Categorized Data as CSV",
                data=csv,
                file_name=f"scraped_products_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else: 
            st.error("No data was collected from any site.")