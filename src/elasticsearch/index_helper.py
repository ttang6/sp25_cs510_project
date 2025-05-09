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
    """Get all user indices (excluding system indices)"""
    all_indices = es.indices.get_alias().keys()
    return [idx for idx in all_indices if not idx.startswith('.')]

def get_index_type(index_name):
    """Determine the type of index based on its name"""
    if index_name.startswith('webpages_'):
        return 'webpage'
    elif index_name.endswith('_professors'):
        return 'professor'
    return 'unknown'

def get_index_stats(index_name, index_type):
    """Get specific stats based on index type"""
    try:
        stats = es.indices.stats(index=index_name)
        count = stats['indices'][index_name]['total']['docs']['count']
        size = stats['indices'][index_name]['total']['store']['size_in_bytes']
        health = es.cluster.health(index=index_name)['status']
        
        # Format size
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f}KB"
        else:
            size_str = f"{size/(1024*1024):.1f}MB"
        
        # Get type-specific stats
        if index_type == 'webpage':
            # Get mapping to show fields
            mapping = es.indices.get_mapping(index=index_name)
            fields = list(mapping[index_name]['mappings']['properties'].keys())
            return {
                'count': count,
                'size': size_str,
                'health': health,
                'fields': fields
            }
        elif index_type == 'professor':
            # Get average rating if available
            try:
                avg_rating = es.search(
                    index=index_name,
                    body={
                        "aggs": {
                            "avg_rating": {"avg": {"field": "avgRating"}}
                        },
                        "size": 0
                    }
                )['aggregations']['avg_rating']['value']
                return {
                    'count': count,
                    'size': size_str,
                    'health': health,
                    'avg_rating': f"{avg_rating:.2f}" if avg_rating else "N/A"
                }
            except:
                return {
                    'count': count,
                    'size': size_str,
                    'health': health
                }
        else:
            return {
                'count': count,
                'size': size_str,
                'health': health
            }
    except Exception as e:
        return {'error': str(e)}

def show_indices():
    """Display all indices"""
    try:
        indices = get_user_indices()
        
        if not indices:
            print("No user indices found")
            return
        
        print("\nAvailable Indices:")
        print("-" * 50)
        for index in indices:
            print(index)
        print("-" * 50)
        
    except Exception as e:
        print(f"Error showing indices: {str(e)}")

def delete_indices():
    """Delete indices with options"""
    try:
        indices = get_user_indices()
        
        if not indices:
            print("No user indices found")
            return
        
        print("\nDelete Options:")
        print("1. Delete specific index")
        print("2. Delete all user indices")
        print("3. Back to main menu")
        
        choice = input("\nChoice (1-3): ")
        
        if choice == "1":
            print("\nAvailable indices:")
            for i, index in enumerate(indices, 1):
                print(f"{i}. {index}")
            
            index_num = input("\nIndex number to delete: ")
            try:
                index_num = int(index_num)
                if 1 <= index_num <= len(indices):
                    index_to_delete = indices[index_num - 1]
                    confirm = input(f"Delete '{index_to_delete}'? (y/n): ")
                    if confirm.lower() == 'y':
                        print(f"Deleting: {index_to_delete}")
                        es.indices.delete(index=index_to_delete)
                        print("Done")
                    else:
                        print("Cancelled")
                else:
                    print("Invalid number")
            except ValueError:
                print("Invalid input")
        
        elif choice == "2":
            confirm = input("Delete all user indices? (y/n): ")
            if confirm.lower() == 'y':
                for index in indices:
                    print(f"Deleting: {index}")
                    es.indices.delete(index=index)
                print("All user indices deleted")
            else:
                print("Cancelled")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def rename_index():
    """Rename an index"""
    try:
        indices = get_user_indices()
        
        if not indices:
            print("No user indices found")
            return
        
        print("\nAvailable indices:")
        for i, index in enumerate(indices, 1):
            print(f"{i}. {index}")
        
        index_num = input("\nSelect index number to rename: ")
        try:
            index_num = int(index_num)
            if 1 <= index_num <= len(indices):
                old_name = indices[index_num - 1]
                new_name = input(f"Enter new name for '{old_name}': ")
                
                if new_name in indices:
                    print("Error: Index with this name already exists")
                    return
                
                confirm = input(f"Rename '{old_name}' to '{new_name}'? (y/n): ")
                if confirm.lower() == 'y':
                    # Create new index with same mapping
                    mapping = es.indices.get_mapping(index=old_name)
                    es.indices.create(index=new_name, body=mapping[old_name])
                    
                    # Reindex data
                    es.reindex(body={
                        "source": {"index": old_name},
                        "dest": {"index": new_name}
                    })
                    
                    # Delete old index
                    es.indices.delete(index=old_name)
                    print("Index renamed successfully")
                else:
                    print("Cancelled")
            else:
                print("Invalid index number")
        except ValueError:
            print("Invalid input")
            
    except Exception as e:
        print(f"Error renaming index: {str(e)}")

if __name__ == "__main__":
    print("\n=== Elasticsearch Index Manager ===")
    print("Welcome! This tool helps you manage your Elasticsearch indices.")
    
    while True:
        print("\nMain Menu:")
        print("1. Show indices")
        print("2. Delete indices")
        print("3. Rename index")
        print("4. Exit")
        
        choice = input("\nChoice (1-4): ")
        
        if choice == "1":
            show_indices()
        elif choice == "2":
            delete_indices()
        elif choice == "3":
            rename_index()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice") 