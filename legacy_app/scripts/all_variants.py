# %%
'''
All Variants
'''
import pandas as pd

df_heba = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\heba\heba_variants.csv")
df_nillens = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\nillens\nillens_variants.csv")
df_lilly = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\lilly home\lilly_home_variants.csv")
df_heba

# %%
df_heba["Brand"] = "Heba Linens"
df_nillens["Brand"] = "Nillens"
df_lilly["Brand"] = "Lilly Home"

df_combined_variants = pd.concat([df_heba, df_nillens, df_lilly], ignore_index=True)
df_combined_variants["Brand + Variant ID"] = df_combined_variants["Brand"] + " #" + df_combined_variants["Variant ID"].astype(str)
df = pd.DataFrame()
df["Brand"] = df_combined_variants["Brand"]
df["Variant ID"] = df_combined_variants["Variant ID"]
df["Variant"] = df_combined_variants["Handle"]
df["Price"] = df_combined_variants["Price"]
df["Availability"] = df_combined_variants["Availability"]
df["SKU"] = df_combined_variants["SKU"]
df["Brand + Variant ID"] = df_combined_variants["Brand + Variant ID"]
df

# %%
# df.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_variants_add_description.csv")
variant_list = df["Brand + Variant ID"].tolist()
variant_set = set(variant_list)
df.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_variants_clean.csv")

# %%



