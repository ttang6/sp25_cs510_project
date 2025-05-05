from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "professors"

mapping = {
    "mappings": {
        "properties": {
            "id": { "type": "integer" },
            "firstName": { "type": "text" },
            "lastName": { "type": "text" },
            "fullName": { "type": "text" },
            "department": { "type": "text" },
            "numRatings": { "type": "integer" },
            "avgRating": { "type": "float" },
            "avgDifficulty": { "type": "float" },
            "wouldTakeAgainPercent": { "type": "float" },
            "tags": { "type": "keyword" }
        }
    }
}

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"Deleted existing index: {index_name}")

es.indices.create(index=index_name, body=mapping)
print(f"Created index: {index_name}")