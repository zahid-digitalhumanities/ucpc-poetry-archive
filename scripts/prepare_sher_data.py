# scripts/prepare_sher_data.py
# =========================================================
# UCPC — Sher-Level Dataset Builder (Research Grade)
# FIXED for dictionary cursor
# =========================================================

import sys
import os
import re
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.base import get_db_connection


# =========================================================
# TEXT CLEANING
# =========================================================
def normalize_urdu(text):
    """
    Normalize Urdu text for ML consistency
    """

    if not text:
        return ""

    text = str(text)

    # Remove extra spaces/newlines
    text = re.sub(r'\s+', ' ', text)

    # Remove tatweel
    text = text.replace('ـ', '')

    # Normalize Urdu chars
    replacements = {
        'ي': 'ی',
        'ك': 'ک',
        'ة': 'ہ',
        'ۀ': 'ہ',
        'ھ': 'ہ',
        'ؤ': 'و',
        'إ': 'ا',
        'أ': 'ا',
        'ٱ': 'ا'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


# =========================================================
# BUILD SHER DATASET
# =========================================================
def prepare_sher_dataset():

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 70)
    print("📚 UCPC SHER DATASET PREPARATION")
    print("=" * 70)

    # -----------------------------------------------------
    # Total ghazals - FIXED for dictionary cursor
    # -----------------------------------------------------
    cur.execute("""
        SELECT COUNT(*) as total
        FROM texts
        WHERE form = 'ghazal'
    """)

    row = cur.fetchone()
    # Handle both dict and tuple cursor
    if hasattr(row, 'keys'):
        total_ghazals = row['total']
    else:
        total_ghazals = row[0]

    print(f"\n📖 Total ghazals in DB: {total_ghazals}")

    # -----------------------------------------------------
    # Main query
    # -----------------------------------------------------
    cur.execute("""
        SELECT
            t.id AS text_id,
            t.poet_id,
            p.name,
            p.name_urdu,

            t.title_urdu,
            t.normalized_text,
            t.text_urdu,

            v.couplet_index,
            v.misra1_urdu,
            v.misra2_urdu,

            t.integrity_status,
            t.is_deleted

        FROM texts t

        JOIN poets p
            ON t.poet_id = p.id

        JOIN verses v
            ON t.id = v.text_id

        WHERE t.form = 'ghazal'

          AND t.poet_id IS NOT NULL

          AND (
                t.is_deleted = FALSE
                OR t.is_deleted IS NULL
          )

          AND v.misra1_urdu IS NOT NULL
          AND v.misra2_urdu IS NOT NULL

          AND LENGTH(v.misra1_urdu) > 1
          AND LENGTH(v.misra2_urdu) > 1

        ORDER BY t.id, v.couplet_index
    """)

    rows = cur.fetchall()

    print(f"🧾 Total verse rows fetched: {len(rows)}")

    # -----------------------------------------------------
    # Build dataset
    # -----------------------------------------------------
    data = []

    skipped = 0

    for r in rows:

        # Dict cursor (your database uses this)
        if hasattr(r, "keys"):

            text_id = r["text_id"]
            poet_id = r["poet_id"]
            poet_name = r["name"]
            poet_name_urdu = r["name_urdu"]

            title_urdu = r["title_urdu"]

            couplet_index = r["couplet_index"]

            misra1 = r["misra1_urdu"]
            misra2 = r["misra2_urdu"]

        # Tuple cursor (fallback)
        else:

            text_id = r[0]
            poet_id = r[1]
            poet_name = r[2]
            poet_name_urdu = r[3]

            title_urdu = r[4]

            couplet_index = r[7]

            misra1 = r[8]
            misra2 = r[9]

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------
        misra1 = normalize_urdu(misra1)
        misra2 = normalize_urdu(misra2)

        sher_text = f"{misra1}\n{misra2}".strip()

        # Skip tiny/noisy samples
        if len(sher_text) < 15:
            skipped += 1
            continue

        # Skip obvious garbage
        if sher_text.count("؟") > 5:
            skipped += 1
            continue

        data.append({

            "text_id": text_id,

            "poet_id": poet_id,

            "poet_name": poet_name,

            "poet_name_urdu": poet_name_urdu,

            "title_urdu": title_urdu,

            "couplet_index": couplet_index,

            "sher_text": sher_text,

            # ML helper fields
            "token_count": len(sher_text.split()),

            "char_count": len(sher_text)
        })

    cur.close()
    conn.close()

    # -----------------------------------------------------
    # DataFrame
    # -----------------------------------------------------
    df = pd.DataFrame(data)

    if len(df) == 0:

        print("\n❌ No usable data found.")
        return pd.DataFrame()

    # -----------------------------------------------------
    # Dataset stats
    # -----------------------------------------------------
    unique_ghazals = df["text_id"].nunique()
    unique_poets = df["poet_id"].nunique()

    print("\n" + "=" * 70)
    print("📊 DATASET SUMMARY")
    print("=" * 70)

    print(f"✅ Sher samples: {len(df)}")
    print(f"✅ Unique ghazals: {unique_ghazals}")
    print(f"✅ Unique poets: {unique_poets}")
    print(f"⚠️ Skipped noisy rows: {skipped}")

    # -----------------------------------------------------
    # Poet distribution
    # -----------------------------------------------------
    print("\n🎭 Top poets by sher count:\n")

    poet_counts = (
        df["poet_name"]
        .value_counts()
        .head(15)
    )

    for poet, count in poet_counts.items():

        print(f"  • {poet}: {count} shers")

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------
    output_path = "sher_dataset.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print(f"💾 Saved dataset: {output_path}")
    print("=" * 70)

    return df


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    df = prepare_sher_dataset()

    if len(df) > 0:

        print("\n🚀 Dataset ready for training.")
        print("Next step:")
        print("python models/ml/train_poet_classifier_v9.py")

    else:

        print("\n❌ Dataset creation failed.")