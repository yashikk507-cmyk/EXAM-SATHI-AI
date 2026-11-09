# ExamSaathi AI — Development Challenges, Debugging & Solutions

This document records the technical challenges, mistakes, debugging processes, solutions, and lessons learned during the development of **ExamSaathi AI**.

Rather than simply listing errors, it explains how each issue was identified, investigated, and addressed throughout the development process.

The purpose is to maintain an honest technical record of the development journey and demonstrate practical problem-solving skills.

---

## 1. Environment and Development Setup

### 1.1 Ollama command not recognized

**Problem:**  
While setting up the local AI environment, the `ollama` command was not recognized in PowerShell.

**How I identified it:**
- Attempted to execute the Ollama command from the terminal.
- Checked whether Ollama was installed.
- Investigated the executable location.

**Solution:**
- Located the installed Ollama executable.
- Used its full path to execute it while resolving the terminal command availability issue.
- Verified that the local model could run.

**What I learned:**  
Installing software does not always make its command immediately available in every terminal. Environment variables and PATH configuration are important when working with local development tools.

### 1.2 Pylance reported unresolved Python imports

**Problem:**  
VS Code displayed unresolved import warnings even though Python packages could be imported successfully from the terminal.

**How I identified it:**
- Tested package imports directly in PowerShell.
- Compared terminal behaviour with the warnings displayed by Pylance.

**Solution / investigation:**
- Investigated the Python interpreter selected in VS Code.
- Checked the virtual environment and package installation context.

**What I learned:**  
The Python interpreter selected by an editor should match the environment used to execute the application. An editor warning does not always mean the package is missing.

---

## 2. Gnani AI Integration Challenges

### 2.1 Speech-to-text integration

**Problem:**  
Integrating Gnani AI speech-to-text into the application required validating the API request and audio-processing workflow.

**How I identified it:**
- Tested the speech-to-text service independently.
- Inspected the API response and recognized transcript.
- Verified the language detection and transcription configuration.

**Solution:**
- Tested the STT workflow separately before connecting it to the main application.
- Validated the request configuration and speech-processing pipeline.

**What I learned:**  
External APIs should be tested independently before integrating them into a larger application. This makes it easier to identify whether an issue belongs to the API or the application code.

### 2.2 TTS returned HTTP 500 for long responses

**Problem:**  
Gnani AI text-to-speech worked for shorter responses but returned an HTTP 500 error when processing a longer answer of approximately 2,311 characters.

**How I identified it:**
- Created an independent TTS test.
- Compared requests with different text lengths.
- Tested 500, 1,000 and 1,500-character inputs.
- Confirmed that the shorter tests succeeded.

**Solution:**
- Implemented chunked text-to-speech generation.
- Divided long answers into smaller segments before sending them for speech generation.
- Tested the chunked workflow.

**What I learned:**  
An API may work correctly for small inputs but fail with larger payloads. Testing different input sizes helps identify practical service limitations.

### 2.3 English questions sometimes received Hindi answers

**Problem:**  
The application did not consistently follow the language selected by the student.

**How I identified it:**
- Selected English in the frontend.
- Asked questions and checked the generated response.
- Compared the selected language with the language used in the answer.

**Solution:**
- Investigated the frontend language selection and backend language handling.
- Adjusted the language-handling workflow.

**What I learned:**  
Language selection must be handled consistently across the frontend, backend and AI response-generation pipeline.

### 2.4 Microphone did not work in Brave

**Problem:**  
Voice input did not work as expected in the Brave browser.

**How I identified it:**
- Tested the microphone functionality in Brave.
- Repeated the test in Google Chrome.
- Compared the behaviour between browsers.

**Solution / result:**
- Chrome microphone testing succeeded.
- Used browser comparison to isolate the issue from the general voice-processing workflow.

**What I learned:**  
Browser permissions and browser-specific compatibility can affect microphone functionality. Features involving browser hardware access should be tested across different browsers.

### 2.5 Text Ask button stopped working while voice interaction worked

**Problem:**  
The voice workflow was functioning, but the text-based Ask button was not working correctly.

**How I identified it:**
- Tested text questions separately.
- Compared the text workflow with the working voice workflow.
- Investigated the frontend request path and backend endpoint.

**Solution / investigation:**
- Isolated the text interaction instead of assuming that the entire AI engine was broken.
- Investigated the frontend-to-backend communication path.

**What I learned:**  
Different features can depend on different routes and frontend event handlers. A working voice feature does not guarantee that text interaction is working.

---

## 3. PDF Processing and RAG Challenges

### 3.1 PDF upload failure

**Problem:**  
PDF uploading initially failed during integration.

**How I identified it:**
- Tested PDF uploads through the website.
- Inspected backend terminal output.
- Investigated the upload and document-processing workflow.

**Solution:**
- Debugged the PDF processing and upload path.
- Retested the upload functionality after making corrections.

