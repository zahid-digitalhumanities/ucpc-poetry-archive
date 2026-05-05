import os
from pathlib import Path

BASE_PATH = Path(r"E:\latest_app\ucpc-poetry-archive-main\dataset")

for poet_dir in BASE_PATH.iterdir():
    if not poet_dir.is_dir():
        continue

    ur_dir = poet_dir / "ur"
    if not ur_dir.is_dir():
        print(f"Skipping {poet_dir.name}: no 'ur' folder")
        continue

    ghazal_files = [f for f in ur_dir.iterdir() if f.is_file()]
    if not ghazal_files:
        print(f"No files found in {ur_dir}")
        continue

    ghazal_files.sort()

    output_file = ur_dir / f"{poet_dir.name}_combined.txt"

    with open(output_file, "w", encoding="utf-8") as out:
        for idx, file_path in enumerate(ghazal_files):
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                # Write opening marker
                out.write("###GHZ###\n")
                # Write ghazal content
                out.write(content)
                # If not the last ghazal, add a newline so next marker appears on its own line
                # (Do not add extra blank line)
                if idx < len(ghazal_files) - 1:
                    out.write("\n")
            except Exception as e:
                print(f"  Error reading {file_path.name}: {e}")

    print(f"Created: {output_file}\n")

print("All done.")