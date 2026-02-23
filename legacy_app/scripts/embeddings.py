from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

import pprint
# 1. Our 10 products
products = [
    "Cotton Bath Towel", "Soft Microfiber Washcloth",
    "Heavyweight Winter Duvet", "Goose Down Comforter",
    "Stainless Steel Frying Pan", "Non-stick Ceramic Skillet",
    "Organic Whole Milk", "Almond Milk (Unsweetened)",
    "Bluetooth Wireless Headphones", "Noise-Cancelling Earbuds"
]


descriptions = ""

# 2. Batch Inference (Text -> Vectors)
product_embeddings = model.encode(products)

# 3. Compute the 10x10 Matrix
# This compares the 'product_embeddings' against themselves
matrix = util.cos_sim(product_embeddings, product_embeddings)
sorted = []
dict_products = {}
# Convert to a readable numpy array
sim_matrix = matrix.numpy()
print(sim_matrix)