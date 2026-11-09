# ExamSaathi AI — Learn Without Limits

An AI-powered educational assistant that helps students understand concepts through text and voice interaction, with support for learning directly from uploaded PDF notes.

**GitHub:** https://github.com/yashikk507-cmyk/EXAM-SATHI-AI

---

## 1. Project Overview

ExamSaathi AI is an AI-based learning assistant designed to make studying easier and more interactive.

Students can ask questions in English or Hindi, receive AI-generated explanations, interact using voice, and upload PDF notes to ask questions based on their study material.

The project combines a locally running Large Language Model (LLM), Retrieval-Augmented Generation (RAG), and Gnani AI's speech technologies.

## 2. Key Features

- **AI Text Tutor:** Ask questions and receive educational explanations.
- **Voice Interaction:** Ask questions using your microphone.
- **Speech-to-Text:** Converts spoken questions into text using Gnani AI.
- **Text-to-Speech:** Converts AI-generated answers into audio.
- **Bilingual Support:** English and Hindi interaction.
- **PDF Learning:** Upload PDF notes and ask questions about their content.
- **RAG-Based Answers:** Retrieves relevant information from uploaded study material before generating answers.
- **Student Session Isolation:** Keeps uploaded PDF collections separated between browser sessions.
- **Responsive Interface:** A student-friendly web interface.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| LLM | Ollama — Qwen 2.5 3B |
| Embeddings | Ollama — nomic-embed-text |
| Vector Database | ChromaDB |
| PDF Processing | PyPDF |
| Speech-to-Text | Gnani AI Prisma |
| Text-to-Speech | Gnani AI Timbre |
| API Communication | Requests |
| Configuration | Python Dotenv |

## 4. System Architecture

```text
                 STUDENT
                    |
                    v
             WEB INTERFACE
          (HTML, CSS, JavaScript)
                    |
                    v
              FASTAPI SERVER
                    |
          +---------+---------+
          |         |         |
          v         v         v
       TEXT       VOICE      PDF
       INPUT      INPUT      UPLOAD
          |         |         |
          |         v         v
          |      GNANI STT  PDF PROCESSING
          |         |         |
          +---------+         v
          |                CHUNKING
          |                   |
          v                   v
       OLLAMA              EMBEDDINGS
      QWEN 2.5                 |
          |                   v
          |               CHROMADB
          |                   |
          |              RETRIEVAL
          |                   |
          |                   v
          |              RAG ANSWER
          |                   |
          +---------+---------+
                    |
                    v
             GENERATED ANSWER
                    |
                    v
              GNANI TTS
                    |
                    v
             STUDENT RESPONSE
```

## 5. Project Structure

```text
EXAM-SATHI-AI/
│
├── main.py
├── ai_engine.py
├── voice_engine.py
├── tts_engine.py
├── pdf_processor.py
├── text_chunker.py
├── rag_engine.py
├── rag_answer.py
│
├── static/
│   └── index.html
│
├── requirements.txt
├── .env.example
└── .gitignore
```

### Main Python Files

| File | Responsibility |
|---|---|
| `main.py` | FastAPI application and API endpoints |
| `ai_engine.py` | Generates educational answers using Ollama |
| `voice_engine.py` | Handles speech-to-text and voice-question processing |
| `tts_engine.py` | Generates speech from text using Gnani AI |
| `pdf_processor.py` | Extracts content from uploaded PDF files |
| `text_chunker.py` | Splits PDF content into smaller chunks |
| `rag_engine.py` | Handles embeddings, storage, and retrieval |
| `rag_answer.py` | Generates answers using retrieved PDF context |
| `static/index.html` | Frontend user interface |

## 6. Installation and Setup

### Prerequisites

Install the following:

- Python 3.12
- Git
- Ollama
- An active Gnani AI API key

### Step 1: Clone the repository

```bash
git clone https://github.com/yashikk507-cmyk/EXAM-SATHI-AI.git
cd EXAM-SATHI-AI
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and start Ollama

Download Ollama from:

https://ollama.com/

Pull the required models:

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

Make sure the Ollama service is running.

### Step 5: Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
GNANI_API_KEY_ID=your_actual_api_key
EXAMSAATHI_SESSION_SECRET=your_random_secret
COOKIE_SECURE=false
```

**Security:** Never upload your actual `.env` file or API key to GitHub. The `.env` file is excluded through `.gitignore`.

For an HTTPS deployment, configure `COOKIE_SECURE=true`.

### Step 6: Run the application

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open the application:

http://127.0.0.1:8000/app

