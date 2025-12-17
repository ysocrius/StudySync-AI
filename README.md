# StudySync AI (Citrine & Sage Integration)Tool

This is a full-stack MVP inspired by "NotebookLM", built for the Citrine & Sage assignment.
It features RAG-based Q&A, Audio Dialogue generation, and Video Summarization.
An AI-powered study companion that transforms textbook chapters and YouTube videos into interactive learning experiences.

## Prerequisites
-   **Node.js** (v18+)
-   **Python** (v3.9+)
-   **OpenAI API Key** (Required for RAG & Audio)

## 🚀 Features

### **1. AI-Powered RAG Chatbot**
*   **Interactive Q&A:** Ask questions about your study material.
*   **Smart Citations:** Citations are granular and specific (e.g., `📺 YouTube (Ec19...)`, `📚 chapter.pdf`).
*   **Streaming Responses:** Real-time, typewriter-style responses for a premium feel.
*   **Reasoning:** Answers are synthesized from both text and video transcripts.

### **2. Audio Dialogue Generation (Podcast Mode)**
*   **Two-Person Dialogue:** Converts dry text into an engaging conversation between two hosts.
*   **Audio Sync:** Generated audio is cached and synchronized with the transcript.

### **3. Smart Summaries**
*   **Multi-Modal Summary:** meaningful summaries derived from both the PDF chapter and related YouTube videos.

---

## 🛠️ Setup Instructions

### 1. Backend Setup
The backend requires Python 3.8+.
```bash
cd backend
# Create virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies (pinned for stability)
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in `backend/` and add your OpenAI Key:
```
OPENAI_API_KEY=sk-your-key-here
```

**Run the Server:**
```bash
python main.py
```
*The server will start on `http://localhost:5000`.*

### 2. Frontend Setup
The frontend uses React + Vite.
```bash
cd frontend
npm install
npm run dev
```
*The app will open at `http://localhost:5173`.*

---

## 🔮 Future Roadmap: Dynamic Uploader
I have designed a technical plan to make this tool fully dynamic (NotebookLM style):
- **Drag-and-Drop:** Upload multiple PDFs.
- **YouTube Validation:** Add videos by URL (auto-validating for captions).
- **Session Support:** Create different study sets.
*(See `dynamic_uploader_plan.md` in the project files for full architecture)*

## Tech Stack
*   **Frontend:** React, Vite, TailwindCSS, Lucide Icons
*   **Backend:** Flask, LangChain, FAISS, OpenAI API
## Features Implemented
*   ✅ **Audio Dialogue Mode:** Simulated podcast between Teacher and Student.
*   ✅ **Video/Text Summary:** Context-aware summary of the content.
*   ✅ **Interactive Q&A:** Chatbot grounded in the Chapter PDF and Videos.
