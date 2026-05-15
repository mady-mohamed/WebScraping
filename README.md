# Web Scraping & Categorization App

A Streamlit-based Web Scraping application that collects product data from multiple Shopify-powered e-commerce websites, categorizes products using keyword-based classification, and groups semantically similar products using sentence embeddings and clustering.

<img width="1738" height="702" alt="image" src="https://github.com/user-attachments/assets/3ca664a3-83ad-4d9e-83e0-b4cd2313e21e" />


## Features

- Scrape multiple websites
- Add and remove websites dynamically from the UI
- Automatic product Categories
- Semantic product clustering using AI embeddings
- Download cleaned and categorized data as CSV
- Streamlit-based interactive interface
- Deduplication and product normalization
- Progress tracking during scraping

---

## Tech Stack

- Python
- Streamlit
- Pandas
- BeautifulSoup4
- Requests
- Sentence Transformers
- NetworkX
- NumPy

---

## Project Structure

```text
project/
│
├── app.py
├── scraping.py
├── st_app/
│   └── save_data.json
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/mady-mohamed/WebScraping
cd WebScraping
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate the environment:

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit app:

```bash
streamlit run app.py
```

The application will open in your browser automatically.

---

## How It Works

### 1. Website Management

The application stores websites inside:

```text
st_app/save_data.json
```

Users can:
- Add new websites
- Remove existing websites
- Persist website configuration between sessions

---

### 2. Product Scraping

The scraper:
- Iterates through Shopify collection pages
- Extracts product handles
- Calls Shopify's hidden `.js` product endpoint
- Collects:
  - Product title
  - Variants
  - Price
  - SKU
  - Availability
  - Description
  - Product URL
  - Brand name

---

### 3. Product Categorization

Products are categorized using keyword scoring.

Current categories include:

- baby_kids
- bedding
- bathroom
- dining
- kitchen
- clothing
- loungeware
- home_decor
- storage

The algorithm:
- Scans titles and descriptions
- Assigns weighted scores
- Returns the best matching category
- Stores evidence for classification

---

### 4. Semantic Clustering

The application uses:

```python
SentenceTransformer('all-MiniLM-L6-v2')
```

to generate embeddings for products.

Products are grouped by semantic similarity using:
- cosine similarity
- graph clustering
- connected components

This helps identify:
- duplicate products
- related variants
- similar listings across stores

---

## Output Columns

The exported CSV includes:

| Column | Description |
|---|---|
| Brand | Website brand |
| Product | Product title |
| Category | Assigned category |
| Cluster ID | Similarity cluster |
| Price | Product price |
| SKU | Product SKU |
| Product URL | Direct product link |
| Description | Cleaned description |
| Category Evidence | Why the category was assigned |

---

## Example Workflow

1. Launch the app
2. Add websites if needed
3. Select websites to scrape
4. Click "Start Scraping"
5. Wait for processing
6. Review categorized products
7. Download CSV results

---

## Notes

- The scraper currently assumes Shopify-based websites.
- Some websites may block scraping requests.
- Large scraping jobs may take time due to rate limiting.
- Semantic clustering requires downloading the transformer model on first run.

---

## Future Improvements

Potential enhancements:

- [x] Async scraping
- [x] Retry queue system
- [x] Database integration
- [ ] Better clustering thresholds
- [ ] Multi-threaded scraping
- [ ] Image scraping support
- [ ] Export to Excel
- [ ] Product comparison dashboard
- [ ] AI-based category prediction
- [ ] Using a Local or API-based LLM to name the Clusters
