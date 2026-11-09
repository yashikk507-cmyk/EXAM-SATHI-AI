
from ollama import chat
from rag_engine import search_notes


def generate_rag_response(
    question,
    session_id,
    output_language="en-IN"
):

    language_name = {
        "en-IN": "English",
        "hi-IN": "Hindi"
    }.get(output_language, "English")

    # Retrieve notes belonging only to this visitor
    results = search_notes(
        question,
        session_id=session_id,
        top_k=3
    )

    if not results:
        return {
            "answer": "No relevant information found in your uploaded notes.",
            "sources": []
        }

    # Combine retrieved chunks into context
    context = "\n\n".join(
        result["text"] for result in results
    )

    # Generate answer using Qwen
    response = chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "system",
                "content": f"""
You are ExamSaathi AI, a college educational tutor.

Answer the student's question using the provided notes.

Rules:
1. Prioritize information from the notes.
2. Do not invent facts.
3. If the notes do not contain enough information,
   clearly say so.
4. Explain concepts in simple language.
5. Respond only in {language_name}.

Retrieved notes:
{context}
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        options={
            "temperature": 0.2,
            "num_predict": 500
        }
    )

    # Prepare source references
    sources = []

    for result in results:
        sources.append({
            "document": result["source"].split("\\")[-1].split("/")[-1],
            "chunk": result["chunk_index"],
            "page": result.get("page", "Unknown"),
            "distance": round(result["distance"], 4)
        })

    return {
        "answer": response.message.content,
        "sources": sources
    }
