# %%
'''
Loading Products
'''
import pandas as pd

df_heba = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\heba\heba_products.csv")
df_nillens = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Nillens\nillens_products.csv")
df_lilly = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Lilly Home\lilly_home_products.csv")

# %%
'''
Create in an all_products table 
'''
df_heba["Brand"] = "Heba Linens"
df_nillens["Brand"] = "Nillens"
df_lilly["Brand"] = "Lilly Home"
df_combined_products = pd.concat([df_heba, df_nillens, df_lilly], ignore_index=True)
df_combined_products

# %%
def remove_duplicate_products(df):
    """
    Removes rows where the combination of Brand and Handle is repeated.
    Keeps the first occurrence and removes subsequent ones.
    """
    # subset: the columns to check for duplicates
    # keep: 'first' keeps the first instance, 'last' keeps the last, False drops all duplicates
    df_cleaned = df.drop_duplicates(subset=['Brand', 'Handle'], keep='first')
    
    # Optional: Reset the index since rows were removed
    df_cleaned = df_cleaned.reset_index(drop=True)
    
    return df_cleaned

# %%
# Apply the function
df_combined_products_clean = remove_duplicate_products(df_combined_products)

# Display result
print(f"Total rows after removing duplicates: {df_combined_products_clean.shape[0]}. Rows removed {df_combined_products.shape[0]-df_combined_products_clean.shape[0]}")

# %%
df_combined_products_clean.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products.csv")
df_combined_products.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_products_unclean.csv")


# %%
'''
Loading Variants
'''
import pandas as pd

df_heba = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\heba\heba_variants.csv")
df_nillens = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Nillens\nillens_variants.csv")
df_lilly = pd.read_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Lilly Home\lilly_home_variants.csv")

# %%
'''
Save variants in a all_variants table 
'''
df_heba["Brand"] = "Heba Linens"
df_nillens["Brand"] = "Nillens"
df_lilly["Brand"] = "Lilly Home"
df_combined_variants = pd.concat([df_heba, df_nillens, df_lilly], ignore_index=True)
df_combined_variants


# %%
df_variants_final = df_combined_variants.drop_duplicates(subset=['Variant ID', 'Brand'], keep='first')
df_variants_final.to_csv(r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\all_variants.csv")