**What I learned:**  
File upload functionality involves multiple stages, including frontend submission, backend validation, file handling and document extraction. Each stage should be checked independently.

### 3.2 Duplicate chunks in ChromaDB

**Problem:**  
Duplicate document chunks were appearing in the vector database.

**How I identified it:**
- Inspected records stored in ChromaDB.
- Checked document chunks and their metadata.
- Used dedicated cleanup and checking scripts during debugging.

**Solution:**
- Improved chunk handling.
- Cleaned up duplicate records using development scripts.
- Rechecked stored records.

**What I learned:**  
Vector databases require careful management of document IDs, chunk creation and insertion. Repeatedly processing the same document without appropriate handling can introduce duplicate records.

### 3.3 Incorrect PDF page metadata

**Problem:**  
Some retrieved chunks contained incorrect page metadata, including a page value of `-1`.

**How I identified it:**
- Inspected the metadata stored in ChromaDB.
- Compared stored page information with the PDF extraction output.
- Used metadata-checking scripts to investigate the issue.

**Solution:**
- Investigated and corrected page tracking in the document-processing workflow.
- Verified the stored metadata after making changes.

**What I learned:**  
Metadata is just as important as extracted text in a RAG system. Incorrect metadata can make document retrieval and source tracking unreliable.

### 3.4 IndentationError in `rag_engine.py`

**Problem:**  
The application encountered a Python indentation error after modifications to the page-tracking logic.

**How I identified it:**
- Read the terminal traceback.
- Identified `rag_engine.py` as the affected file.
- Located the incorrect indentation in the modified code.

**Solution:**
- Corrected the indentation.
- Restarted the application.
- Retested the affected functionality.

**What I learned:**  
Python uses indentation to define code blocks. Even a small formatting mistake can prevent the entire application from starting.

### 3.5 Invalid PDF files

**Problem:**  
The application needed to ensure that a file with a `.pdf` extension was actually a valid PDF.

**How I identified it:**
- Renamed a text file with a `.pdf` extension.
- Attempted to upload it through the application.
- Checked whether the application accepted or rejected it.

**Solution / result:**
- Tested the file-validation workflow.
- Verified that the invalid file was rejected.

**What I learned:**  
File extensions alone are not reliable proof of file type. Applications should validate uploaded content rather than trusting filenames.

### 3.6 Oversized PDF uploads

**Problem:**  
Large files could consume unnecessary resources during upload and processing.

**How I identified it:**
- Tested a PDF larger than the configured 10 MB limit.
- Observed the application's response.

**Solution / result:**
- Configured a maximum PDF upload size of 10 MB.
- Verified rejection of oversized uploads.

**What I learned:**  
Upload limits are important for controlling resource consumption and reducing the risk of abuse.

---

## 4. Session Isolation and Multi-User Testing

### 4.1 Students accessing each other's PDFs

**Problem:**  
A multi-user educational application must prevent one student's uploaded study material from appearing in another student's session.

**How I identified it:**
- Uploaded a PDF using a normal Chrome session.
- Opened the application in Chrome Incognito.
- Checked whether the second session could access the first session's PDF material.

**Solution:**
- Implemented session-based separation of PDF collections.
- Used separate session-specific ChromaDB collections.
- Tested access again using separate browser sessions.

**Result:**  
The Incognito session could not access the PDF collection uploaded in the normal Chrome session during testing.

**What I learned:**  
Multi-user applications require data separation at the backend. Hiding files in the frontend is not sufficient.

### 4.2 Audio privacy testing

**Problem:**  
Generated audio files also needed to be considered when testing data separation.

**How I identified it:**
- Compared audio access between normal Chrome and Incognito sessions.

**Result:**  
Browser-session testing was performed, but this does not establish strong server-side ownership protection for audio files.

**Further improvement required:**
- Bind audio access to the requesting session.
- Verify file ownership before serving audio.
- Avoid relying only on unguessable filenames.

**What I learned:**  
A file being difficult to guess does not replace authorization checks.

### 4.3 Simultaneous student requests

**Problem:**  
The application needed to handle different students using it at the same time.

**How I identified it:**
- Opened the application in normal Chrome and Incognito.
- Asked different questions from both sessions.
- Compared the resulting interactions.

**Result:**  
The simultaneous interaction test succeeded.

**What I learned:**  
Testing only one browser session is not enough for a multi-user application. Separate sessions should be tested to identify possible data-mixing problems.

---

## 5. Security and Deployment Challenges

### 5.1 Public access versus login protection

**Problem:**  
An authentication requirement was initially considered for mentor evaluation, but it did not match the intended public student experience.

**How I identified it:**
- Evaluated the proposed login flow against the project's goal.
- Determined that students should be able to access the application without entering mentor credentials.

**Solution:**
- Chose public student access.
- Focused on session separation and backend security rather than mandatory login credentials.

**What I learned:**  
Security decisions should match the intended user experience. Public access does not mean that user data and backend resources should be left unprotected.

