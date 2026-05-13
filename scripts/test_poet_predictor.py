# scripts/test_poet_predictor.py
"""
Test the poet prediction system with known ghazals
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ai_engine.poet_prediction_ai_v2 import predict_poet_from_text
from models.base import get_db_connection

# Sample test ghazals by known poets
TEST_GHAZALS = {
    "Mirza Ghalib": """
    دل ہی تو ہے نہ سنگ و خشت، درد سے بھر نہ آئے کیوں
    روئیں گے ہم ہزار بار، کوئی ہمیں سزائے کیوں
    
    ہم کو ان سے وفا کی ہے امید، جو نہیں جانتے وفا کیا ہے
    رکھتا ہے کس درجہ ہمارا دل، اس بے وفا سے گلہ کیا ہے
    """,
    
    "Mir Taqi Mir": """
    دل کی کیا خوبی کہ ناداں دل کو سمجھا ہی نہیں
    آگے بجھنا ہے تو بجھ جا، اور جلنا ہے تو جل
    
    اشک آنکھوں میں ہے لب پر نہیں آتی صدا
    اب تو یوں ہے کہ مرے دل میں ہے دل نہیں
    """,
    
    "Faiz Ahmed Faiz": """
    دلِ ناداں تجھے ہوا کیا ہے؟
    آخر اس درد کی دوا کیا ہے؟
    
    ہم پرورشِ لوح و قلم کرتے رہیں گے
    جو دل پہ گزرتی ہے رقم کرتے رہیں گے
    """,
    
    "Allama Iqbal": """
    خودی کو کر بلند اتنا کہ ہر تقدیر سے پہلے
    خدا بندے سے خود پوچھے، بتا تیری رضا کیا ہے
    
    ستاروں سے آگے جہاں اور بھی ہیں
    ابھی عشق کے امتحاں اور بھی ہیں
    """,
    
    "Ahmed Faraz": """
    مجھے تم سے محبت ہے مگر کہنے کی جرأت نہیں
    یہ کیسا عشق ہے جس میں وفا کرنے کی ہمت نہیں
    
    تنہائیوں کا سلسلہ رہنے دیجیے
    ہم کو تو آنے والی صدی کا سہارا چاہیے
    """,
    
    "Parveen Shakir": """
    اپنی آنکھوں کے سمندر میں اتر جا تو سہی
    کون کہتا ہے کہ یہ شہر تمہارے لیے ہے
    
    میری آنکھیں تو ہیں پانی کا سمندر لیکن
    تیرے چہرے کا عکس ان میں نظر آتا ہے
    """
}

def test_predictions():
    """Run tests on all known ghazals"""
    
    print("="*70)
    print("🧪 TESTING POET PREDICTION SYSTEM")
    print("="*70)
    
    results = []
    correct = 0
    
    for expected_poet, text in TEST_GHAZALS.items():
        print(f"\n📝 Testing: {expected_poet}")
        print("-" * 40)
        
        predictions = predict_poet_from_text(text, top_n=3)
        
        if predictions and predictions[0]['poet_name']:
            predicted = predictions[0]['poet_name']
            confidence = predictions[0]['confidence_percent']
            
            is_correct = (predicted == expected_poet)
            status = "✅" if is_correct else "❌"
            
            print(f"  {status} Predicted: {predicted} ({confidence}%)")
            
            if is_correct:
                correct += 1
            
            # Show top 3 predictions
            if len(predictions) > 1:
                print("  Other predictions:")
                for p in predictions[1:3]:
                    print(f"    - {p['poet_name']} ({p['confidence_percent']}%)")
            
            # Show style markers if available
            if predictions[0].get('style_markers'):
                markers = predictions[0]['style_markers'][:3]
                if markers:
                    print(f"  Style markers: {', '.join(markers)}")
        else:
            print(f"  ❌ Prediction failed for {expected_poet}")
        
        results.append({
            'expected': expected_poet,
            'predicted': predictions[0]['poet_name'] if predictions else None,
            'confidence': predictions[0]['confidence_percent'] if predictions else 0,
            'correct': predictions and predictions[0]['poet_name'] == expected_poet
        })
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"  Total tests: {len(TEST_GHAZALS)}")
    print(f"  Correct: {correct}")
    print(f"  Accuracy: {correct/len(TEST_GHAZALS)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for r in results:
        status = "✅" if r['correct'] else "❌"
        print(f"  {status} {r['expected']:20} → {r['predicted']} ({r['confidence']:.0f}%)")
    
    return results

def test_with_real_data(limit=10):
    """Test with real ghazals from database"""
    
    print("\n" + "="*70)
    print("📚 TESTING WITH REAL DATABASE GHAZALS")
    print("="*70)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            t.id,
            p.name as poet_name,
            t.text_urdu
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.form = 'ghazal'
          AND t.is_deleted = FALSE
          AND t.integrity_status = 'clean'
          AND t.text_urdu IS NOT NULL
          AND LENGTH(t.text_urdu) > 200
        ORDER BY RANDOM()
        LIMIT %s
    """, (limit,))
    
    test_cases = cur.fetchall()
    cur.close()
    conn.close()
    
    correct = 0
    for test in test_cases:
        ghazal_id = test['id']
        expected = test['poet_name']
        text = test['text_urdu']
        
        predictions = predict_poet_from_text(text, top_n=1)
        
        if predictions:
            predicted = predictions[0]['poet_name']
            confidence = predictions[0]['confidence_percent']
            is_correct = (predicted == expected)
            
            status = "✅" if is_correct else "❌"
            print(f"  {status} ID:{ghazal_id:5} | Expected: {expected:20} → Got: {predicted} ({confidence:.0f}%)")
            
            if is_correct:
                correct += 1
    
    print(f"\n  Real data accuracy: {correct/len(test_cases)*100:.1f}% ({correct}/{len(test_cases)})")


if __name__ == "__main__":
    # Run tests
    test_predictions()
    
    # Optional: test with real data
    run_real_test = input("\nTest with real database ghazals? (y/n): ").lower()
    if run_real_test == 'y':
        test_with_real_data(limit=20)