## 7. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Application health |
| GET | `/app` | Opens the web interface |
| POST | `/ask` | Processes text questions |
| POST | `/ask-voice` | Processes voice questions |
| GET | `/audio/{filename}` | Serves generated audio |
| POST | `/upload-pdf` | Uploads and processes PDF files |
| POST | `/ask-rag` | Answers questions using uploaded PDFs |

## 8. How RAG Works

Retrieval-Augmented Generation allows ExamSaathi AI to answer questions using information from a student's uploaded PDF notes.

The process consists of:

1. **PDF Extraction:** Extract text from uploaded PDF documents.
2. **Text Chunking:** Divide extracted text into smaller sections.
3. **Embedding Generation:** Convert text chunks into numerical vector representations using `nomic-embed-text`.
4. **Vector Storage:** Store embeddings in ChromaDB.
5. **Retrieval:** Find relevant chunks when a student asks a question.
6. **Answer Generation:** Pass retrieved context to Qwen 2.5 to generate an educational response.

This helps the assistant answer questions using the student's own study material rather than relying only on general model knowledge.

## 9. Voice Processing Workflow

### Voice Input

1. Student records a question using the microphone.
2. Audio is sent to the FastAPI backend.
3. Gnani AI Prisma processes speech-to-text.
4. The recognized question is passed to the AI engine.
5. Qwen generates an answer.

### Voice Output

1. The generated answer is passed to Gnani AI Timbre.
2. Text is converted into speech.
3. Audio is returned to the frontend.
4. Student can listen to the generated response.

## 10. Security Measures

The project includes several security measures:

- API credentials stored in environment variables.
- `.env` excluded from Git tracking.
- HTTP-only session cookies.
- Signed session identifiers.
- Separate PDF collections for different sessions.
- PDF and audio upload size restrictions.
- File validation and UUID-based filenames.
- Basic rate limiting on API endpoints.
- Security-related HTTP response headers.
- Temporary audio cleanup.

**Important:** These measures are a foundation for a student-facing demo, not a complete production security audit. Production deployment should additionally include persistent rate limiting, session and collection expiry, stronger audio ownership checks, CSRF/origin protections, monitoring, and deployment hardening.

## 11. Development Challenges and Improvements

Some important engineering areas addressed during development:

- **Speech processing:** Integrated Gnani AI speech recognition and synthesis into the application.
- **Long TTS responses:** Identified failures with long text and implemented chunk-based speech generation.
- **Language handling:** Improved the English/Hindi language-selection flow.
- **PDF retrieval:** Worked on page-aware extraction, chunking, and retrieval.
- **Session isolation:** Separated uploaded PDF data between browser sessions.
- **File validation:** Added restrictions for unsupported and oversized uploads.
- **API key protection:** Moved sensitive credentials to environment variables.
- **GitHub hygiene:** Excluded local databases, generated audio, uploaded documents, and secrets from the public repository.

## 12. Current Limitations

- Ollama must be running for local LLM and embedding operations.
- The application requires a valid Gnani AI API key for speech services.
- The current local setup is not an always-on public hosting solution.
- A cloud deployment needs suitable compute resources, model hosting, persistent storage, and additional security hardening.
- The current session and rate-limiting implementation needs further production-level improvements.

## 13. Future Improvements

- Add support for more Indian languages.
- Improve PDF retrieval accuracy.
- Add quizzes and automatic question generation.
- Add student progress tracking.
- Improve response quality and reduce latency.
- Introduce production-grade authentication and storage where required.
- Deploy on reliable cloud infrastructure.

## 14. Learning Outcomes

Building ExamSaathi AI involved practical work with:

- Python backend development.
- FastAPI and REST APIs.
- Large Language Models.
- Retrieval-Augmented Generation.
- Vector databases and embeddings.
- Speech recognition and speech synthesis.
- PDF processing.
- Session management and application security.
- Git and GitHub.

## 15. Running the Project — Quick Reference

```bash
# Activate environment
venv\Scripts\activate

# Start the application
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then visit:

http://127.0.0.1:8000/app

---

## 16. Project Information

**Project:** ExamSaathi AI  
**Category:** Artificial Intelligence / Machine Learning / EdTech  
**Backend:** Python and FastAPI  
**AI Engine:** Ollama — Qwen 2.5 3B  
**Speech Technology:** Gnani AI Prisma and Timbre  
**Repository:** https://github.com/yashikk507-cmyk/EXAM-SATHI-AI

Built as an educational AI project exploring the practical integration of LLMs, RAG, and voice technologies.

---

*ExamSaathi AI — Big ideas. Made simple.*
