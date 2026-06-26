import os
import sys
import json
import logging
import requests
from pathlib import Path

# Add project root to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
logger = logging.getLogger("webhook")

def main():
    if not config.MAKE_WEBHOOK_URL:
        logger.warning("MAKE_WEBHOOK_URL is not set. Skipping webhook trigger.")
        return

    # Find all JSON metadata files in output directory
    json_files = list(config.OUTPUT_DIR.glob("*.json"))
    if not json_files:
        logger.info("No metadata files found in output directory.")
        return

    repo = config.GITHUB_REPOSITORY
    if not repo:
        logger.warning("GITHUB_REPOSITORY not set. Webhook needs this to build raw URL.")
        return

    for meta_path in json_files:
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            filename = data.get("filename")
            if not filename:
                continue

            # Construct the raw GitHub URL
            # Use the commit SHA instead of 'main' to bypass GitHub's aggressive caching
            import subprocess
            try:
                commit_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
            except:
                commit_sha = 'main'
                
            raw_url = f"https://raw.githubusercontent.com/{repo}/{commit_sha}/output/{filename}"
            
            payload = {
                "video_url": raw_url,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "tags": data.get("tags", "")
            }

            logger.info(f"Triggering webhook for: {filename}")
            response = requests.post(config.MAKE_WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code in (200, 201, 202):
                logger.info(f"✅ Webhook triggered successfully: {response.status_code}")
                # Remove JSON so it's not triggered again if run locally
                meta_path.unlink()
            else:
                logger.error(f"❌ Webhook failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.exception(f"Error processing {meta_path.name}")

if __name__ == "__main__":
    main()
