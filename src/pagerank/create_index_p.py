from elasticsearch import Elasticsearch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.es_config as es_config

# Connect to Elasticsearch
es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=("elastic", es_config.KEY),
    verify_certs=False,
    ssl_show_warn=False
)

index_name = "pagerank"

# Define mapping
mapping = {
    "mappings": {
        "properties": {
            "url": {"type": "keyword"},
            "pagerank_score": {"type": "float"}
        }
    }
}

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"Deleted existing index: {index_name}")

es.indices.create(index=index_name, body=mapping)
print(f"Created index: {index_name}") 