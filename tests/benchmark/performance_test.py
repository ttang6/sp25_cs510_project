from elasticsearch import Elasticsearch
import logging
import time
import random
import statistics
from typing import List, Dict, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchBenchmark:
    def __init__(self, host: str = "https://localhost:9200", api_key: str = 'M5KBpgGq4Gx1YOnmoFkp'):
        """Initialize Elasticsearch client and benchmark parameters"""
        self.es = Elasticsearch(
            [host],
            basic_auth=("elastic", api_key),
            verify_certs=False,
            ssl_show_warn=False
        )
        self.queries = []
        self.results = []
        
    def load_queries(self, file_path: str) -> None:
        """Load queries from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.queries = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.queries)} queries from {file_path}")
        except Exception as e:
            logger.error(f"Error loading queries: {e}")
            raise

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a single search query and measure time"""
        try:
            start_time = time.time()
            
            response = self.es.search(
                index="*",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content^2", "anchor_texts"]
                        }
                    },
                    "size": 10
                }
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "execution_time": execution_time,
                "total_hits": response["hits"]["total"]["value"],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing query '{query}': {e}")
            return {
                "query": query,
                "execution_time": -1,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_benchmark(self, num_queries: int = 100000, iterations: int = 3) -> None:
        """Run benchmark with specified number of queries and iterations"""
        if not self.queries:
            raise ValueError("No queries loaded. Please load queries first.")
        
        logger.info(f"Starting benchmark with {num_queries} queries, {iterations} iterations")
        
        queries_per_iteration = num_queries // iterations
        
        for iteration in range(iterations):
            logger.info(f"Starting iteration {iteration + 1}/{iterations}")
            iteration_results = []
            iteration_start_time = time.time()
            
            for i in range(queries_per_iteration):
                if (i + 1) % 1000 == 0:
                    elapsed_time = time.time() - iteration_start_time
                    queries_per_second = (i + 1) / elapsed_time
                    logger.info(f"Processed {i + 1}/{queries_per_iteration} queries in iteration {iteration + 1} "
                              f"({queries_per_second:.2f} queries/second)")
                
                query = random.choice(self.queries)
                result = self.execute_query(query)
                iteration_results.append(result)
            
            iteration_time = time.time() - iteration_start_time
            logger.info(f"Completed iteration {iteration + 1} in {iteration_time:.2f} seconds "
                       f"({queries_per_iteration/iteration_time:.2f} queries/second)")
            
            self.results.append(iteration_results)
            
        self._analyze_results()

    def _analyze_results(self) -> None:
        """Analyze benchmark results"""
        all_times = []
        successful_queries = 0
        failed_queries = 0
        
        for iteration in self.results:
            for result in iteration:
                if result["execution_time"] > 0:
                    all_times.append(result["execution_time"])
                    successful_queries += 1
                else:
                    failed_queries += 1
        
        if not all_times:
            logger.error("No successful queries to analyze")
            return
        
        analysis = {
            "total_queries": successful_queries + failed_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "min_time": min(all_times),
            "max_time": max(all_times),
            "mean_time": statistics.mean(all_times),
            "median_time": statistics.median(all_times),
            "std_dev": statistics.stdev(all_times) if len(all_times) > 1 else 0,
            "percentiles": {
                "p50": statistics.median(all_times),
                "p90": sorted(all_times)[int(len(all_times) * 0.9)],
                "p95": sorted(all_times)[int(len(all_times) * 0.95)],
                "p99": sorted(all_times)[int(len(all_times) * 0.99)]
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"benchmark_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis": analysis,
                "raw_results": self.results
            }, f, indent=2)
    
        print("\n=== Benchmark Results Summary ===")
        print(f"Total Queries: {analysis['total_queries']}")
        print(f"Successful Queries: {analysis['successful_queries']}")
        print(f"Failed Queries: {analysis['failed_queries']}")
        print("\nResponse Time Statistics (ms):")
        print(f"Min: {analysis['min_time']:.2f}")
        print(f"Max: {analysis['max_time']:.2f}")
        print(f"Mean: {analysis['mean_time']:.2f}")
        print(f"Median: {analysis['median_time']:.2f}")
        print(f"Std Dev: {analysis['std_dev']:.2f}")
        print("\nPercentiles (ms):")
        print(f"50th: {analysis['percentiles']['p50']:.2f}")
        print(f"90th: {analysis['percentiles']['p90']:.2f}")
        print(f"95th: {analysis['percentiles']['p95']:.2f}")
        print(f"99th: {analysis['percentiles']['p99']:.2f}")
        print(f"\nDetailed results saved to: {results_file}")

def main():
    # Initialize benchmark
    benchmark = SearchBenchmark()
    
    # Load queries
    benchmark.load_queries("tests/data/benchmark_queries.txt")
    
    # Run benchmark with 100,000 queries
    benchmark.run_benchmark(num_queries=100000, iterations=3)

if __name__ == "__main__":
    main()