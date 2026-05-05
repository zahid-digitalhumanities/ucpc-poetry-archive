ucpc-poetry-archive/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── models/
│   ├── base.py, ghazal_model.py, ingest_pipeline.py, ...
│   ├── ai_engine/
│   │   ├── poet_prediction_ai.py
│   │   └── similarity_model.py
│   └── ml/
│       ├── poet_classifier_v7.pkl
│       └── train_poet_classifier_v7.py
├── modules/
│   ├── embeddings.py
│   ├── radif_qaafiya.py
│   ├── meter.py, theme.py, ai_tools.py, image_generator.py
├── routes/
│   ├── ingest_routes.py
│   ├── ai_routes.py
│   ├── ask_ucpc_index.py
│   └── ...
├── static/
│   ├── css/, js/, fonts/, images/
├── templates/
│   ├── base.html, index.html, view.html
│   ├── ghazal_ingest.html, ask_ucpc.html
│   └── ...
└── scripts/
    ├── export_training_data.py
    ├── train_poet_classifier_v7.py
    └── ... (utility scripts)
