import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from models.poet_prediction_model import predict_poet

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import numpy as np

# ================= LOAD DATA =================
conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
    SELECT t.id, p.name
    FROM texts t
    JOIN poets p ON t.poet_id = p.id
    WHERE t.text_urdu IS NOT NULL
""")

rows = cur.fetchall()
cur.close()
conn.close()

# ================= PREDICTIONS =================
y_true, y_pred = [], []

print(f"🔍 Running predictions on {len(rows)} ghazals...\n")

for i, row in enumerate(rows):
    text_id = row['id']
    poet_name = row['name']

    pred = predict_poet(text_id, top_n=1)

    if pred and pred.get('top_prediction'):
        y_true.append(poet_name)
        y_pred.append(pred['top_prediction']['poet_name'])

    if (i + 1) % 200 == 0:
        print(f"Processed {i+1}/{len(rows)}")

# ================= METRICS =================

print("\n📊 ACCURACY")
acc = accuracy_score(y_true, y_pred)
print(f"Accuracy: {round(acc * 100, 2)}%")

print("\n📋 CLASSIFICATION REPORT\n")
print(classification_report(y_true, y_pred))

# ================= CONFUSION MATRIX =================

labels = sorted(list(set(y_true)))
cm = confusion_matrix(y_true, y_pred, labels=labels)

plt.figure(figsize=(12, 10))
plt.imshow(cm)

plt.title("Confusion Matrix – Poet Classifier")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.xticks(ticks=np.arange(len(labels)), labels=labels, rotation=90)
plt.yticks(ticks=np.arange(len(labels)), labels=labels)

# Annotate numbers
for i in range(len(labels)):
    for j in range(len(labels)):
        plt.text(j, i, cm[i, j], ha='center', va='center')

plt.tight_layout()
plt.savefig("confusion_matrix.png")

print("\n✅ Confusion matrix saved as confusion_matrix.png")