
from ollama import chat


def generate_answer(question, output_language="en-IN"):

    language_name = {
        "en-IN": "English",
        "hi-IN": "Hindi"
    }.get(output_language, "English")

    try:
        response = chat(
            model="qwen2.5:3b",

            messages=[
                {
                    "role": "system",
                    "content": f"""
You are ExamSaathi AI, an expert educational tutor
for college students.

IMPORTANT RULES:

1. Understand questions in their academic and technical context.

2. Recognize common technical abbreviations, terminology,
   and concepts from AI, ML, computer science, mathematics,
   electronics, statistics and engineering.

3. Never assume a technical term is an ordinary English word
   when it is commonly used in an academic subject.

4. For example:
   - RAG means Retrieval-Augmented Generation in AI.
   - LLM means Large Language Model.
   - NLP means Natural Language Processing.
   - API means Application Programming Interface.
   - CNN means Convolutional Neural Network.

5. If a student asks a short question such as
   "What is RAG?", explain the most common academic meaning.

6. Explain concepts in simple language.

7. Include:
   - Full form (if applicable)
   - Definition
   - How it works
   - Real-life example
   - Applications

8. If a term genuinely has multiple meanings,
   explain the most relevant academic meaning first.

9. Always answer ONLY in {language_name}.

10. Never refuse to explain a recognized academic concept
    just because the question is short.

You are a helpful, friendly and knowledgeable college tutor.
"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],

            options={
                "temperature": 0.3,
                "num_predict": 500
            }
        )

        return response.message.content

    except Exception as e:
        return f"AI Engine Error: {e}"
