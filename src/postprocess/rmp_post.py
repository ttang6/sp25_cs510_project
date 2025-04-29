import re
from bs4 import BeautifulSoup
import json
import os
import glob

# Define file paths
HTML_DIR = './data/RMP_Htmls'
OUTPUT_PATH = './data/rmp/uiuc_professor_info.json'

# Define fields to extract
fields = [
    'firstName',
    'lastName',
    'department',
    'numRatings',
    'avgRating',
    'avgDifficulty',
    'wouldTakeAgainPercent',
    'legacyId'
]

def extract_professor_info(html_file_path):
    """
    从单个 HTML 文件中提取教授信息
    html_file_path: HTML 文件路径
    返回: 提取的教授信息字典
    """
    # 读取 HTML 文件
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"File not found: {html_file_path}")
        return None

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找包含 window.__RELAY_STORE__ 的 script 标签
    script_tags = soup.find_all('script')
    relay_store_content = None
    for script in script_tags:
        if script.string and 'window.__RELAY_STORE__' in script.string:
            relay_store_content = script.string
            break

    if not relay_store_content:
        print(f"window.__RELAY_STORE__ data not found in {html_file_path}")
        return None

    # 使用正则表达式提取 window.__RELAY_STORE__ 内容
    match = re.search(r'window.__RELAY_STORE__ = (\{.*?\});', relay_store_content, re.DOTALL)
    if not match:
        print(f"Failed to parse window.__RELAY_STORE__ data in {html_file_path}")
        return None

    # 将 JSON 字符串解析为 Python 字典
    relay_store_json = match.group(1)
    try:
        relay_store = json.loads(relay_store_json)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in {html_file_path}: {e}")
        return None

    # 查找主教授记录
    main_professor = None
    for key, value in relay_store.items():
        if isinstance(value, dict) and value.get('__typename') == 'Teacher':
            main_professor = {}
            for field in fields:
                main_professor[field] = value.get(field, 'N/A' if field in ['firstName', 'lastName', 'department', 'legacyId'] else -1)
            break

    if not main_professor:
        print(f"Main professor info not found in {html_file_path} (no __typename: Teacher record)")
        return None

    # 提取 Top Tags
    top_tags = []
    tags_container = soup.find('div', class_='TeacherTags__TagsContainer-sc-16vmh1y-0')
    if tags_container:
        tag_elements = tags_container.find_all('span', class_='Tag-bs9vf4-0')
        top_tags = [tag.get_text(strip=True) for tag in tag_elements]
    else:
        top_tags = []

    # 构建教授信息字典
    professor_data = {
        "professor": {
            "id": main_professor.get('legacyId', 'N/A'),
            "firstName": main_professor.get('firstName', 'N/A'),
            "lastName": main_professor.get('lastName', 'N/A'),
            "fullName": f"{main_professor.get('firstName', 'N/A')} {main_professor.get('lastName', 'N/A')}".strip(),
            "department": main_professor.get('department', 'N/A'),
            "ratings": {
                "numRatings": main_professor.get('numRatings', -1),
                "avgRating": main_professor.get('avgRating', -1),
                "avgDifficulty": main_professor.get('avgDifficulty', -1),
                "wouldTakeAgainPercent": main_professor.get('wouldTakeAgainPercent', -1)
            },
            "tags": top_tags
        }
    }

    return professor_data

def process_all_professors(html_dir=HTML_DIR, output_path=OUTPUT_PATH):
    """
    处理所有教授的 HTML 文件，提取信息并保存到 JSON
    html_dir: HTML 文件目录
    output_path: 输出 JSON 文件路径
    """
    # 获取所有 HTML 文件
    html_files = glob.glob(os.path.join(html_dir, "*.html"))
    if not html_files:
        print(f"No HTML files found in {html_dir}")
        return

    print(f"Found {len(html_files)} HTML files in {html_dir}")

    # 存储所有教授信息的列表
    all_professors = []
    existing_ids = set()  # 存储已存在的教授 ID

    # 遍历每个 HTML 文件
    for html_file in html_files:
        print(f"Processing file: {html_file}")
        professor_data = extract_professor_info(html_file)
        if not professor_data:
            print(f"Skipped file due to error: {html_file}")
            continue

        # 检查教授 ID 是否重复
        professor_id = professor_data['professor']['id']
        if professor_id in existing_ids:
            print(f"Professor ID {professor_id} already exists, skipping...")
            continue

        # 添加到列表并更新 ID 集合
        existing_ids.add(professor_id)
        all_professors.append(professor_data)
        print(f"Extracted info for professor ID: {professor_id}")

    # 构建最终 JSON 结构
    output_data = {
        "professors": all_professors
    }

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存到 JSON 文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to: {output_path}")
        print(f"Total professors processed: {len(all_professors)}")
    except Exception as e:
        print(f"Failed to save JSON file: {e}")

# 运行代码
if __name__ == "__main__":
    process_all_professors()