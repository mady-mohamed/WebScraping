# %%
import pandas as pd

''' Products '''

df = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products.csv")
brands = [x for x in df["Brand"]]
handles = [x for x in df["Handle"]]
products = [[x, y] for x, y in zip(brands, handles)]

# %%
unique_products = set(tuple(row) for row in products)
[[x[0],x[1]] for x in unique_products]


