# 🧠 MindMirror

> **Open-source, privacy-first AI companion for emotional reflection.**

MindMirror helps you understand your thoughts, recognize emotional patterns, and reflect through supportive conversations inspired by Cognitive Behavioral Therapy (CBT).

It combines **AI journaling, emotion analysis, cognitive distortion detection, CBT-inspired conversations, voice journaling, and emotional insights** into one application.

The goal is simple:

> **Give people a private space to understand themselves better — while keeping the technology open and their data under their control.**

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Try%20MindMirror-6366f1)](https://mind-mirror-tau.vercel.app/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ⭐ Support MindMirror

If you find MindMirror useful or interesting:

* ⭐ **Star** the repository to help others discover it
* 🍴 **Fork** it and build your own version
* 🐛 **Report bugs** and issues
* 💡 **Suggest features**
* 🤝 **Contribute** with code, documentation, or ideas

Every star, fork, issue, and contribution helps the project grow.

---

## 🚀 Try MindMirror

### 🌐 Live Demo

**[Open MindMirror →](https://mind-mirror-tau.vercel.app/)**

MindMirror also includes a **Demo Mode** so you can explore the application and its emotional insights without using real personal journal data.

---

# 🌱 Why MindMirror?

Most AI applications require sending your conversations to a cloud AI provider.

MindMirror takes a different approach.

### 🔒 Privacy-first

Your journal can contain deeply personal information.

MindMirror can run AI models **locally on your own machine using Ollama**, allowing you to keep your data under your control.

### 🧠 CBT-inspired

MindMirror uses a structured conversation approach inspired by Cognitive Behavioral Therapy:

1. Identify possible cognitive distortions
2. Validate the emotional experience
3. Examine the thought
4. Encourage reflection through Socratic questions
5. Suggest a practical next step

### 🤖 Local AI

Run MindMirror with **Ollama** and local language models.

No paid AI API is required when using the local AI configuration.

### 📊 Understand your patterns

MindMirror goes beyond storing journal entries.

It helps surface:

* Emotional trends
* Cognitive distortions
* Possible triggers
* Weekly patterns
* Growth streaks
* Changes over time

---

# ✨ Features

| Feature                    | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| 📔 **AI Journaling**       | Write about your thoughts and receive emotional analysis                 |
| 🧠 **CBT Analysis**        | Detect possible cognitive distortions and encourage healthier reflection |
| 💬 **AI Companion**        | Supportive conversations using a CBT-inspired framework                  |
| 📊 **Emotional Dashboard** | Explore mood trends, emotional timelines, and insights                   |
| 📈 **Growth Story**        | Compare earlier and recent entries to visualize changes                  |
| 🎙️ **Voice Journaling**   | Record thoughts using Whisper speech-to-text                             |
| 🔍 **Pattern Detection**   | Identify emotional patterns and recurring themes                         |
| 🔔 **Daily Check-ins**     | Browser push notifications and email reminders                           |
| 📱 **Offline-first PWA**   | Install MindMirror as a Progressive Web App                              |
| 🎨 **Modern UI**           | Responsive dark glassmorphism interface                                  |
| 🧪 **Demo Mode**           | Explore MindMirror with deterministic demo data                          |
| 👨‍⚕️ **Therapist Export** | Generate a printable summary of journal insights                         |

---

# 🧠 How It Works

MindMirror uses a structured five-step CBT-inspired conversation process.

### 1. Detect

The system looks for possible cognitive distortions such as:

* Catastrophizing
* Mind reading
* All-or-nothing thinking
* Overgeneralization
* Other common thinking patterns

### 2. Validate

The AI acknowledges the user's emotional experience before attempting to reframe the thought.

### 3. Examine

The conversation uses Socratic-style questions to encourage reflection.

### 4. Ground

When appropriate, the system can introduce grounding techniques such as breathing or sensory check-ins.

### 5. Next Step

The conversation encourages a practical and manageable next step.

---

# 🏗️ Architecture

```text
                        ┌─────────────────────────┐
                        │     Next.js Frontend    │
                        │                         │
                        │ Journal / Chat /        │
                        │ Dashboard / Landing     │
                        └────────────┬────────────┘
                                     │
                                  HTTP + SSE
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │     FastAPI Backend     │
                        │                         │
                        │ Auth / Analysis /       │
                        │ Chat / Journal APIs     │
                        └────────────┬────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ PostgreSQL  │       │ Ollama/Groq │       │   Whisper   │
       │   Database  │       │     LLM     │       │    STT      │
       └─────────────┘       └─────────────┘       └─────────────┘
              │                      │
              ▼                      ▼
       ┌─────────────┐       ┌─────────────┐
       │   Alembic   │       │ HuggingFace │
       │  Migrations │       │Emotion Model│
       └─────────────┘       └─────────────┘
```

---

# 🛠️ Tech Stack

| Layer          | Technology                                     |
| -------------- | ---------------------------------------------- |
| Frontend       | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend        | FastAPI, Pydantic, Python 3.11                 |
| AI             | Ollama / Groq, Hugging Face, Whisper           |
| Database       | PostgreSQL                                     |
| Migrations     | Alembic                                        |
| Authentication | JWT, HttpOnly cookies, bcrypt                  |
| PWA            | Service Worker, Cache API                      |
| Email          | Resend                                         |
| Testing        | Vitest, React Testing Library, pytest          |
| Deployment     | Docker / Render / Vercel                       |

---

# 🚀 Quick Start

## Requirements

Before starting, make sure you have:

* Docker Desktop
* At least **8 GB RAM**
* At least **10 GB free disk space**

The additional disk space is primarily required for AI model downloads.

---

## Clone the Repository

```bash
git clone https://github.com/HASSANFARYAD/MindMirror.git
cd MindMirror
```

---

## Configure Environment Variables

Create your environment file:

```bash
cp .env.example .env
```

Then open `.env` and configure the values required for your environment.

---

## Start with Docker

```bash
docker-compose up --build
```

The first startup may take several minutes because AI models may need to be downloaded.

Once the services are running:

### Frontend

```text
http://localhost:3000
```

### Backend API

```text
http://localhost:8000
```

### API Documentation

```text
http://localhost:8000/docs
```

---

# 🤖 AI Configuration

MindMirror supports different AI providers.

## Local AI with Ollama

For a privacy-focused setup, use Ollama:

```env
AI_PROVIDER=ollama
```

This allows the language model to run locally on your machine.

### Why Ollama?

* Local inference
* No paid API required
* Greater control over your data
* Works with open-source models
* Useful for offline/private deployments

---

## Cloud AI with Groq

You can also configure Groq:

```env
AI_PROVIDER=groq
```

See `.env.example` for the complete configuration.

---

# 🎙️ Voice Journaling

MindMirror supports voice journaling using **Whisper speech-to-text**.

The general flow is:

```text
Voice Recording
       ↓
Whisper Speech-to-Text
       ↓
Journal Entry
       ↓
Emotion Analysis
       ↓
AI Insights
```

This allows users to capture their thoughts without typing.

---

# 📊 Emotional Insights

MindMirror provides visual insights into your journal history.

Depending on the available data, you can explore:

* Mood trends
* Sentiment changes
* Emotional patterns
* Cognitive distortions
* Recurring themes
* Growth over time

The purpose is to make your journal history easier to reflect on rather than simply storing entries.

---

# 🔔 Notifications

MindMirror supports reminders and notifications for journaling and check-ins.

Supported functionality includes:

* Daily journaling reminders
* Browser push notifications
* Email reminders
* Pattern-related notifications

Notification configuration is documented in `.env.example`.

---

# 📱 Progressive Web App

MindMirror is designed as an **offline-first Progressive Web App (PWA)**.

You can install it on supported devices and access supported functionality without treating it like a traditional website.

---

# 🧪 Demo Mode

MindMirror includes a deterministic demo mode.

This allows developers and users to explore:

* Journal entries
* Emotional patterns
* Dashboard visualizations
* Insights
* Growth history

without having to populate the application with personal data.

---

# 🧪 Testing

## Frontend

```bash
cd frontend
npm test
```

## Backend

```bash
cd backend
python3 -m pytest -v
```

---

# 📁 Project Structure

```text
MindMirror/
│
├── backend/
│   ├── main.py
│   ├── alembic/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── database/
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── tests/
│   └── public/
│
├── .env.example
├── docker-compose.yml
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── DEPLOYMENT.md
├── AUDIT_REPORT.md
└── README.md
```

---

# 🍴 Build Your Own MindMirror

Want to customize MindMirror?

Click the **Fork** button at the top of this repository and create your own version.

Then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/MindMirror.git
cd MindMirror
```

Create a feature branch:

```bash
git checkout -b feature/my-feature
```

Make your changes, test them, and open a pull request.

---

# 💡 What Can You Build?

MindMirror is intentionally open to experimentation.

You could contribute:

* 🎨 UI improvements
* 🧠 New CBT techniques
* 🤖 Support for additional local AI models
* 📊 Better emotional visualizations
* 🎙️ Improved voice journaling
* 🔐 Privacy improvements
* ♿ Accessibility improvements
* 🧪 Additional tests
* 🌍 Internationalization
* 📚 Better documentation
* 🔌 New integrations

---

# 🤝 Contributing

Contributions are welcome!

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide, including:

* How to set up your development environment
* Contribution workflow
* How to report bugs
* How to suggest features
* Code style and testing requirements

If you're looking for something to work on, check issues labeled:

* `good first issue`
* `help wanted`
* `documentation`
* `enhancement`

---

# 🔐 Privacy

MindMirror is designed with privacy in mind.

When configured with local AI through Ollama, your AI processing can happen on your own machine rather than being sent to a third-party AI provider.

However, your final privacy guarantees depend on your deployment configuration, infrastructure, database, AI provider, and environment.

Always review your configuration before using real sensitive information.

---

# ⚠️ Disclaimer

MindMirror is a software project for **self-reflection and emotional support**.

It is **not a replacement for a licensed mental-health professional, diagnosis, treatment, or emergency services**.

If someone is experiencing a mental-health emergency or is in immediate danger, they should contact appropriate local emergency services or a qualified professional.

---

# 📄 License

MindMirror is released under the **MIT License**.

See [LICENSE](LICENSE) for details.

---

<p align="center">

**Built with ❤️ by Hassan Faryad**

</p>
