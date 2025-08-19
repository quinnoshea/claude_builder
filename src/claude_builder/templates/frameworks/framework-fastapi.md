<!-- REPLACE:architecture -->
**Project Type**: ${project_type}  
**Framework**: FastAPI
**Complexity**: ${complexity_level}

This FastAPI project follows modern Python web development patterns:

### FastAPI Architecture Patterns
- **Dependency Injection**: Use FastAPI's dependency system for shared resources
- **Pydantic Models**: Define request/response models with type validation
- **Router Organization**: Group related endpoints using APIRouter
- **Middleware**: Implement cross-cutting concerns (CORS, logging, auth)
- **Background Tasks**: Use FastAPI's background task system for async operations

### Recommended Project Structure
```
src/
├── main.py              # Application entry point
├── api/
│   ├── __init__.py
│   ├── routes/          # API route definitions
│   └── dependencies.py  # Shared dependencies
├── models/
│   ├── __init__.py
│   └── schemas.py       # Pydantic models
├── core/
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   └── database.py      # Database connections
└── tests/
    ├── __init__.py
    └── test_*.py        # Test modules
```
<!-- /REPLACE:architecture -->

<!-- REPLACE:getting-started -->
### FastAPI Prerequisites
- Python 3.8+ with FastAPI support
- Understanding of async/await patterns
- Basic knowledge of REST API design

### FastAPI Setup Instructions
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run development server: `uvicorn main:app --reload`
6. Open API docs: http://localhost:8000/docs

### FastAPI Key Commands
```bash
# Install FastAPI and dependencies
pip install "fastapi[all]" uvicorn

# Run development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run with gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Generate OpenAPI schema
python -c "import json; from main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json

# Run tests with FastAPI test client
pytest tests/ -v

# Database migrations (if using Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### FastAPI Development Tips
- Use the interactive API documentation at `/docs` for testing
- Leverage FastAPI's automatic request/response validation
- Use dependency injection for database connections and shared services
- Implement proper error handling with HTTPException
- Use background tasks for long-running operations
- Enable CORS if building a web frontend
<!-- /REPLACE:getting-started -->