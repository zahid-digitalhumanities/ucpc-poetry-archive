# modules/explainability.py
"""
Human-readable explanation for poet attribution.
"""

# Pre‑defined stylistic markers for major poets (expandable)
POET_STYLE_MARKERS = {
    "Faiz Ahmed Faiz": [
        "revolutionary vocabulary",
        "progressive political imagery",
        "long, flowing verse structures",
        "frequent use of 'صبح', 'زنداں', 'قید'"
    ],
    "Ahmed Faraz": [
        "romantic directness",
        "modern conversational diction",
        "melancholic intimacy",
        "colloquial tone"
    ],
    "Mir Taqi Mir": [
        "classical sorrow imagery",
        "minimalist diction",
        "existential melancholy",
        "frequent 'دل', 'غم', 'ہجر'"
    ],
    "Allama Iqbal": [
        "philosophical abstraction",
        "selfhood terminology (خودی)",
        "elevated rhetorical structure",
        "Islamic revivalist themes"
    ],
    "Mirza Ghalib": [
        "paradoxical expressions",
        "sophisticated wordplay",
        "philosophical doubt",
        "Persianized vocabulary"
    ],
    "Parveen Shakir": [
        "feminine perspective",
        "intimate emotional tone",
        "modern urban imagery",
        "direct personal address"
    ]
}

DEFAULT_EXPLANATION = [
    "lexical similarity detected",
    "stylistic overlap with known works",
    "consistent character n‑gram pattern"
]


def explain_prediction(poet_name: str) -> list:
    """
    Return a list of stylistic markers for the predicted poet.
    """
    if poet_name in POET_STYLE_MARKERS:
        return POET_STYLE_MARKERS[poet_name]
    return DEFAULT_EXPLANATION