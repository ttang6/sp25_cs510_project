import requests
import os
import time
import random
import base64
import rmp_config

OUTPUT_DIR = "./data/rmp_htmls"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 " \
             "Safari/537.36"

SID = rmp_config.SID

def encode_school_id(sid):
    school_str = f"School-{sid}"
    return base64.b64encode(school_str.encode()).decode()


def process(sid, output_dir=OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://www.ratemyprofessors.com/"
    }

    download_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.ratemyprofessors.com/"
    }

    cursor = ""
    has_next_page = True
    count = 8
    total_links = 0

    graphql_query = """
    query TeacherSearchPaginationQuery(
      $count: Int!
      $cursor: String
      $query: TeacherSearchQuery!
    ) {
      search: newSearch {
        teachers(query: $query, first: $count, after: $cursor) {
          edges {
            cursor
            node {
              id
              legacyId
              firstName
              lastName
              __typename
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
          resultCount
        }
      }
    }
    """

    school_id = encode_school_id(sid)

    while has_next_page:
        payload = {
            "query": graphql_query,
            "variables": {
                "count": count,
                "cursor": cursor,
                "query": {
                    "text": "",
                    "schoolID": school_id,
                    "fallback": True
                }
            }
        }

        print(f"Fetching professor list (cursor={cursor})...")
        try:
            response = requests.post(
                "https://www.ratemyprofessors.com/graphql",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            teachers = data.get("data", {}).get("search", {}).get("teachers", {})
            edges = teachers.get("edges", [])
            page_info = teachers.get("pageInfo", {})

            if not edges:
                print("No professors found, possibly at the end.")
                break

            for edge in edges:
                node = edge.get("node", {})
                legacy_id = node.get("legacyId")
                if legacy_id:
                    full_url = f"https://www.ratemyprofessors.com/professor/{legacy_id}"
                    total_links += 1

                    print(f"Fetching professor page {total_links}: {full_url}")
                    try:
                        prof_response = requests.get(full_url, headers=download_headers, timeout=10)
                        prof_response.raise_for_status()

                        output_path = os.path.join(output_dir, f"professor_{legacy_id}.html")
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(prof_response.text)
                        print(f"Saved to: {output_path} (Size: {os.path.getsize(output_path)} bytes)")

                        time.sleep(random.uniform(1, 3))

                    except requests.RequestException as e:
                        print(f"Failed to fetch {full_url}: {e}")
                        continue

            print(f"Processed {len(edges)} links this page, total: {total_links}")

            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor", "")
            print(f"hasNextPage: {has_next_page}, next cursor: {cursor}")

            time.sleep(random.uniform(1, 3))

        except requests.RequestException as e:
            print(f"Request failed: {e}")
            break
        except Exception as e:
            print(f"Parsing failed: {e}")
            break

    print(f"Finished! Total processed: {total_links} professor pages.")


if __name__ == "__main__":
    school_id = SID
    process(school_id)
