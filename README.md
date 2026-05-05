# StudyWise AI

StudyWise AI is an AI-powered study assistant that turns uploaded learning materials into citation-backed answers, quizzes, flashcards, and weak-topic recommendations using Retrieval-Augmented Generation.

## Project Overview
StudyWise AI helps students and self-learners understand their study materials faster. Users can upload documents, ask questions about their own materials, generate quizzes, review flashcards, and track weak topics over time.

## Problem
Students often have many PDFs, lecture notes, slides, and articles, but struggle to quickly understand, review, and retain the material.

Generic AI chatbots can answer questions, but they usually do not reference the student's own material, track learning progress, or identify weak topics.

## Solution
StudyWise AI combines document upload, RAG-based question answering, quiz generation, flashcards, and progress tracking into one study-focused platform.

Answers should be grounded in uploaded documents and include source references, so users can study with more trust, structure, and accountability.

## Target Users
- University students
- Self-learners
- Bootcamp students
- Certification candidates
- Researchers reviewing academic papers
- Tutors, teachers, study group leaders, and professionals learning technical material

## Features
- Secure user registration and login
- PDF and TXT document upload
- Block-ordered PDF text extraction with page preservation
- Semantic document chunking with headings, section paths, page ranges, source metadata, and quality checks
- Chroma-ready vector storage with deterministic local embeddings for development
- Hybrid retrieval with query rewriting, keyword search, vector search, proposition search, fusion, reranking, dedupe, and page filters
- Citation-backed document Q&A
- Quiz generation from uploaded materials with strict JSON validation
- Quiz attempts and scoring
- Weak topic tracking with source pages, chunk IDs, difficulty, and cognitive skill metadata
- Basic analytics, RAG traces, and AI evaluation metrics
- Flashcards as an optional MVP feature or Version 1.1 feature

## MVP Scope
### In Scope
- User registration and login
- Dashboard
- Document upload
- PDF and text extraction
- Chunking
- Embedding generation
- Vector storage with ChromaDB
- RAG question answering
- Source references
- Quiz generation
- Quiz attempt submission
- Weak topic tracking
- Basic analytics dashboard

### Out of Scope for MVP
- Real-time collaboration
- Mobile app
- Payment system
- Teacher or admin portal
- Browser extension
- Voice-based study assistant
- Advanced spaced repetition
- Multi-user shared workspaces

## Tech Stack
### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- React Hook Form
- Zod
- Axios or Fetch API
- Zustand or React Context for lightweight state

### Backend
- FastAPI
- Python
- SQLAlchemy
- Pydantic
- Alembic
- PyMuPDF for PDF parsing
- Gemini API for LLM generation by default
- OpenAI API as an optional alternate LLM provider
- ChromaDB for vector storage

### Database
- PostgreSQL

### Authentication
- JWT-based authentication for MVP
- Password hashing with bcrypt or Argon2

### Deployment
- Frontend: Vercel
- Backend: Render, Railway, or Fly.io
- Database: Supabase PostgreSQL, Neon, Railway PostgreSQL, or Render PostgreSQL
- Vector database: Local ChromaDB for development, hosted Chroma or pgvector later

## Architecture
```text
User
  |
Next.js Frontend
  |
FastAPI Backend
  |
PostgreSQL Database
  |
Document Parser / Chunker / Embedding Service
  |
ChromaDB Vector Store
  |
Retriever
  |
LLM Service
  |
Citation-backed Answer / Quiz / Flashcards
```

## How RAG Works in This Project
1. User uploads a PDF or TXT file.
2. The backend validates the file type and size.
3. The backend extracts page-ordered text from the file with PyMuPDF.
4. Text is cleaned, repeated page artifacts are removed, and page numbers are preserved.
5. The semantic chunker preserves headings, sections, definitions, examples, processes, and page ranges where possible.
6. Each chunk receives metadata, including document ID, user ID, chunk ID, page range, section title, content type, token count, text hash, and quality score.
7. Proposition-level study statements are extracted from chunks to improve retrieval and quiz grounding.
8. Chunks are stored in local JSON for the MVP and indexed in ChromaDB when enabled.
9. Retrieval always filters by authenticated `user_id` and selected `document_id`.
10. The retriever rewrites and decomposes the query, applies page filters when present, runs keyword/vector/proposition retrieval, fuses results, dedupes chunks, reranks, and builds context.
11. The LLM receives only retrieved context blocks with page and chunk labels.
12. The LLM answers using only the retrieved context and cites source pages/chunks.
13. If the answer is not in the retrieved context, the AI says it cannot find enough information in the uploaded document.

