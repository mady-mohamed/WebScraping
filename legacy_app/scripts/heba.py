# %%
import pandas as pd
file = r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\heba.csv'
df = pd.read_csv(file)
df = df[df['Description'].fillna('').str.strip() != ""]
df = df.dropna()
df

# %%
# import pandas as pd

# # Define how to handle each column during the merge
# aggregation_rules = {
#     'Variant': lambda x: list(x.unique()), # Create a "White, Cream, Blue" string
#     'Variant ID': lambda x: list(x.astype(str).unique()),               # Create a list of IDs
#     'SKU': lambda x: list(x.unique()),                      # Create a list of SKUs
#     'Handle': 'first',                                      # Keep the first value found
#     'Availability': 'first',
#     'Product URL': 'first',
#     'Scraped at': 'first'
# }

# # Group by the "Core" identity of the product and apply the rules
# df_merged = df.groupby(['Product', 'Description', 'Price'], as_index=False).agg(aggregation_rules)

# # Reorder columns to match your original header order
# columns_order = [
#     'Product', 'Variant', 'Price', 'Handle', 'Variant ID', 
#     'Availability', 'SKU', 'Product URL', 'Scraped at', 
#     'Description'
# ]
# df_merged = df_merged[columns_order]
# df_merged['Hollistic Description'] = df_merged['Product'] + ' - ' + str(df_merged['Variant']) + ": " + df_merged["Description"]
# df_merged.to_csv(r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\heba_variants_cleaned.csv')

import pandas as pd

# 1. Clean the 'Description' column BEFORE merging to remove new lines
df['Description'] = df['Description'].str.replace(r'\n|\r', ' ', regex=True)

# 2. Updated aggregation rules to create clean strings instead of Python lists
# We use ', '.join() to make "White, Cream" instead of "['White', 'Cream']"
aggregation_rules = {
    'Variant': lambda x: ', '.join(map(str, x.unique())), 
    'Variant ID': lambda x: ', '.join(map(str, x.unique())),
    'SKU': lambda x: ', '.join(map(str, x.unique())),
    'Handle': 'first',
    'Availability': 'first',
    'Product URL': 'first',
    'Scraped at': 'first'
}

# Group by the "Core" identity
df_merged = df.groupby(['Product', 'Description', 'Price'], as_index=False).agg(aggregation_rules)

# 3. FIX: Create the Hollistic Description correctly
# Use .astype(str) instead of str() to handle it row-by-row
df_merged['Hollistic Description'] = (
    df_merged['Product'] + 
    ' - ' + 
    df_merged['Variant'].astype(str) + 
    ": " + 
    df_merged["Description"]
)

# Reorder columns
columns_order = [
    'Product', 'Variant', 'Price', 'Handle', 'Variant ID', 
    'Availability', 'SKU', 'Product URL', 'Scraped at', 
    'Description', 'Hollistic Description'
]
df_merged = df_merged[columns_order]

# Save to CSV (index=False prevents that extra "0, 1, 2" column at the start)
df_merged.to_csv(r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\heba_compact_view.csv', index=False)
df_merged

# %%
'''
Products Table
'''
df_products = df_merged
df_products = df_products.drop(columns=['Variant', 'Price', 'Variant ID', 'Availability', 'SKU'])
df_products.to_csv(r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\heba_products.csv', index=False)
df_products

# %%
'''
Variants Table
'''

df_variants = df
df_variants = df_variants.drop(columns=['Product', "Product URL", 'Description'])
cols_to_move = ['Variant ID', 'Handle', 'Variant', 'Price', 'SKU', 'Scraped at']

# Get the list of all other columns that aren't in the "move" list
remaining_cols = [c for c in df_variants.columns if c not in cols_to_move]

# Reorder with move-list first, then the rest
df_variants = df[cols_to_move + remaining_cols]
df_variants.to_csv(r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\heba_variants.csv', index=False)
df_variants


