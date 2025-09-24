# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses a **Makefile** for all development operations. Key commands:

**Service Management:**
- `make up` - Start all services (Django, PostgreSQL, Redis)
- `make down` - Stop all services  
- `make build` - Build Docker images
- `make restart` - Restart all services

**Development:**
- `make bash` - Enter Django container bash
- `make shell` - Enter Django shell (uses shell_plus)
- `make dbshell` - Enter PostgreSQL shell

**Database:**
- `make migrate` - Apply migrations
- `make makemigrations` - Create new migrations
- `make makemigrations app=<name>` - Create migrations for specific app
- `make createsuperuser` - Create Django superuser

**Code Quality:**
- `make lint` - Check code with ruff (apps and config dirs only)
- `make format` - Format code with ruff (includes unsafe fixes and import sorting)
- `make check` - Run both lint and test
- `make test` - Run tests with pytest
- `make test-coverage` - Run tests with coverage reporting

**Package Management:**
- `make install` - Install dependencies with uv
- `make list_packages` - List installed packages

## Project Architecture

**Core Structure:**
```
apps/
├── core/           # Base models (Category with MPTT), WebSocket consumers, services
├── questions/      # Question model and admin
├── interviews/     # Interview sessions and answer models
config/             # Django settings and URL configuration
```

**Key Technologies:**
- **Django 5.2+** with Python 3.12+
- **PostgreSQL** for primary database
- **Redis** for caching and WebSocket channel layer
- **Docker Compose** for containerization
- **MPTT** (Modified Preorder Tree Traversal) for hierarchical categories
- **Django Channels** for WebSocket support
- **uv** for Python package management

**AI/Audio Components:**
- **OpenAI GPT-3.5-turbo** via LangChain for answer analysis
- **ElevenLabs TTS** for high-quality text-to-speech generation  
- **ElevenLabs STT** for speech-to-text transcription
- **Multi-language support** with auto-detection

**Key Models:**
- `Category` (core) - Hierarchical categories using MPTT
- `Question` (questions) - Interview questions with difficulty levels and types
- `InterviewSession` (interviews) - User interview sessions 
- `Answer` (interviews) - User answers with LLM analysis and detailed scoring

**Important Services:**
- `InterviewService` (core/services.py) - Manages interview flow, question selection, answer storage
- `LLMAnswerAnalyzer` (core/llm_analyzer.py) - Analyzes answers using OpenAI API with detailed criteria
- `ElevenLabsTTSService` (core/elevenlabs_tts_service.py) - ElevenLabs TTS with multiple voices
- `ElevenLabsSTTService` (core/elevenlabs_stt_service.py) - ElevenLabs speech recognition
- `elevenlabs_service.py` - Unified service layer with backward compatibility

**WebSocket Architecture:**
- Uses Django Channels with Redis backend
- Interview flow handled via WebSocket consumers
- Real-time audio/text exchange for voice interviews

## Development Notes

**Environment Setup:**
- All development happens in Docker containers
- Uses `uv` instead of pip for faster dependency management
- Environment variables configured via `.env` file
- **Required API Keys**: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`

**Code Standards:**
- **Ruff** for linting and formatting (line length: 88 chars)  
- **Python 3.12+** target version
- **Russian language** used in admin interface (`LANGUAGE_CODE = "ru"`)
- Excludes migrations from linting

**Testing:**
- Uses **pytest** for testing framework
- Coverage reporting with HTML output
- Tests should cover core business logic in services

**Database:**
- Uses PostgreSQL 15 with health checks
- Migrations managed through Django ORM
- MPTT handles tree operations for categories

**Static Files:**
- Static files served from `/static/` URL
- Media files served from `/media/` URL
- Uses Docker volumes for persistence

## Common Patterns

**Interview Flow:**
1. User starts session via `InterviewService.start_interview()`
2. Questions selected randomly from filtered queryset
3. Answers processed by `LLMAnswerAnalyzer` with detailed scoring
4. Session statistics calculated in `get_session_stats()`

**AI Integration:**
- OpenAI API key required for LLM analysis
- ElevenLabs API key required for TTS/STT
- LLM prompts in Russian for technical interview analysis
- Detailed JSON-based scoring across 5 criteria
- Streaming feedback generation for real-time responses

**Audio Processing:**
- **ElevenLabs TTS** with cloud-based high-quality voices
- **ElevenLabs STT** with multi-language auto-detection
- Base64 audio encoding for WebSocket transmission  
- Chunked audio generation for streaming responses
- Voice selection from preset configurations or custom voice IDs
- Configurable voice parameters (stability, similarity, style)