## RAG Architecture Notes
The current RAG system is inspired by practical patterns from modern RAG projects and open-source references, including RAG-Anything, RAG_Techniques, LangChain, LlamaIndex, Haystack, ChromaDB examples, pgvector examples, and NVIDIA's RAG blueprint.

Implemented MVP patterns:

- Structure-aware ingestion instead of blind text splitting
- Section-aware and content-type-aware chunk metadata
- Proposition extraction for atomic evidence
- Query rewriting and query decomposition
- Hybrid retrieval with keyword, Chroma vector, and proposition scoring
- Reciprocal rank fusion and lightweight reranking
- Duplicate chunk removal
- Citation mapping with page ranges and chunk IDs
- Strict JSON schema output for quizzes
- Source-aware weak-topic tracking
- Retrieval traces for evaluation and debugging

## User Flow
### New User Flow
```text
Landing Page
  |
Register
  |
Login
  |
Dashboard
  |
Upload Document
  |
Ask Questions / Generate Quiz
```

### Document Q&A Flow
```text
Select Document
  |
Ask Question
  |
Retrieve Relevant Chunks
  |
Generate Answer
  |
Show Citations
  |
Save Chat History
```

### Quiz Flow
```text
Select Document
  |
Choose Question Count and Difficulty
  |
Generate Quiz
  |
Answer Questions
  |
Submit Attempt
  |
View Score and Explanations
  |
Update Weak Topics
```

### Progress Review Flow
```text
Open Progress Page
  |
Review Weak Topics
  |
View Accuracy by Topic
  |
Follow Study Recommendations
  |
Return to Source Document/Page
```

## Database Design
Main tables:

- `users`
- `documents`
- `document_chunks`
- `chat_messages`
- `quizzes`
- `quiz_questions`
- `quiz_attempts`
- `quiz_answers`
- `weak_topics`
- `evaluation_metrics`

## API Requirements
### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users/me`

### Documents
- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `DELETE /api/v1/documents/{document_id}`

### RAG
- `POST /api/v1/documents/{document_id}/ask`
- `GET /api/v1/documents/{document_id}/chat-history`

### Quizzes
- `POST /api/v1/documents/{document_id}/quizzes`
- `GET /api/v1/quizzes`
- `GET /api/v1/quizzes/{quiz_id}`
- `POST /api/v1/quizzes/{quiz_id}/attempts`
- `GET /api/v1/quizzes/{quiz_id}/attempts`

### Flashcards
- `POST /api/v1/documents/{document_id}/flashcards`
- `GET /api/v1/documents/{document_id}/flashcards`

### Progress
- `GET /api/v1/progress/summary`
- `GET /api/v1/progress/weak-topics`
- `GET /api/v1/progress/recommendations`

### Evaluation
- `GET /api/v1/evaluation/metrics`
- `GET /api/v1/evaluation/rag-traces`
- `POST /api/v1/evaluation/log`

## Evaluation
StudyWise AI should track simple AI quality metrics:

- Retrieval accuracy
- Citation coverage
- Answer groundedness
- Average response time
- Quiz generation success rate
- JSON validation success rate
- Valid source page rate
- Difficulty validation pass rate
- Weak-topic improvement rate
- User rating of answer helpfulness

## Security Considerations
- Passwords must never be stored in plain text.
- Protected routes must require authentication.
- Users must only access their own documents, chunks, quizzes, attempts, and progress data.
- File uploads must validate type, size, and page count.
- Unsupported, password-protected, unreadable, or empty files should be rejected.
- RAG retrieval must be scoped to the current user and selected document.
- Prompts must instruct the model to use only retrieved context.
- AI answers must not invent citations.
- Do not log passwords, tokens, API keys, document contents, or full user prompts unless explicitly required and safe.

## Backend Constraints
### MVP File Limits
- Maximum file size: 10MB
- Allowed file types: PDF and TXT
- Maximum pages per PDF: 100

### Document Processing Statuses
```text
uploaded
processing
ready
failed
```

