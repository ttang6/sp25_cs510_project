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

def create_professor_index(department):
    """Create professor index for a specific department"""
    index_name = f"{department}_professors"
    
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

    es.indices.create(index=index_name, body=mapping)
    print(f"Created index: {index_name}")

def main():
    # Get the path to the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw", "rmp")
    
    # Get all subdirectories
    departments = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    # Create indices for each department
    for department in departments:
        create_professor_index(department)

if __name__ == "__main__":
    main()