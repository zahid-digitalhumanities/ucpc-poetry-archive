# scripts/check_training_data_quality.py
"""
Training Data Quality Checker
Run this before training to ensure data quality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
import pandas as pd

def check_data_quality():
    """Comprehensive data quality report"""
    
    conn = get_db_connection()
    
    print("="*70)
    print("📊 TRAINING DATA QUALITY REPORT")
    print("="*70)
    
    # 1. Overall corpus stats
    print("\n📈 CORPUS STATISTICS:")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_ghazals,
            COUNT(CASE WHEN integrity_status = 'clean' THEN 1 END) as clean_ghazals,
            COUNT(CASE WHEN is_deleted = TRUE THEN 1 END) as deleted_ghazals,
            COUNT(DISTINCT poet_id) as total_poets
        FROM texts
        WHERE form = 'ghazal'
    """)
    stats = cur.fetchone()
    print(f"  Total ghazals: {stats['total_ghazals']:,}")
    print(f"  Clean ghazals: {stats['clean_ghazals']:,}")
    print(f"  Deleted ghazals: {stats['deleted_ghazals']:,}")
    print(f"  Total poets: {stats['total_poets']}")
    
    # 2. Poets with sufficient data
    print("\n📚 POETS WITH SUFFICIENT DATA (≥30 ghazals):")
    cur.execute("""
        SELECT 
            p.id,
            p.name,
            p.name_urdu,
            COUNT(t.id) as ghazal_count
        FROM poets p
        JOIN texts t ON p.id = t.poet_id
        WHERE t.form = 'ghazal'
          AND t.is_deleted = FALSE
          AND t.integrity_status IN ('clean', 'merged')
          AND t.text_urdu IS NOT NULL
          AND LENGTH(t.text_urdu) > 100
        GROUP BY p.id, p.name, p.name_urdu
        HAVING COUNT(t.id) >= 30
        ORDER BY ghazal_count DESC
    """)
    
    poets = cur.fetchall()
    print(f"  Found {len(poets)} poets with ≥30 ghazals")
    
    for poet in poets:
        bar = "█" * (poet['ghazal_count'] // 20)
        print(f"  {poet['name']:25} {poet['ghazal_count']:4} {bar}")
    
    # 3. Text length distribution
    print("\n📏 TEXT LENGTH DISTRIBUTION:")
    cur.execute("""
        SELECT 
            LENGTH(text_urdu) as text_length,
            LENGTH(normalized_text) as norm_length
        FROM texts
        WHERE form = 'ghazal'
          AND is_deleted = FALSE
          AND integrity_status = 'clean'
          AND text_urdu IS NOT NULL
    """)
    lengths = cur.fetchall()
    
    if lengths:
        raw_lengths = [l['text_length'] for l in lengths if l['text_length']]
        if raw_lengths:
            import numpy as np
            print(f"  Min length: {np.min(raw_lengths)} chars")
            print(f"  Max length: {np.max(raw_lengths)} chars")
            print(f"  Mean length: {np.mean(raw_lengths):.0f} chars")
            print(f"  Median length: {np.median(raw_lengths):.0f} chars")
    
    # 4. Class balance check
    print("\n⚖️ CLASS BALANCE:")
    cur.execute("""
        SELECT 
            p.name,
            COUNT(t.id) as count
        FROM poets p
        JOIN texts t ON p.id = t.poet_id
        WHERE t.form = 'ghazal'
          AND t.is_deleted = FALSE
          AND t.integrity_status = 'clean'
          AND t.text_urdu IS NOT NULL
          AND LENGTH(t.text_urdu) > 100
        GROUP BY p.name
        HAVING COUNT(t.id) >= 10
        ORDER BY count DESC
        LIMIT 15
    """)
    
    counts = cur.fetchall()
    if counts:
        max_count = counts[0]['count']
        min_count = counts[-1]['count']
        ratio = max_count / min_count if min_count > 0 else 0
        
        print(f"  Most represented: {counts[0]['name']} ({max_count} samples)")
        print(f"  Least represented: {counts[-1]['name']} ({min_count} samples)")
        print(f"  Imbalance ratio: {ratio:.1f}:1")
        
        if ratio > 10:
            print("  ⚠️ WARNING: High class imbalance! Consider using class weights.")
    
    # 5. Embedding coverage
    print("\n🔬 EMBEDDING COVERAGE:")
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN g.text_id IS NOT NULL THEN 1 ELSE 0 END) as has_embedding
        FROM texts t
        LEFT JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.form = 'ghazal'
          AND t.is_deleted = FALSE
          AND t.integrity_status = 'clean'
    """)
    emb_stats = cur.fetchone()
    
    if emb_stats['total'] > 0:
        coverage = (emb_stats['has_embedding'] / emb_stats['total']) * 100
        print(f"  Total clean ghazals: {emb_stats['total']}")
        print(f"  With embeddings: {emb_stats['has_embedding']}")
        print(f"  Coverage: {coverage:.1f}%")
        
        if coverage < 90:
            print("  ⚠️ WARNING: Low embedding coverage! Run backfill_embeddings.py")
    
    # 6. Duplicate check
    print("\n🔄 DUPLICATE ANALYSIS:")
    cur.execute("""
        SELECT 
            full_text_hash,
            COUNT(*) as dup_count
        FROM texts
        WHERE form = 'ghazal'
          AND is_deleted = FALSE
        GROUP BY full_text_hash
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    print(f"  Exact duplicate groups: {len(duplicates)}")
    
    # 7. Attribution conflicts
    print("\n⚠️ ATTRIBUTION CONFLICTS:")
    cur.execute("""
        SELECT 
            matla_hash,
            COUNT(DISTINCT poet_id) as poet_count,
            COUNT(*) as ghazal_count
        FROM texts
        WHERE form = 'ghazal'
          AND is_deleted = FALSE
          AND matla_hash IS NOT NULL
        GROUP BY matla_hash
        HAVING COUNT(DISTINCT poet_id) > 1
        LIMIT 10
    """)
    conflicts = cur.fetchall()
    print(f"  Matlas with multiple attributions: {len(conflicts)}")
    
    cur.close()
    conn.close()
    
    # 7. Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS:")
    print("="*70)
    
    if len(poets) < 3:
        print("  ❌ Not enough poets with sufficient data. Consider:")
        print("     - Lowering MIN_SAMPLES_PER_POET to 20")
        print("     - Including more poets from the corpus")
    
    if ratio > 10:
        print("  ⚠️ High class imbalance. Consider:")
        print("     - Using class_weight='balanced' in models")
        print("     - Undersampling majority classes")
    
    if coverage < 90:
        print("  ⚠️ Low embedding coverage. Run:")
        print("     python scripts/backfill_embeddings.py")
    
    if len(conflicts) > 0:
        print("  ⚠️ Attribution conflicts exist. Consider:")
        print("     - Reviewing conflicting matlas first")
        print("     - Excluding conflict records from training")
    
    return poets

if __name__ == "__main__":
    poets = check_data_quality()
    
    print("\n✅ Ready to train? Run:")
    print("   python models/ml/train_poet_classifier_v8.py")