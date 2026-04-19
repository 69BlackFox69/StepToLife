# StepToLife - Employment Support

A platform that helps users find employment in Slovakia using AI agents.

## Features

**4 interactive tabs powered by different AI agents:**

1. **Start** - Initial consultation to identify goals and Slovak language level
2. **Slovak Language** - Micro-lessons in Slovak for different levels (A1-C2)
3. **Resume** - Interactive professional resume creation with PDF export
4. **Jobs** - Job search and vacancy recommendations in Slovakia based on the resume

## Requirements

- Python 3.8+
- OpenAI API key

## Installation

### 1. Open the repository folder
```bash
cd "c:\New hakaton\StepToLife"
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure the .env file

Make sure your credentials are set in the `.env` file:

```env
OPENAI_API_KEY=sk-proj-...
FRONTEND_ORIGIN=http://localhost:5000
```

## Run the application

```bash
python app.py
```

The app will be available at: `http://localhost:5000`

## Project structure

```
StepToLife/
├── app.py                 # Main Flask application
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables
├── agents/                # AI agents package
│   ├── __init__.py
│   ├── base_agent.py      # Base agent class
│   ├── initial_agent.py   # Initial consultation agent
│   ├── language_agent.py  # Language learning agent
│   ├── resume_agent.py    # Resume creation agent
│   └── job_agent.py       # Job search agent
├── templates/             # HTML templates
│   └── index.html         # Main page with tabs
├── static/                # Static files
│   ├── style.css          # Application styles
│   └── script.js          # Client-side JavaScript
└── resumes/               # Folder for saved resume PDFs
```

## API Endpoints

### POST /api/chat/initial
Send a message to the first agent (initial consultation)

**Request:**
```json
{
  "user_id": "user_123",
  "message": "I want to find a job, I am from a marginalized group"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent response...",
  "user_info": {...},
  "knows_slovak": false
}
```

### POST /api/chat/language
Send a message to the language learning agent

**Request:**
```json
{
  "user_id": "user_123",
  "message": "Teach me a greeting",
  "lesson_level": "beginner"
}
```

### POST /api/chat/resume
Send information for resume creation

**Request:**
```json
{
  "user_id": "user_123",
  "message": "My name is Ivan Petrov"
}
```

### POST /api/chat/jobs
Search for jobs based on the resume

**Request:**
```json
{
  "user_id": "user_123",
  "message": "Find a job for me"
}
```

### GET /api/generate-pdf/{user_id}
Download the PDF version of the resume

## Highlights

- 🤖 Uses GPT-4o-mini for natural interaction
- 📚 Interactive micro-lessons in Slovak
- 📄 Automatic PDF resume generation
- 🔍 Job recommendations based on user profile
- 🎯 Support for marginalized groups
- 💬 Four specialized AI agents

## Tech stack

- **Backend:** Flask 2.3.0
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **AI:** OpenAI API (GPT-4o-mini)
- **PDF Generation:** ReportLab, fpdf2
- **Environment:** python-dotenv

## Support

For questions or issues, contact the development team.

## License

MIT License
