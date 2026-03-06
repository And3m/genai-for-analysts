"""
Compare fine-tuned model vs. zero-shot Claude on the test set.
Run: python evaluate.py
"""

import os
import json
import pandas as pd
import anthropic
from dotenv import load_dotenv
from datasets import load_from_disk
from transformers import pipeline
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

load_dotenv()

DATA_DIR = "./processed_data"
MODEL_DIR = "./model_output"


def evaluate_fine_tuned(dataset) -> list[str]:
    """Run the fine-tuned model on the test set."""
    classifier = pipeline(
        "text-classification",
        model=MODEL_DIR,
        tokenizer=MODEL_DIR,
        device=-1,  # CPU
    )
    texts = dataset["test"]["text"]
    preds = classifier(texts, batch_size=32, truncation=True)
    return [p["label"] for p in preds]


def evaluate_zero_shot(dataset, label_names: list[str]) -> list[str]:
    """Run zero-shot Claude on a sample of the test set (cost-limited to 50 examples)."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    texts = dataset["test"]["text"][:50]  # limit for cost
    preds = []

    labels_str = ", ".join(label_names)
    for text in texts:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            system=f"Classify the following text into exactly one of these categories: {labels_str}. Reply with only the category name.",
            messages=[{"role": "user", "content": text}],
        )
        pred = response.content[0].text.strip()
        # Normalise to closest label
        pred = min(label_names, key=lambda l: 0 if l.lower() in pred.lower() else 1)
        preds.append(pred)

    return preds


def run():
    with open(os.path.join(DATA_DIR, "label_mappings.json")) as f:
        mappings = json.load(f)
    id2label = {int(k): v for k, v in mappings["id2label"].items()}
    label_names = list(mappings["label2id"].keys())

    dataset = load_from_disk(DATA_DIR)
    true_labels = [id2label[i] for i in dataset["test"]["labels"]]

    print("=== Fine-Tuned Model Evaluation ===")
    ft_preds = evaluate_fine_tuned(dataset)
    ft_accuracy = accuracy_score(true_labels, ft_preds)
    print(f"Accuracy: {ft_accuracy:.3f}")
    print(classification_report(true_labels, ft_preds))

    print("\n=== Zero-Shot Claude Evaluation (50 samples) ===")
    zs_preds = evaluate_zero_shot(dataset, label_names)
    true_sample = true_labels[:50]
    zs_accuracy = accuracy_score(true_sample, zs_preds)
    print(f"Accuracy (50 samples): {zs_accuracy:.3f}")
    print(classification_report(true_sample, zs_preds))

    # Summary comparison
    print("\n=== Summary ===")
    print(f"Fine-tuned accuracy (full test set): {ft_accuracy:.1%}")
    print(f"Zero-shot Claude accuracy (50 samples): {zs_accuracy:.1%}")


if __name__ == "__main__":
    run()
