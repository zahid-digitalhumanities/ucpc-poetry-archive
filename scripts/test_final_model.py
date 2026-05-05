import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.poet_ml_model_final import predict_poet

text_id = 3786   # replace with a valid ID
result = predict_poet(text_id)
if isinstance(result, dict) and result.get('method') == 'ml':
    print("ML Predictions:")
    for p in result['predictions']:
        print(f"  {p['poet_name']}: {p['confidence']*100:.1f}%")
else:
    print("Similarity-based predictions:")
    for p in result:
        print(f"  {p['poet_name']}: {p['score']*100:.1f}% - {p['explanation_summary']}")