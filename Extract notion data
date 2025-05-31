import requests
import json

# Replace these with your own values
NOTION_TOKEN = 'secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
DATABASE_ID = ''
NOTION_VERSION = '2022-06-28'  # Or the latest version

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def get_database_data(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    results = []
    has_more = True
    next_cursor = None

    while has_more:
        payload = {}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Error querying database: {response.status_code}")
            print(response.text)
            return []

        data = response.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    return results

def save_to_json(data, filename='notion_data.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Data saved to {filename}")

if __name__ == "__main__":
    notion_data = get_database_data(DATABASE_ID)
    save_to_json(notion_data)
