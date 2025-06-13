# DHT Implementation Examples

## Real-World Scenarios

### Scenario 1: Django Project on Mac → Ubuntu CI → Windows Developer

**Initial Setup (Mac Developer)**
```bash
$ cd django-blog
$ dhtl setup

🔍 Analyzing project...
✓ Detected: Django 4.2 project
✓ Found: PostgreSQL, Redis, Celery dependencies
✓ Python version: 3.11.7 (from pyproject.toml)

📦 Installing system dependencies...
✓ postgresql@14 (via brew)
✓ redis (via brew)

🐍 Creating Python 3.11.7 environment...
✓ Virtual environment created
✓ Dependencies installed from requirements.txt
✓ Development tools configured

📝 Generating .dhtconfig...
```

**Generated .dhtconfig**
```yaml
version: "2.0"
dht_version: "0.1.0"
fingerprint:
  created_at: "2024-12-06T15:30:00Z"
  created_by: "DHT/0.1.0"
  platform: "darwin-arm64"

# Python version not stored (already in pyproject.toml)

platform_deps:
  darwin:
    brew: ["postgresql@14", "redis"]
  linux:
    apt: ["libpq-dev", "redis-server", "postgresql-client"]
  windows:
    choco: ["postgresql14", "redis-64"]

validation:
  venv_checksum: "sha256:a1b2c3d4e5f6..."
  config_checksum: "sha256:9876543210fe..."
```

**Ubuntu CI Pipeline**
```bash
$ dhtl clone https://github.com/user/django-blog

🔄 Cloning repository...
✓ Repository cloned

🔍 Found .dhtconfig, regenerating environment...
✓ Python 3.11.7 installed via UV
✓ Platform: ubuntu-22.04 detected
✓ Installing: libpq-dev, redis-server, postgresql-client
✓ Dependencies restored from requirements.txt
✓ Environment checksum: sha256:a1b2c3d4e5f6... ✓ MATCH

🎉 Environment ready!
```

**Windows Developer**
```bash
> dhtl fork https://github.com/user/django-blog

🍴 Forking repository...
✓ Forked to windows-dev/django-blog

🔍 Found .dhtconfig, regenerating environment...
✓ Python 3.11.7 installed via UV
✓ Platform: windows-11 detected
✓ Installing via chocolatey: postgresql14, redis-64
✓ Dependencies restored from requirements.txt
✓ Git Bash detected, configuring Unix-style tools
✓ Environment checksum: sha256:a1b2c3d4e5f6... ✓ MATCH

💡 Note: Using WSL2 is recommended for better compatibility
```

### Scenario 2: FastAPI + React Project Migration

**Existing Project Structure**
```
my-app/
├── backend/
│   ├── requirements.txt     # FastAPI, SQLAlchemy, etc.
│   ├── requirements-dev.txt # pytest, black, etc.
│   └── app/
├── frontend/
│   ├── package.json        # React, TypeScript
│   └── src/
└── docker-compose.yml
```

**Running dhtl setup**
```bash
$ dhtl setup

🔍 Analyzing project...
✓ Detected: FastAPI backend + React frontend
✓ Found: Docker Compose configuration
⚠️ No pyproject.toml found, creating one...

📦 Migrating to modern Python packaging...
✓ Created pyproject.toml from requirements files
✓ Generated uv.lock for reproducible installs

🌐 Multi-language setup detected...
? How should Node.js be managed?
  1. Install in .venv using UV tools (recommended)
  2. Use system Node.js (version 18.17.0 detected)
  3. Use nvm (detected at ~/.nvm)
> 1

✓ Node.js 18.17.0 will be installed in .venv

📝 Generating .dhtconfig...
```

**Generated Configuration**
```yaml
# pyproject.toml (created)
[project]
name = "my-app-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "pydantic>=2.0.0",
    "uvicorn[standard]>=0.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.7.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
]

# .dhtconfig
version: "2.0"
languages:
  node:
    version: "18.17.0"
    installer: "uv tool"
    working_dir: "frontend"

services:
  postgres:
    detected_from: "docker-compose.yml"
    connection: "postgresql://localhost:5432/myapp"
  redis:
    detected_from: "backend/app/config.py"

platform_deps:
  darwin:
    brew: ["postgresql@14", "redis"]
  linux:
    apt: ["libpq-dev", "redis-server"]
```

### Scenario 3: Data Science Project with Conda Migration

**Existing environment.yml**
```yaml
name: ml-project
channels:
  - conda-forge
dependencies:
  - python=3.10
  - numpy=1.24.3
  - pandas=2.0.3
  - scikit-learn=1.3.0
  - matplotlib=3.7.2
  - jupyter=1.0.0
  - pip:
    - torch==2.0.1
    - transformers==4.31.0
```

**Migration Process**
```bash
$ dhtl setup --migrate-from conda

🔍 Analyzing Conda environment...
✓ Found environment.yml
✓ Detected: Data Science / ML project

🔄 Converting to UV-based workflow...
✓ Creating pyproject.toml with equivalent dependencies
⚠️ Note: CUDA support detected for PyTorch

? Select PyTorch variant:
  1. CPU only (smaller, works everywhere)
  2. CUDA 11.8 (requires NVIDIA GPU)
  3. CUDA 12.1 (latest, requires NVIDIA GPU)
> 2

✓ Dependencies converted
✓ Creating uv.lock for exact reproducibility

📊 Configuring Jupyter...
✓ Jupyter kernel will be installed in .venv
✓ Added nbqa for notebook linting
✓ Added notebook to pre-commit hooks

🎯 Migration complete!
   Old: conda activate ml-project
   New: source .venv/bin/activate
```

