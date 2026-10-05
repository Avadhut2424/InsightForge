# InsightForge AI — Frontend Workspace

The official React/TypeScript frontend for InsightForge AI — an autonomous retrieval-augmented research assistant.

---

## 1. Overview

The frontend provides an interactive research workstation inspired by Linear and Perplexity, featuring:
- **Research Topic Discovery & Input:** Prompt input with real-time character count and validation matching the backend.
- **Live Workflow Progress:** Live visualizer tracking LangGraph execution steps (`Planner` ➔ `Retriever` ➔ `Synthesizer` ➔ `Critic` ➔ `Finalize`).
- **Citation-Grounded Report Viewer:** Formatted markdown reports with interactive sentence-level citation cards and verbatim knowledge base chunk inspectability.
- **Critic Verification Inspector:** Surfaces Critic verdicts, reasoning, and revision loop counts.
- **Client Run History & Quick Lookup:** Workstation persistence for switching between past and current research runs.
- **Dark & Light Mode:** Accessible themes with system preference detection and persistence.

---

## 2. Prerequisites

- **Node.js:** v18+ (tested on Node v24)
- **InsightForge Backend:** The FastAPI backend must be running on `http://localhost:8000`.

---

## 3. Getting Started

### 3.1 Install Dependencies
```bash
npm install
```

### 3.2 Environment Configuration
Copy the sample environment file if you need custom API URLs:
```bash
cp .env.example .env.local
```
- By default, `VITE_API_BASE_URL` is empty, which causes Vite to proxy `/research` and `/health` requests directly to `http://localhost:8000`.
- To target an external or direct API host, set:
  ```env
  VITE_API_BASE_URL=http://localhost:8000
  ```

### 3.3 Start the Development Server
```bash
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) in your browser.

---

## 4. Testing & Verification

### Run Unit and Component Tests (Vitest)
```bash
npm test
```
To run tests in watch mode:
```bash
npm run test:watch
```

### Typecheck and Production Build
```bash
npm run build
```

### Linting
```bash
npm run lint
```