### Chunking Defaults
```text
Chunk size: 650 words
Overlap: 125 words
Initial retrieval: 20+ candidates per retrieval source
Final top K retrieval: 6-8 chunks
```

## Testing
Expected test coverage:

- Unit tests for chunking, scoring, validation, and weak-topic updates
- Integration tests for auth, document upload, RAG routes, quiz routes, and progress routes
- AI evaluation tests for citation coverage, retrieval quality, invalid JSON handling, and hallucination resistance

## Setup Instructions
The project now contains a Next.js frontend and FastAPI backend.

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\uvicorn app.main:app --reload
```

The backend runs at:

```text
http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

The frontend runs at:

```text
http://localhost:3000
```

### Current MVP Implementation Note
This implementation uses local JSON persistence for MVP data and ChromaDB for local vector indexing when enabled.

If `GEMINI_API_KEY` is set in `backend/.env`, the backend uses Gemini for citation-backed answers and structured quiz generation. This is the default local setup and works with the Gemini free tier, subject to rate limits.

If no Gemini key is set, the app can optionally use OpenAI when `AI_PROVIDER=openai` and `OPENAI_API_KEY` are configured. If no AI key is set, the app falls back to local retrieval and template quiz generation.

Chroma indexing uses a deterministic local embedding fallback in the MVP, so document processing can work without OpenAI embeddings. For stronger semantic retrieval later, replace the fallback with provider embeddings.

The PRD target remains PostgreSQL, ChromaDB, and cloud LLM generation. The local adapters are intended to be replaced as the product hardens.

Expected local setup:

```text
frontend/
backend/
docs/
scripts/
docker-compose.yml
```

## Environment Variables
Expected environment variables:

```text
JWT_SECRET=change-this-to-a-long-random-secret
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=45
CHROMA_ENABLED=true
CHROMA_DIR=./data/chroma
CHROMA_COLLECTION=studywise_chunks
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
FRONTEND_URL=http://localhost:3000

# Optional OpenAI provider settings
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Never commit real secrets or API keys.

## Design Reference


Design system: **Academic Precision**

StudyWise AI should feel clean, structured, academic, and reliable. The UI should use generous whitespace, precise spacing, low-contrast borders, and calm colors to reduce cognitive load for students.

### Visual Style
- Clean tech
- Modern corporate
- Minimal
- Structured
- Quiet and academic

### Core Design Rules
- Use Inter for headings, labels, navigation, buttons, and UI text.
- Use Newsreader for long-form study content, notes, summaries, and AI-generated answers.
- Use professional navy / near-black as the primary color.
- Use slate blue as the secondary color.
- Use light blue accents for AI actions, highlights, and insights.
- Use crisp off-white backgrounds with white cards.
- Use 1px borders and subtle tonal layers instead of heavy shadows.
- Use 4px corners for buttons and inputs.
- Use 8px corners for larger cards.
- Avoid large pill shapes, loud gradients, heavy shadows, bubbly UI, and clutter.

### Reference Screens
- Landing Page
- Login / Register
- Dashboard
- Upload Documents
- Document Details
- Ask AI Assistant
- Quizzes & Flashcards
- Learning Progress


## Limitations
- Scanned image-only PDFs are not supported in the MVP unless OCR is added.
- Password-protected PDFs should be rejected.
- Very large PDFs should be limited.
- Flashcards may ship after the core MVP.
- Multi-document chat is a future improvement.
- ChromaDB is the MVP vector store. pgvector may replace it later.

## Future Improvements
### Version 1.1
- Flashcard generation
- Better document summaries
- Difficulty-based quiz generation
- Topic-based study recommendations

### Version 1.2
- Spaced repetition
- Multi-document chat
- Document collections
- Export quiz results

### Version 2.0
- Supabase pgvector instead of ChromaDB
- Team study spaces
- Tutor dashboard
- Mobile app
- OCR for scanned PDFs
- Voice-based study mode

## Key Risks
- Poor PDF extraction
- Hallucinated answers
- Invalid quiz JSON
- Cross-user data leakage
- High AI API cost

## Final MVP Definition
The MVP is complete when a user can register, log in, upload a PDF, process it into chunks and embeddings, ask citation-backed questions, generate and complete quizzes, and see weak topics update from quiz results.
