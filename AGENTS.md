# AGENTS.md

## Project Overview
- **Project:** StudyWise AI - an AI-powered study assistant that lets users upload learning materials, ask citation-backed questions, generate quizzes and flashcards, and track weak topics over time using Retrieval-Augmented Generation.
- **Target user:** Students aged 16-55.
- **My skill level:** [beginner / intermediate / expert]
- **Stack:** Next.js, TypeScript, Tailwind CSS, FastAPI, Python, local JSON persistence for the MVP adapter, PDF/TXT parsing, optional Gemini API generation by default, optional OpenAI Responses API generation, and deterministic local RAG fallbacks. PRD target stack includes PostgreSQL, ChromaDB, and cloud LLM generation.

## Design Reference
- **Stitch project:** https://stitch.withgoogle.com/projects/5299216589319221533
- **Design system:** Academic Precision.
- **Style:** Clean tech, modern corporate, minimal, structured, quiet, and academic.
- **Feel:** Intelligent, organized, reliable, and focused on reducing cognitive load.
- **Primary color:** Professional navy / near-black (`#0F172A` / `#000000`).
- **Secondary color:** Slate blue (`#475569` / `#515F74`).
- **Accent color:** Light blue (`#0EA5E9`) for AI actions, highlights, and insights.
- **Background:** Crisp off-white (`#F7F9FB`) with white cards.
- **Typography:** Inter for headings, labels, navigation, buttons, and UI. Newsreader for long-form study content, notes, summaries, and generated answers.
- **Layout:** 12-column desktop grid, max width around 1280px, 8px spacing baseline, generous whitespace.
- **Cards:** White or soft gray surfaces, 1px borders, low shadow only when needed.
- **Corners:** Precise and restrained. Use 4px for buttons and inputs, 8px for larger cards.
- **Avoid:** Large rounded pill shapes, loud gradients, heavy shadows, bubbly UI, cluttered layouts, and decorative elements that do not help studying.
- **Existing Stitch screens:** Landing Page, Login / Register, Dashboard, Upload Documents, Document Details, Ask AI Assistant, Quizzes & Flashcards, Learning Progress.

## Commands
- **Install:** `cd frontend && npm install`; `cd backend && python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`
- **Dev:** Backend: `cd backend && .venv\Scripts\uvicorn app.main:app --reload`; Frontend: `cd frontend && npm run dev`
- **Build:** `cd frontend && npm run build`
- **Test:** `cd backend && .venv\Scripts\pytest`
- **Lint:** `cd frontend && npm run lint`

## Do
- Read existing code before modifying anything
- Match existing patterns, naming, and style
- Handle errors gracefully - no silent failures
- Keep changes small and scoped to what was asked
- Run dev/build after changes to verify nothing broke
- Ask clarifying questions before guessing

## Don't
- Install new dependencies without asking
- Delete or overwrite files without confirming
- Hardcode secrets, API keys, or credentials
- Rewrite working code unless explicitly asked
- Push, deploy, or force-push without permission
- Make changes outside the scope of the request

## When Stuck
- If a task is large, break it into steps and confirm the plan first
- If you can't fix an error in 2 attempts, stop and explain the issue

## Testing
- Run existing tests after any change
- Add at least one test for new features
- Never skip or delete tests to make things pass

## Git
- Small, focused commits with descriptive messages
- Never force push

## Response Style
- always respond with clear & concise messages
- use plain English when explaining to the User
- avoid long sentences, complex words, or long paragraphs

## Agent skills

### Issue tracker

Issues and PRDs are tracked as GitHub issues on `johnnnys3/Studywise-ai` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
