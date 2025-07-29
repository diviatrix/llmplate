# LLM Template System Backend

Production-ready backend system for structured data generation using LLM models through OpenRouter and Ollama, with a powerful template system based on Jinja2.

## 🚀 Features

### Authentication & Security
- 🔐 **Multi-auth support**: Email/Password + OAuth2 (Google, GitHub)
- 🔑 **JWT tokens** with refresh mechanism
- 🛡️ **Role-based access** for templates (public/private)
- 🔒 **Secure password hashing** with bcrypt

### LLM Integration
- 🤖 **OpenRouter**: Access to 100+ models (Claude, GPT-4, Gemini, etc.)
- 🏠 **Ollama**: Local model support for privacy
- 💰 **Cost tracking**: Real-time pricing information
- 🔍 **Smart filters**: Free/paid, online-capable models
- ⚡ **Provider fallback**: Automatic switching on failures

### Template System
- 📝 **Jinja2 templates** with custom filters
- ✅ **3-tier validation**: Strict (JSON Schema), Custom rules, or None
- 🎨 **Template gallery** with examples
- 🔄 **Live preview** with variable substitution
- 📚 **Categories**: Education, Content, Research, Business
- 🏷️ **Tagging system** for organization

### Data Generation
- 🔄 **Background processing** with Celery (Mock for development)
- 📊 **8 export formats**: JSON, CSV, PDF, XLSX, MD, HTML, XML, TXT
- 📈 **Progress tracking** for long operations
- 💾 **Generation history** with search and filters
- 🔁 **Batch processing** support
- 💲 **Cost and token tracking**
- ⚡ **Real-time status updates**

### Developer Experience
- 📖 **Auto-generated API docs** (Swagger/ReDoc)
- 🧪 **100% test coverage** with TDD approach
- 🏭 **Factory pattern** for clean architecture
- 🐳 **Docker support** for easy deployment
- 📝 **Type hints** throughout the codebase

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-template-backend.git
cd llm-template-backend

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

The application will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Run the application
uvicorn app.main:app --reload
```

### Using Makefile

```bash
# Install dependencies
make install

# Run tests
make test

# Start application
make run

# See all commands
make help
```

## Development Workflow

We follow Test-Driven Development (TDD):

1. Write tests first
2. Run tests (should fail)
3. Write minimal code to pass
4. Run tests (should pass)
5. Refactor if needed

## 📁 Project Structure

```
llm-template-backend/
├── app/
│   ├── api/              # API endpoints (auth, providers, templates, generation)
│   ├── auth/             # Authentication logic (JWT, OAuth, password)
│   ├── models/           # MongoDB models (User, Template, Generation)
│   ├── providers/        # LLM providers (OpenRouter, Ollama)
│   ├── templates/        # Template engine (validator, renderer)
│   ├── generation/       # Generation logic (service, tasks, export)
│   ├── celery_app.py     # Celery configuration
│   ├── config.py         # Application configuration
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── tests/
│   ├── unit/             # Unit tests (165+ tests)
│   ├── integration/      # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── factories.py      # Test data factories
├── templates/
│   └── examples/         # Example JSON templates
├── docker/               # Docker configuration files
│   └── nginx.conf        # Nginx configuration
├── .github/
│   └── workflows/        # CI/CD pipelines
├── Dockerfile            # Production Docker image
├── Dockerfile.dev        # Development Docker image
├── docker-compose.yml    # Development environment
├── docker-compose.prod.yml # Production environment
├── Makefile             # Development commands
├── requirements.txt     # Python dependencies
└── requirements-dev.txt # Development dependencies
```

## 🧪 Testing

We follow Test-Driven Development (TDD) with comprehensive coverage:

- **Coverage**: 100% for all API endpoints
- **Test Types**: Unit, Integration, E2E
- **Tools**: pytest, factory-boy, faker, httpx
- **Mocking**: pytest-mock for external services
- **Fixtures**: Reusable test data and auth tokens

Run tests:
```bash
# All tests with coverage
pytest --cov=app

# Specific test file
pytest tests/unit/test_auth.py -v

# With coverage report
pytest --cov=app --cov-report=html
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with email/password
- `GET /auth/me` - Get current user
- `POST /auth/refresh` - Refresh access token
- `GET /auth/oauth/{provider}` - Start OAuth flow
- `GET /auth/oauth/{provider}/callback` - OAuth callback

### Providers
- `GET /providers` - List available providers
- `GET /providers/models` - List all models with filters
- `GET /providers/models/{model_id}` - Get model details
- `POST /providers/test` - Test provider connection

### Templates
- `POST /templates` - Create template
- `GET /templates` - List templates
- `GET /templates/{id}` - Get template
- `PUT /templates/{id}` - Update template
- `DELETE /templates/{id}` - Delete template
- `POST /templates/validate` - Validate template
- `POST /templates/preview` - Preview rendering
- `GET /templates/examples` - List examples
- `POST /templates/examples/{id}/import` - Import example

### Generation (Coming Soon)
- `POST /generate` - Start generation
- `GET /generate/{job_id}` - Check status
- `GET /generate/{job_id}/result` - Get result
- `GET /history` - Generation history

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t llm-template-backend .

# Run with docker-compose
docker-compose up -d
```

### Environment Variables
See `.env.example` for all required variables:
- `SECRET_KEY` - JWT secret key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `MONGODB_URL` - MongoDB connection string
- OAuth credentials for Google and GitHub

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests first (TDD)
4. Implement feature
5. Ensure 100% test coverage
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Based on ideas from [llm-data-gen](https://github.com/diviatrix/llm-data-gen)
- Built with FastAPI, MongoDB, and ❤️