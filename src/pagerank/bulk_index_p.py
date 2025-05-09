import json
from elasticsearch import Elasticsearch
from tqdm import tqdm
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.es_config as es_config


es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=("elastic", es_config.KEY),
    verify_certs=False,
    ssl_show_warn=False
)

index_name = "pagerank"
pagerank_file = "data/pagerank/pagerank_scores.json"
batch_size = 1000

# Read PageRank results
print(f"Reading file: {pagerank_file}")
with open(pagerank_file, 'r', encoding='utf-8') as f:
    pagerank_scores = json.load(f)

# Convert to list and sort
print("Sorting data...")
scores_list = [(url, score) for url, score in pagerank_scores.items()]
scores_list.sort(key=lambda x: x[1], reverse=True)

# Prepare bulk import
print("Starting bulk import...")
actions = []
total_imported = 0

for url, score in tqdm(scores_list, desc="Import progress"):
    # Add action metadata
    actions.append({
        "index": {
            "_index": index_name
        }
    })
    # Add document data
    actions.append({
        "url": url,
        "pagerank_score": score
    })
    
    # Bulk import
    if len(actions) >= batch_size * 2:  # Multiply by 2 because each document has 2 lines
        es.bulk(body=actions)
        total_imported += len(actions) // 2  # Divide by 2 to get actual document count
        actions = []

# Import remaining data
if actions:
    es.bulk(body=actions)
    total_imported += len(actions) // 2

print(f"Successfully imported {total_imported} PageRank records") 