### Scenario 4: Legacy Project Modernization

**Before: Messy Project**
```
old-project/
├── requirements.txt        # Unpinned: django\nrequests\nmysql-python
├── test_stuff.py          # Uses unittest
├── my_tests.py           # Also unittest
├── main.py               # Mixed tabs/spaces
└── config.json           # Hardcoded secrets
```

**Modernization with dhtl**
```bash
$ dhtl setup --modernize

🔍 Analyzing legacy project...
⚠️ Found issues to fix:
   - Unpinned dependencies
   - unittest instead of pytest
   - No linting configuration
   - Hardcoded secrets detected
   - Mixed indentation

🔧 Modernizing project...

1️⃣ Upgrading dependencies:
   ✓ django → django>=4.2.0,<5.0
   ✓ requests → requests>=2.31.0
   ✓ mysql-python → mysqlclient>=2.2.0 (maintained fork)

2️⃣ Migrating to pytest:
   ✓ Converting test_stuff.py
     - self.assertEqual(a, b) → assert a == b
     - self.assertRaises → pytest.raises
   ✓ Converting my_tests.py
   ✓ Created pytest.ini with sensible defaults

3️⃣ Setting up code quality tools:
   ✓ Configured ruff (fast linting + formatting)
   ✓ Fixed mixed indentation (chose spaces)
   ✓ Created .pre-commit-config.yaml

4️⃣ Securing secrets:
   ✓ Created .env.template
   ✓ Moved secrets to environment variables
   ⚠️ Remember to add .env to .gitignore!

📝 Created modernization report: MODERNIZATION_REPORT.md
```

### Scenario 5: Complex Multi-Service Project

**Project Structure**
```
microservices-app/
├── services/
│   ├── auth/          # Go service
│   ├── api/           # FastAPI
│   ├── worker/        # Python + Rust extension
│   └── frontend/      # Next.js
├── shared/
│   └── proto/         # Protocol buffers
└── deploy/
    └── k8s/          # Kubernetes configs
```

**DHT Handles Complexity**
```bash
$ dhtl setup

🔍 Analyzing multi-service project...
✓ Detected: Microservices architecture
✓ Languages: Python, Go, Rust, TypeScript
✓ Deploy target: Kubernetes

🎯 Creating unified development environment...

1️⃣ Python services (api, worker):
   ✓ Python 3.11.7 environment
   ✓ Shared dependencies extracted to root pyproject.toml
   ✓ Service-specific deps in services/*/pyproject.toml

2️⃣ Go service (auth):
   ✓ Go 1.21 configured
   ✓ Will use 'uv run go' for consistent tooling

3️⃣ Rust extension (worker):
   ✓ Rust toolchain 1.73.0
   ✓ maturin configured for Python bindings
   ✓ Will build with 'uv run maturin develop'

4️⃣ Frontend (Next.js):
   ✓ Node.js 18.17.0 via UV tools
   ✓ pnpm configured for fast installs

5️⃣ Development tools:
   ✓ protoc for protocol buffers
   ✓ kubectl for K8s interaction
   ✓ skaffold for local K8s development
   ✓ pre-commit hooks for all languages

📝 Generated configurations:
   ✓ .dhtconfig (orchestrates everything)
   ✓ Makefile (common tasks)
   ✓ .vscode/settings.json (IDE configuration)
   ✓ scripts/dev.sh (one-command startup)

🚀 Start everything: ./scripts/dev.sh
```

### Scenario 6: CI/CD Integration

**.github/workflows/test.yml (generated)**
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11.7"]  # From .dhtconfig
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install DHT
      run: |
        curl -sSL https://dht.dev/install.sh | bash
        echo "$HOME/.dht/bin" >> $GITHUB_PATH
    
    - name: Regenerate environment
      run: |
        dhtl regenerate
        dhtl validate-env
    
    - name: Run tests
      run: |
        source .venv/bin/activate || .venv\Scripts\activate
        dhtl test
    
    - name: Upload coverage
      run: |
        source .venv/bin/activate || .venv\Scripts\activate
        dhtl coverage --upload
```

## Key Differentiators

### 1. **Intelligent Detection**
DHT doesn't ask unnecessary questions. It detects:
- Python version from multiple sources
- Framework from file patterns and imports
- Required system dependencies from Python packages
- Development workflow from existing tool configs

### 2. **Platform Abstraction**
Same commands work everywhere:
```bash
# These work identically on Mac/Linux/Windows:
dhtl setup
dhtl test
dhtl run python manage.py runserver
```

### 3. **Progressive Enhancement**
DHT improves projects without breaking them:
- Keeps existing configs working
- Adds modern tooling alongside
- Migrates incrementally when requested
- Never forces architectural changes

### 4. **Minimal Configuration**
.dhtconfig only stores what's absolutely necessary:
- ❌ NOT: Python packages (in pyproject.toml)
- ❌ NOT: Tool versions (in pyproject.toml) 
- ✅ YES: Platform-specific system packages
- ✅ YES: Multi-language tool versions
- ✅ YES: Environment checksums

### 5. **Verification Built-in**
Every regeneration is verified:
```bash
$ dhtl regenerate
...
✓ Environment checksum: sha256:a1b2c3... ✓ MATCH

# If mismatch:
⚠️ Environment differs from expected:
  - Expected: pandas==2.0.3
  - Found: pandas==2.1.0
  
Run 'dhtl fix-env' to resolve
```

This makes "works on my machine" impossible - either it matches exactly or DHT tells you why it doesn't.