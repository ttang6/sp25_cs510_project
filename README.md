# CS 510 A1 SP25: Advanced Information Retrieval Final Project

A campus resource search platform based on Elasticsearch.

## Features

- Multiple search methods and data sources
- PageRank algorithm integration for web ranking
- Search history support
- Real-time search suggestions
- Detailed search result scoring

## System Requirements

- Python 3.10 or higher
- Elasticsearch 9.0 or higher
- Modern browsers (Chrome, Firefox, Safari, etc.)

## Project Structure

```
├── data/               # Data files
│   ├── pagerank/       # PageRank data
│   └── raw/            # JSON data
│       ├── rmp/        # RateMyProfessor data
│       └── website/    # Web data
├── src/                # Source code
│   ├── config/         # Authentication settings
│   ├── crawlers/       # Crawler module
│   ├── elasticsearch/  # ES tools
│   ├── pagerank/       # PageRank tools
│   └── postprocess/    # Data preprocessing
├── static/             # Static resources
│   └── templates/      # HTML templates
├── tests/              # Evalution code
│   ├── benchmark/      # Basic test
│   ├── locust/         # Stress test
│   └── data/           # Data files
├── requirements.txt    # Project dependencies
├── build.py            # Quick initialization tool
└── main.py             # Main application
```

## Installation

1. Clone the repository:
```bash
git clone git@github.com:ttang6/sp25_cs510_project.git
cd sp25_cs510_project
```

2. Create and activate virtual environment (recommended):
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Elasticsearch:
   - Create an `es_config` file in `/src/config` with your Elasticsearch key:
     ```
     KEY = your_elasticsearch_key
     ```
   - Ensure Elasticsearch service is running
   - Default configuration: `https://localhost:9200`

## Usage

1. Run the service:
If you're using my data, you can run
```bash
python build.py
```
to automatically initialize Elasticsearch indices and import data, then run
```bash
python main.py
```
to start the service

2. Access the application:
   - Open browser and visit `http://127.0.0.1:5000`
   - Enter keywords in the search box
   - Choose search type

3. Search features:
   - Standard search: search across all indices
   - General word search: cross-index search
   - Index search: search specific indices
   - Search history viewing
   - Professor ratings from students

4. Advanced features:
   - Click "Show detailed" to view detailed search scores
   - Pagination support for search results

## Development Guide

1. Crawler Configuration:
   - For `web_crawler.py`: Create a `web_config` file in `/src/config` with target domain:
     ```
     URL = your_target_domain
     ```
   - For `rmp_crawler.py`: Create a `rmp_config` file in `/src/config` with school ID:
     ```
     SID = your_school_id
     ```

2. Data Processing:
   - Data stored in `/data/raw`, each subfolder for one data type
   - Run `postprocess` tools for data preprocessing if needed
   - Adjust tags in `create_index_data.py` based on JSON files
   - Run `create_index_data.py`, `create_index_prof.py` to create indices

3. Data Indexing:
   - Run `bulk_index_data.py`, `bulk_index_prof.py` to import
   - Supports batch import and incremental updates

4. PageRank Calculation:
   - Run `pagerank_pipeline.py` to calculate page rankings
   - Results saved in `data/pagerank/` directory
   - Run `create_index_p.py` to create indices
   - Run `bulk_index_o.py` to import

5. Search Optimization:
   - Multi-field search support
   - PageRank score integration
   - Real-time search suggestions

## Common Issues

1. Elasticsearch Connection Issues:
   - Check if Elasticsearch service is running
   - Verify connection configuration
   - Confirm authentication credentials

2. No Search Results:
   - Verify indices are created
   - Check search keywords
   - Validate index data integrity

## Known Bugs

1. Pagination Error:
   - When search results exceed 10,000 entries, the last page navigation will fail