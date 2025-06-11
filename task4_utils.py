import os
import json

def output_all_plugins_to_txt(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        plugins = json.load(f)

    slugs = [plugin.get("slug") for plugin in plugins if plugin.get("slug")]

    with open(output_path, "w", encoding="utf-8") as f:
        for slug in slugs:
            f.write(f"{slug}\n")

    print(f"✅ Wrote {len(slugs)} plugin slugs to {output_path}")

def output_top_100_plugins_to_txt(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        plugins = json.load(f)

    top_plugins = plugins[:100]
    slugs = [plugin.get("slug") for plugin in top_plugins if plugin.get("slug")]

    with open(output_path, "w", encoding="utf-8") as f:
        for slug in slugs:
            f.write(f"{slug}\n")

    print(f"✅ Wrote top {len(slugs)} plugin slugs to {output_path}")

def read_plugins_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        slugs = [line.strip() for line in f.readlines() if line.strip()]
    return slugs
