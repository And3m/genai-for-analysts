"""
Data preparation: load CSV, tokenise, and split into train/val/test sets.
Run: python prepare_data.py
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer

MODEL_NAME = "distilbert-base-uncased"
DATA_PATH = "./data/tickets.csv"
OUTPUT_DIR = "./processed_data"
MAX_LENGTH = 128
LABEL_COL = "label"
TEXT_COL = "text"


def load_and_validate() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    assert TEXT_COL in df.columns and LABEL_COL in df.columns, \
        f"CSV must have '{TEXT_COL}' and '{LABEL_COL}' columns"
    df = df.dropna(subset=[TEXT_COL, LABEL_COL])
    print(f"Loaded {len(df)} rows. Label distribution:\n{df[LABEL_COL].value_counts()}")
    return df


def encode_labels(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    labels = sorted(df[LABEL_COL].unique())
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}
    df = df.copy()
    df["label_id"] = df[LABEL_COL].map(label2id)
    return df, label2id, id2label


def tokenise(examples, tokenizer):
    return tokenizer(
        examples[TEXT_COL],
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH,
    )


def prepare():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df, label2id, id2label = encode_labels(load_and_validate())

    train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df["label_id"], random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df["label_id"], random_state=42)

    print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def to_hf_dataset(split_df: pd.DataFrame) -> Dataset:
        return Dataset.from_dict({
            TEXT_COL: split_df[TEXT_COL].tolist(),
            "labels": split_df["label_id"].tolist(),
        })

    dataset = DatasetDict({
        "train": to_hf_dataset(train_df),
        "validation": to_hf_dataset(val_df),
        "test": to_hf_dataset(test_df),
    })

    tokenised = dataset.map(lambda x: tokenise(x, tokenizer), batched=True)
    tokenised.save_to_disk(OUTPUT_DIR)

    import json
    with open(os.path.join(OUTPUT_DIR, "label_mappings.json"), "w") as f:
        json.dump({"label2id": label2id, "id2label": id2label}, f, indent=2)

    print(f"Saved processed dataset to {OUTPUT_DIR}")


if __name__ == "__main__":
    prepare()
