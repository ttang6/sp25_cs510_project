import json
import os
import numpy as np
import networkx as nx

def build_graph_from_crawl(crawl_json_path):
    """
    从爬虫结果中构建网页图，边表示超链接
    """
    with open(crawl_json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    G = nx.DiGraph()
    for page in pages:
        src = page.get('url')
        if not src:
            continue
        outlinks = page.get('outlinks', [])
        for dst in outlinks:
            if dst != src:  # 避免自环
                G.add_edge(src, dst)

    print(f"[INFO] 构建完成网页图：{G.number_of_nodes()} 个页面，{G.number_of_edges()} 条链接")
    return G


def pagerank(graph, alpha=0.85, tol=1e-6, max_iter=100):
    """
    PageRank 算法实现
    """
    nodes = list(graph.nodes())
    N = len(nodes)

    M = nx.to_numpy_array(graph, nodelist=nodes, dtype=float)
    for i in range(N):
        if M[i].sum() == 0:
            M[i] = np.ones(N) / N  # 悬空节点：平均分散
        else:
            M[i] /= M[i].sum()
    M = M.T

    r = np.ones(N) / N  # 初始化 rank 向量
    for _ in range(max_iter):
        r_new = alpha * (M @ r) + (1 - alpha) / N
        if np.linalg.norm(r_new - r, 1) < tol:
            break
        r = r_new

    return {nodes[i]: float(r[i]) for i in range(N)}


def save_pagerank_to_json(pagerank_scores, output_path):
    """
    保存 PageRank 结果为 JSON 文件
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pagerank_scores, f, indent=2, ensure_ascii=False)
    print(f"[INFO] PageRank 分数已保存到：{output_path}")


if __name__ == "__main__":
    # 修改为你的爬虫结果文件路径
    crawl_path = './data/rawJSON/grainger_20250502_112300.json'
    output_path = './data/pagerank/pagerank_scores.json'

    G = build_graph_from_crawl(crawl_path)
    scores = pagerank(G)
    save_pagerank_to_json(scores, output_path)
