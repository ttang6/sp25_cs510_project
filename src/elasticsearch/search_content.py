from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "webpages"

def search_webpages(query, size=10):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "anchor_texts^1.5", "content"]
            }
        },
        "size": size
    }

    res = es.search(index=index_name, body=body)
    results = []
    for hit in res["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "title": src.get("title", ""),
            "url": src.get("url", ""),
            "score": hit["_score"],
            "snippet": src.get("content", "")[:200]  # 可选返回前200字符
        })
    return results