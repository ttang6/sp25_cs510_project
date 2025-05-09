import json
import os
import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix

def get_all_json_dirs(main_dir):
    """
    Get all directories containing JSON files from main directory
    
    Args:
        main_dir: Main directory path
    Returns:
        list: List of directories containing JSON files
    """
    json_dirs = []
    for root, _, files in os.walk(main_dir):
        if any(file.endswith('.json') for file in files):
            json_dirs.append(root)
    return json_dirs

def build_graph_from_directories(input_dirs):
    """
    Build a complete web graph from all JSON files in multiple directories
    
    Args:
        input_dirs: List of directories containing crawler result JSON files
    Returns:
        networkx.DiGraph: Directed graph containing all page link relationships
    """
    G = nx.DiGraph()
    total_pages = 0
    total_links = 0
    processed_urls = set()  # 用于跟踪已处理的URL
    
    # Process each directory
    for input_dir in input_dirs:
        print(f"[INFO] Processing directory: {input_dir}")
        
        # Get all JSON files in current directory
        json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        
        if not json_files:
            print(f"[WARNING] No JSON files found in {input_dir}")
            continue
        
        # Process each JSON file
        for json_file in json_files:
            file_path = os.path.join(input_dir, json_file)
            print(f"[INFO] Reading file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    pages = json.load(f)
                    
                    # Add all pages and links
                    for page in pages:
                        src = page.get('url')
                        if not src:
                            continue
                            
                        # 只统计未处理过的URL
                        if src not in processed_urls:
                            total_pages += 1
                            processed_urls.add(src)
                            
                        outlinks = page.get('outlinks', [])
                        for dst in outlinks:
                            if dst != src:  # Avoid self-loops
                                G.add_edge(src, dst)
                                total_links += 1
            except Exception as e:
                print(f"[ERROR] Failed to process {file_path}: {str(e)}")
    
    print(f"[INFO] Web graph construction completed:")
    print(f"      - Total unique pages: {total_pages}")
    print(f"      - Total links: {total_links}")
    print(f"      - Graph nodes: {G.number_of_nodes()}")
    print(f"      - Graph edges: {G.number_of_edges()}")
    
    return G

def pagerank(graph, alpha=0.85, tol=1e-6, max_iter=100):
    """
    PageRank algorithm implementation using sparse matrices
    """
    nodes = list(graph.nodes())
    N = len(nodes)
    
    # Create node to index mapping
    node_to_index = {node: i for i, node in enumerate(nodes)}
    
    # Create sparse adjacency matrix
    rows, cols = [], []
    for src, dst in graph.edges():
        rows.append(node_to_index[src])
        cols.append(node_to_index[dst])
    
    # Create sparse matrix
    M = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(N, N))
    
    # Normalize columns
    col_sums = M.sum(axis=0)
    col_sums[col_sums == 0] = 1  # Avoid division by zero
    M = M.multiply(1 / col_sums)
    
    # Initialize rank vector
    r = np.ones(N) / N
    
    # Power iteration
    for _ in range(max_iter):
        r_new = alpha * (M @ r) + (1 - alpha) / N
        if np.linalg.norm(r_new - r, 1) < tol:
            break
        r = r_new
    
    # Apply logarithmic normalization with scaling factor
    scaling_factor = 10000
    normalized_scores = np.log1p(r * scaling_factor)
    
    # Map scores to 0-1 range
    min_score = np.min(normalized_scores)
    max_score = np.max(normalized_scores)
    if max_score > min_score:
        normalized_scores = (normalized_scores - min_score) / (max_score - min_score)
    
    # Return normalized scores
    return {nodes[i]: float(f"{normalized_scores[i]:.8f}") for i in range(N)}

def save_pagerank_to_json(pagerank_scores, output_path):
    """
    Save PageRank results to JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pagerank_scores, f, indent=2, ensure_ascii=False)
    print(f"[INFO] PageRank scores saved to: {output_path}")

def process_main_directory(main_dir, output_dir):
    """
    Process all JSON files in main directory and its subdirectories
    
    Args:
        main_dir: Main directory path containing all data
        output_dir: Output directory path for saving PageRank results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all directories containing JSON files
    input_dirs = get_all_json_dirs(main_dir)
    print(f"[INFO] Found {len(input_dirs)} directories with JSON files")
    
    # Build graph from all directories
    G = build_graph_from_directories(input_dirs)
    
    # Check if graph is empty
    if G.number_of_nodes() == 0:
        print("[ERROR] Built graph is empty, please check if input path is correct")
        print(f"Current input path: {main_dir}")
        exit(1)
    
    # Calculate PageRank
    scores = pagerank(G)
    
    # Save results
    output_file = os.path.join(output_dir, 'pagerank_scores.json')
    save_pagerank_to_json(scores, output_file)

if __name__ == "__main__":
    # Main directory containing all data
    main_dir = './data/raw/website'
    output_dir = './data/pagerank'
    
    # Process all directories
    process_main_directory(main_dir, output_dir)