### 5.2 Protecting API credentials

**Problem:**  
Third-party API credentials must not be exposed in frontend code or uploaded to a public repository.

**How I identified it:**
- Reviewed the frontend for sensitive API configuration.
- Checked Git status and staged files.
- Reviewed `.gitignore`.

**Solution:**
- Stored the Gnani API key in the backend environment configuration.
- Excluded `.env` from Git tracking.
- Included `.env.example` as a configuration template.

**What I learned:**  
API credentials should remain on the server side. A public repository should never contain real secrets.

### 5.3 Cloudflare Quick Tunnel stopped working after closing the laptop

**Problem:**  
The public application URL stopped working after the laptop was closed.

**How I identified it:**
- Started the FastAPI server locally.
- Exposed it through a Cloudflare Quick Tunnel.
- Confirmed that the public URL worked.
- Closed the laptop and tried accessing the URL again.

**Root cause:**  
The application and tunnel were running on the local machine. Closing the laptop stopped the processes that provided public access.

**Solution / understanding:**
- Recognized that Cloudflare Quick Tunnel exposes a local service; it does not host the application independently.
- The laptop, FastAPI server and tunnel must remain running for the URL to work.

**What I learned:**  
A public tunnel is not the same as permanent cloud hosting. An always-available application needs infrastructure that remains online.

### 5.4 GitHub publishing and secret protection

**Problem:**  
The project needed to be published publicly without accidentally including credentials, local databases or generated files.

**How I identified it:**
- Ran `git status`.
- Reviewed the files marked as untracked.
- Checked `.gitignore`.
- Reviewed the files staged for the initial commit.

**Solution:**
- Added environment files, local databases, uploads, generated audio and temporary development files to `.gitignore`.
- Kept `.env.example` available as a template.
- Committed the project source files and pushed them to GitHub.

**What I learned:**  
Publishing a project requires more than pushing code. Sensitive configuration, generated data and local development files must be reviewed before every public commit.

---

## 6. Debugging Methods I Used

During development, I learned to approach problems systematically rather than making random code changes.

| Debugging method | How I used it |
|---|---|
| Terminal tracebacks | Located Python errors and identified affected files. |
| Application logs | Investigated API requests and backend failures. |
| Independent API testing | Tested Gnani STT and TTS before integrating them. |
| Input-length testing | Compared different TTS input sizes to identify long-text failures. |
| Browser comparison | Compared microphone behaviour in Brave and Chrome. |
| Session comparison | Tested normal Chrome and Incognito to investigate data isolation. |
| Database inspection | Checked ChromaDB chunks and metadata. |
| Negative testing | Uploaded invalid and oversized PDF files. |
| Concurrent testing | Tested different questions from separate browser sessions. |
| Git verification | Checked staged files and `.gitignore` before publishing. |

### My debugging workflow

I followed this general process:

1. Reproduce the issue.
2. Read the error message or inspect the unexpected behaviour.
3. Identify the component involved.
4. Test that component independently where possible.
5. Investigate the root cause.
6. Make a focused change.
7. Restart or retest the affected workflow.
8. Verify that the fix works and check for regressions.

This approach helped me understand the difference between an error's visible symptoms and its actual cause.

---

## 7. Key Technical Lessons

The development of ExamSaathi AI taught me several important lessons:

1. **Test components independently:** External APIs and local models should be validated before integration.
2. **Understand input limitations:** Large inputs can behave differently from small inputs.
3. **Debug one layer at a time:** Frontend, backend, AI models and databases should be investigated separately.
4. **Validate uploaded files:** Never trust a file extension alone.
5. **Manage vector databases carefully:** Chunk IDs, metadata and duplicate records affect retrieval quality.
6. **Design for multiple users:** Session separation must be enforced on the backend.
7. **Protect credentials:** API keys belong in environment variables, not frontend code or public commits.
8. **Understand deployment architecture:** A tunnel does not replace a hosted server.
9. **Test edge cases:** Invalid files, large files, separate sessions and simultaneous requests are important.
10. **Verify every fix:** A change should be followed by a test that demonstrates whether the issue was resolved.

---

## 8. Final Reflection

Developing ExamSaathi AI was not a straightforward process. It involved debugging local AI models, integrating external speech services, building a PDF-based RAG pipeline, handling browser-specific behaviour, testing session isolation and preparing the project for public GitHub access.

Some of the most valuable learning came from problems that were not immediately obvious. For example, a TTS request could succeed with short text but fail with a longer answer, and a working voice feature did not guarantee that the text interaction was functioning correctly.

These experiences helped me develop a more structured approach to software development:

**Reproduce → Investigate → Isolate → Fix → Retest.**

This document records the challenges and learning from the development process, not just the final working features.

---

*Documentation note: This record is based on the development and troubleshooting history available for ExamSaathi AI. Where a root cause or final fix was not independently confirmed, it is identified as an investigation, result or further improvement rather than presented as a verified resolution.*