from elasticsearch import Elasticsearch
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

base_folder = "data/raw/website"
subfolders = [f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))]

mapping = {
    "mappings": {
        "properties": {
            "title":        { "type": "text", "analyzer": "english" },
            "url":          { "type": "keyword" },
            "anchor_texts": { "type": "text", "analyzer": "english" },
            "content":      { "type": "text", "analyzer": "english" },
            "outlinks":     { "type": "keyword" }
        }
    }
}

for subfolder in subfolders:
    index_name = f"webpages_{subfolder}"
    print(f"Creating index: {index_name}")
    es.indices.create(index=index_name, body=mapping)
    print(f"Index '{index_name}' created successfully")

print("\nAll indices created successfully!")