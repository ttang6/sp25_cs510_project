import json
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch("http://localhost:9200")
index_name = "webpages"

with open("data/rawJSON/exmaple_data.json") as f:
    pages = json.load(f)

actions = []
for page in pages:
    doc = {
        "_index": index_name,
        "_source": {
            "title": page.get("title", ""),
            "url": page.get("url", ""),
            "anchor_texts": page.get("anchor_texts", []),
            "content": page.get("content", ""),
            "outlinks": page.get("outlinks", [])
        }
    }
    actions.append(doc)

helpers.bulk(es, actions)
print(f"Indexed {len(actions)} web pages.")