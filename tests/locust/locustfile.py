from locust import HttpUser, task, between, events
import random
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locust初始化时的回调"""
    logger.info("Locust test environment initialized")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的回调"""
    logger.info("Starting load test...")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的回调"""
    logger.info("Load test finished")

class SearchUser(HttpUser):
    # 设置用户行为间隔时间（秒）
    wait_time = between(1, 3)
    
    def on_start(self):
        """初始化用户数据"""
        logger.info(f"User {id(self)} started")
        try:
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 构建查询文件的完整路径
            query_file = os.path.join(os.path.dirname(current_dir), "data", "benchmark_queries.txt")
            logger.info(f"Loading queries from: {query_file}")
            
            # 加载测试查询
            with open(query_file, "r", encoding="utf-8") as f:
                self.queries = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.queries)} test queries")
        except Exception as e:
            logger.error(f"Failed to load queries: {e}")
            raise
    
    def on_stop(self):
        """用户停止时的回调"""
        logger.info(f"User {id(self)} stopped")
    
    @task
    def standard_search(self):
        """执行标准搜索"""
        query = random.choice(self.queries)
        logger.info(f"User {id(self)} executing search with query: {query}")
        
        with self.client.get(
            f"/search?q={query}&type=standard",
            name="/search?type=standard",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response_time = response.elapsed.total_seconds()
                logger.info(f"Search completed in {response_time:.2f} seconds")
                # 检查响应时间
                if response_time > 2:
                    logger.warning(f"Response time too long: {response_time:.2f} seconds")
                    response.failure("Response time too long")
            else:
                logger.error(f"Search failed with status code: {response.status_code}")
                response.failure(f"Failed with status code: {response.status_code}") 