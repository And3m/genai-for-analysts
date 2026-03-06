"""
Production inference with the fine-tuned classifier.
Run: python inference.py --text "Server is down for all users in the APAC region"
"""

import argparse
from transformers import pipeline

MODEL_DIR = "./model_output"


def classify(text: str) -> dict:
    classifier = pipeline(
        "text-classification",
        model=MODEL_DIR,
        tokenizer=MODEL_DIR,
        device=-1,
        return_all_scores=True,
    )
    results = classifier(text, truncation=True)[0]
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return {
        "prediction": results_sorted[0]["label"],
        "confidence": round(results_sorted[0]["score"], 4),
        "all_scores": {r["label"]: round(r["score"], 4) for r in results_sorted},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="Text to classify")
    args = parser.parse_args()

    result = classify(args.text)
    print(f"Prediction: {result['prediction']} (confidence: {result['confidence']:.1%})")
    print("All scores:", result["all_scores"])
