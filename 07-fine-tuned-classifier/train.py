"""
Fine-tune DistilBERT on the ticket classification task using Hugging Face Trainer.
Run: python train.py
"""

import os
import json
from datasets import load_from_disk
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

MODEL_NAME = "distilbert-base-uncased"
DATA_DIR = "./processed_data"
OUTPUT_DIR = "./model_output"
EPOCHS = 3
BATCH_SIZE = 16


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "f1_macro": f1_score(labels, predictions, average="macro"),
    }


def train():
    with open(os.path.join(DATA_DIR, "label_mappings.json")) as f:
        mappings = json.load(f)
    label2id = mappings["label2id"]
    id2label = {int(k): v for k, v in mappings["id2label"].items()}

    num_labels = len(label2id)
    dataset = load_from_disk(DATA_DIR)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        logging_dir=os.path.join(OUTPUT_DIR, "logs"),
        logging_steps=50,
        report_to="none",  # set to "wandb" if you have WANDB_API_KEY configured
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

    # Evaluate on test set
    test_results = trainer.evaluate(dataset["test"])
    print("\nTest set results:", test_results)


if __name__ == "__main__":
    train()
