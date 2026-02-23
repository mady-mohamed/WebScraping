import pandas as pd

df = pd.read_csv(r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\all\baby_kids.csv')

# Group by both ID and Name
stats = df.groupby(['Cluster Name'])['Price'].describe()

# Calculate IQR
q3 = df.groupby(['Cluster Name'])['Price'].quantile(0.75)
q1 = df.groupby(['Cluster Name'])['Price'].quantile(0.25)
stats['IQR'] = q3 - q1
# 1. Reset the index so 'Cluster Name' becomes a regular column
# 2. Set 'Cluster Name' as the only index
# 3. Transpose (swap rows/cols) and convert to a dictionary of lists
cluster_dict = stats.reset_index(level=0, drop=True).T.to_dict('list')

# Accessing a specific cluster
print(stats.to_dict())
