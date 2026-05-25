import json
import os
from datetime import datetime

def main():
    print("🚀 Running Job Agent")

    jobs = [
        {
            "title": "SQL Server DBA (Sample)",
            "company": "Demo Corp",
            "link": "https://example.com",
            "source": "system",
            "score": 10
        }
    ]

    data = {
        "generated_at": str(datetime.now()),
        "jobs": jobs
    }

    # FORCE ROOT PATH
    file_path = os.path.join(os.getcwd(), "jobs.json")

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ CREATED:", file_path)
    print("📄 FILE EXISTS:", os.path.exists(file_path))


if __name__ == "__main__":
    main()
