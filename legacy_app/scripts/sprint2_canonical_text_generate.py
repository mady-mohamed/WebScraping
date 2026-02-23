# %%
import pandas as pd

df = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products.csv")
df = df.iloc[:, 1:]
df

# %%
df['Brand + Handle'] = df["Brand"] + ' ' + df["Handle"]
df.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products_clean.csv", index=False)
df

# %%



