# %%
# '''
# All Products
# '''
# import pandas as pd

# df_heba = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\heba\heba_products.csv")
# df_nillens = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\nillens\nillens_products.csv")
# df_lilly = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\lilly home\lilly_home_products.csv")
# df_heba

# %%
from numpy import var
import re, webcolors
df_all = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products_clean.csv")
def extract_color(text):
    match = re.search(r"-\s*([^:-]+):", text)
    if match:
        result = match.group(1)
        return result
variants = df_all["Hollistic Description"].apply(extract_color)
'''
I want to check if the CSS3 having colors in the variants list
'''
i = 0
# 1. Get lowercase color names
colors = webcolors.names("css3")
# 2. Split your column into lists
variants_series = variants.str.split(', ')
def has_color(variant_string):
    """Returns True if any color in the comma-separated string is a valid CSS3 color."""
    if not isinstance(variant_string, str):
        return False
    
    # Split and clean the strings
    variants = [v.strip().lower() for v in variant_string.split(',')]
    
    # Return True if there is any intersection between our list and valid colors
    return any(color in colors for color in variants)
df_all["Variant is Color"] = variants.apply(has_color)
df_all

# %%
df_all

# %%
import numpy as np

df_all["Canonical Text"] = np.where(
    df_all["Variant is Color"] == True,
    df_all["Product"] + " " + df_all["Description"], # Result if True
    df_all["Hollistic Description"]                  # Result if False
)
df_all.drop(columns=["Variant is Color"], axis=1, inplace=True)
df_all.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products_clean.csv", index = False)

# %%
import pandas as pd
df = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products_clean.csv")
# Drop all columns whose names start with "Unnamed"
df = df.drop(df.filter(regex='^Unnamed').columns, axis=1)

# Or in-place:
# df.drop(df.filter(regex='^Unnamed').columns, axis=1, inplace=True)

df["Canonical Text"] = df["Product"] + " " + df["Description"]
print(df.to_csv())


