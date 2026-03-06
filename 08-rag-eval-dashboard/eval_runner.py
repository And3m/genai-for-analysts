"""
RAG Evaluation Runner using RAGAS.
Connects to the ChromaDB from project 03 (copy chroma_db/ here or set CHROMA_PATH).
Run: python eval_runner.py --questions ./test_questions.csv --output ./results.csv
"""

import os
import sys
import json
import argparse
import logging
import pandas as pd
import anthropic
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "policy_docs"
TOP_K = 5


def get_retriever():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    return client.get_collection(COLLECTION_NAME, embedding_function=ef)


def retrieve(collection, query: str) -> list[str]:
    results = collection.query(query_texts=[query], n_results=TOP_K)
    return results["documents"][0]


def generate_answer(question: str, contexts: list[str]) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    context_text = "\n\n".join(contexts)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="You are a helpful assistant. Answer using only the provided context.",
        messages=[{"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"}],
    )
    return response.content[0].text


def run_ragas_evaluation(data: dict) -> dict:
    """Run RAGAS metrics on the collected data."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from datasets import Dataset

        dataset = Dataset.from_dict(data)
        results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision, context_recall])
        return results.to_pandas().to_dict(orient="list")
    except ImportError:
        logger.warning("ragas not installed. Returning raw data only.")
        return {}


def main(questions_path: str, output_path: str):
    questions_df = pd.read_csv(questions_path)
    assert "question" in questions_df.columns, "CSV must have a 'question' column"

    # Optional ground truth column for recall
    has_ground_truth = "ground_truth" in questions_df.columns

    try:
        collection = get_retriever()
    except Exception as e:
        logger.error("Failed to connect to ChromaDB: %s", e)
        logger.error("Run 'python ingest.py' in project 03 first, then copy or point CHROMA_PATH to that chroma_db/")
        sys.exit(1)

    eval_data: dict = {"question": [], "answer": [], "contexts": []}
    if has_ground_truth:
        eval_data["ground_truth"] = []

    for _, row in questions_df.iterrows():
        q = row["question"]
        logger.info("Processing: %s", q)
        contexts = retrieve(collection, q)
        answer = generate_answer(q, contexts)

        eval_data["question"].append(q)
        eval_data["answer"].append(answer)
        eval_data["contexts"].append(contexts)
        if has_ground_truth:
            eval_data["ground_truth"].append(row.get("ground_truth", ""))

    # Save raw outputs
    raw_df = pd.DataFrame({
        "question": eval_data["question"],
        "answer": eval_data["answer"],
        "contexts": [json.dumps(c) for c in eval_data["contexts"]],
    })

    # Run RAGAS
    ragas_results = run_ragas_evaluation(eval_data)
    if ragas_results:
        for metric, scores in ragas_results.items():
            if metric not in ("question", "answer", "contexts", "ground_truth"):
                raw_df[metric] = scores

    raw_df.to_csv(output_path, index=False)
    logger.info("Saved evaluation results to %s", output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="./test_questions.csv")
    parser.add_argument("--output", default="./results.csv")
    args = parser.parse_args()
    main(args.questions, args.output)
