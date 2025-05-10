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

def get_user_indices():
    """Get all non-system indices"""
    all_indices = es.indices.get_alias().keys()
    return [idx for idx in all_indices if not idx.startswith('.')]

def delete_all():
    """Delete all user indices while preserving system indices"""
    try:
        indices = get_user_indices()
        
        if not indices:
            print("No user indices found")
            return
            
        print("\nIndices to be deleted:")
        for idx in indices:
            print(f"- {idx}")
            
        confirm = input("\nConfirm deletion? (y/n): ")
        if confirm.lower() == 'y':
            for index in indices:
                print(f"Deleting: {index}")
                es.indices.delete(index=index)
            print("All user indices deleted successfully")
        else:
            print("Operation cancelled")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    delete_all() 