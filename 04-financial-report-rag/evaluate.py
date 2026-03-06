"""
Evaluation harness using RAGAS to measure RAG pipeline quality.
Run: python evaluate.py
"""

import os
from dotenv import load_dotenv
from retriever import retrieve
import anthropic

load_dotenv()

# Test question set — replace with domain-specific questions
TEST_QUESTIONS = [
    "What were the key risk factors mentioned?",
    "What was the total revenue for the reported period?",
    "What is the company's approach to capital allocation?",
]

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_rag_answer(question: str) -> tuple[str, list[str]]:
    """Run RAG pipeline and return (answer, list_of_context_chunks)."""
    chunks = retrieve(question)
    context_texts = [c["text"] for c in chunks]
    context = "\n\n".join(context_texts)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system="You are a financial analyst. Answer using only the provided context.",
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    )
    return response.content[0].text, context_texts


def run_evaluation():
    """Run RAGAS evaluation on the test question set."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from datasets import Dataset
    except ImportError:
        print("Install ragas and datasets: pip install ragas datasets")
        return

    data = {"question": [], "answer": [], "contexts": []}

    for q in TEST_QUESTIONS:
        print(f"Processing: {q}")
        answer, contexts = get_rag_answer(q)
        data["question"].append(q)
        data["answer"].append(answer)
        data["contexts"].append(contexts)

    dataset = Dataset.from_dict(data)
    results = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_precision])

    print("\n=== RAGAS Evaluation Results ===")
    print(results)
    results.to_pandas().to_csv("evaluation_results.csv", index=False)
    print("Results saved to evaluation_results.csv")


if __name__ == "__main__":
    run_evaluation()
