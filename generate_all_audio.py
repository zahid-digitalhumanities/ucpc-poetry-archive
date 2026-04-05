import os
from models.listen_model import generate_audio
from models.ghazal_model import get_all_ghazals

def main():
    print("🚀 Starting audio generation...\n")

    ghazals = get_all_ghazals()
    total = len(ghazals)
    created = 0
    skipped = 0

    for g in ghazals:
        text_id = g["id"]
        print(f"➡️ Processing ID: {text_id}")

        filename = f"static/audio/{text_id}.mp3"
        if os.path.exists(filename):
            print("⚡ Already exists — skipping\n")
            skipped += 1
            continue

        result = generate_audio(
            text_id,
            g.get("text_urdu", ""),
            g.get("text_english", "")
        )

        if result:
            print("✅ Created\n")
            created += 1
        else:
            print("❌ Failed\n")

    print("🎯 DONE\n")
    print(f"Total Ghazals: {total}")
    print(f"Created Audio: {created}")
    print(f"Skipped (cached): {skipped}")

if __name__ == "__main__":
    main()