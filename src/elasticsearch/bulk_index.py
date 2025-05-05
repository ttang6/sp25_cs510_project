import json
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "professors"

with open("data/rawJSON/rmp/example_prof_info.json") as f:
    data = json.load(f)

prof = data["professor"]
doc = {
    "id": prof["id"],
    "firstName": prof["firstName"],
    "lastName": prof["lastName"],
    "fullName": prof["fullName"],
    "department": prof["department"],
    "numRatings": prof["ratings"]["numRatings"],
    "avgRating": prof["ratings"]["avgRating"],
    "avgDifficulty": prof["ratings"]["avgDifficulty"],
    "wouldTakeAgainPercent": prof["ratings"]["wouldTakeAgainPercent"],
    "tags": prof.get("tags", [])
}

es.index(index=index_name, body=doc)
print("Inserted professor:", prof["fullName"])