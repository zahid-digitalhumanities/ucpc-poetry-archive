# scripts/export_training_data.py
"""
Export clean training data for poet classifier
"""

import sys
import os
import pandas as pd
import json
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your database config
try:
    from models.base import get_db_connection
except ImportError:
    # Fallback connection
    def get_db_connection():
        import psycopg2
        return psycopg2.connect(
            database="ucpc_v3_db",
            user="postgres",
            password="your_password",
            host="localhost",
            port="5432"
        )

def export_training_data(output_csv="training_data_export.csv"):
    """Export clean training data to CSV"""
    
    print("📤 Exporting training data...")
    
    conn = get_db_connection()
    
    # Use cursor with dictionary support
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
    SELECT 
        t.id,
        t.poet_id,
        p.name as poet_name,
        p.name_urdu as poet_name_urdu,
        t.text_urdu,
        t.normalized_text,
        t.verse_count,
        t.integrity_status,
        t.title_urdu,
        COALESCE(t.normalized_text, t.text_urdu) as training_text
    FROM texts t
    JOIN poets p ON t.poet_id = p.id
    WHERE t.form = 'ghazal'
      AND t.is_deleted = FALSE
      AND t.integrity_status IN ('clean', 'merged')
      AND t.text_urdu IS NOT NULL
      AND LENGTH(t.text_urdu) > 100
    ORDER BY p.name, t.id
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Convert to DataFrame
    df = pd.DataFrame(rows)
    
    cursor.close()
    conn.close()
    
    if df.empty:
        print("❌ No data found!")
        return None
    
    print(f"  Exported {len(df)} ghazals")
    print(f"  Poets: {df['poet_name'].nunique()}")
    
    # Show distribution
    print("\n📊 Poet distribution:")
    poet_counts = df['poet_name'].value_counts()
    for poet, count in poet_counts.head(15).items():
        bar = "█" * (count // 10) if count // 10 > 0 else "▌"
        print(f"  {poet[:25]:25} {count:4} {bar}")
    
    # Save to CSV (use correct encoding for Windows)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✅ Saved to: {output_csv}")
    
    # Also save metadata
    metadata = {
        'total_samples': int(len(df)),
        'num_poets': int(df['poet_name'].nunique()),
        'poets': {k: int(v) for k, v in poet_counts.to_dict().items()},
        'date_exported': pd.Timestamp.now().isoformat()
    }
    
    metadata_path = output_csv.replace('.csv', '_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Metadata saved to: {metadata_path}")
    
    return df

if __name__ == "__main__":
    export_training_data()