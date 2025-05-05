from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "webpages"

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

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
es.indices.create(index=index_name, body=mapping)
print(f"Index '{index_name}' created.")