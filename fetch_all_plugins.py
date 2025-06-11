import requests
import json
import os
import time
from concurrent.futures import Executor, ThreadPoolExecutor, as_completed

# Load config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config", "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

API_URL = config["wp_api_url"]
# Validate PER_PAGE
PER_PAGE = config["wp_api_request_limit"]
if PER_PAGE > 100:
    print(f"⚠️ wp_api_request_limit {PER_PAGE} is too high. Setting it to 100.")
    PER_PAGE = 100
TOTAL_PAGES = config["wp_api_total_pages"]


def fetch_page(page):
    params = {
        "action": "query_plugins",
        "request[page]": page,
        "request[per_page]": PER_PAGE,
        "request[browse]": "popular",  # Optional: to get popular plugins first
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        plugins = data.get("plugins", [])

        result = [
            {"name": plugin.get("name"), "slug": plugin.get("slug")}
            for plugin in plugins
        ]

        print(f"✅ Fetched page {page} with {len(result)} plugins")

        return result
    except Exception as e:
        print(f"❌ Error fetching page {page}: {e}")
        return [], 0

def fetch_plugin_details(slug):
    params = {
        "action": "plugin_information",
        "request[slug]": slug,
        "request[fields][sections]": False,
        "request[fields][reviews]": False,
        "request[fields][downloaded]": True,
        "request[fields][active_installs]": True,
        "request[fields][last_updated]": True,
        "request[fields][rating]": True,
        "request[fields][homepage]": True,
        "request[fields][versions]": True,
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"    🔍 Fetched details for plugin '{slug}'")
        return data
    except Exception as e:
        print(f"❌ Error fetching details for plugin '{slug}': {e}")
        return {}

def fetch_all_plugins():
    all_plugins_details = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for page in range(1, TOTAL_PAGES + 1):
            plugins = fetch_page(page)
            if not plugins:
                print("no more plugins found, stopping ....")
                break

            # Submit tasks for fetching details concurrently
            futures = {
                executor.submit(fetch_plugin_details, p["slug"]): p["slug"]
                for p in plugins
                if p.get("slug")
            }

            for future in as_completed(futures):
                details = future.result()
                if details:
                    all_plugins_details.append(details)

                # Sleep a bit between pages to avoid hitting API rate limits too hard
            time.sleep(0.5)

    # Save to db/plugins.txt
    output_path = os.path.join(BASE_DIR, "db", "plugins.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_plugins_details, f, indent=4)

    print(f"\n✅ Saved {len(all_plugins_details)} plugins to {output_path}")

def update_all_plugins():
    all_plugins_details = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for page in range(1, TOTAL_PAGES + 1):
            plugins = fetch_page(page)
            if not plugins:
                print("No more plugins found. Stopping...")
                break

            futures = {
                executor.submit(fetch_plugin_details, p["slug"]): p["slug"]
                for p in plugins
                if p.get("slug")
            }

            for future in as_completed(futures):
                details = future.result()
                if details:
                    all_plugins_details.append(details)

            time.sleep(0.5)

    save_plugins(all_plugins_details, "plugins.json")
    print(f"\n✅ Updated all plugins ({len(all_plugins_details)}) to plugins.json")

def update_top_100_plugins():
    top_plugins_details = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        plugins = fetch_page(1)  # only fetch first page

        futures = {
            executor.submit(fetch_plugin_details, p["slug"]): p["slug"]
            for p in plugins
            if p.get("slug")
        }

        for future in as_completed(futures):
            details = future.result()
            if details:
                top_plugins_details.append(details)

    # Load existing plugins.json if it exists
    existing_path = os.path.join(BASE_DIR, "db", "plugins.json")
    if os.path.exists(existing_path):
        with open(existing_path, "r", encoding="utf-8") as f:
            existing_plugins = json.load(f)
    else:
        existing_plugins = []

    print("\n🔍 Existing top slugs:")
    for plugin in existing_plugins[:len(top_plugins_details)]:
        print(f" - {plugin.get('slug')}")

    print("\n✅ New top slugs:")
    for plugin in top_plugins_details:
        print(f" - {plugin.get('slug')}")

    # Replace the top N plugins in existing list with the new top plugins
    remaining_plugins = existing_plugins[len(top_plugins_details):]
    updated_plugins = top_plugins_details + remaining_plugins

    # Plugin count consistency check
    if len(existing_plugins) != len(updated_plugins):
        print(f"\n⚠️ Plugin count changed! Before: {len(existing_plugins)}, After: {len(updated_plugins)}")
    else:
        print(f"\n✅ Plugin count consistent. ({len(updated_plugins)} plugins)")

    # Save back to plugins.json
    save_plugins(updated_plugins, "plugins.json")
    print(
        f"\n✅ Updated top 100 plugins ({len(top_plugins_details)}) to plugins.json"
    )

def save_plugins(plugins, filename):
    output_path = os.path.join(BASE_DIR, "db", filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(plugins, f, indent=4)

if __name__ == "__main__":
    fetch_all_plugins()
