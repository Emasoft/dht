# DHT Development Plan & Architecture

## 🏗️ **ARCHITECTURAL UNDERSTANDING**

### **DHT Repository vs User Repository**

| **Aspect** | **DHT Repository** | **User Repository** |
|------------|-------------------|---------------------|
| **Purpose** | The development toolkit itself | User's actual project |
| **Location** | `/Users/emanuelesabetta/Code/DHT/dht/` | User's project directory |
| **CI/CD** | `.github/workflows/` (DHT's own) | `.github/workflows/` (generated from DHT templates) |
| **Templates** | `src/DHT/GITHUB_WORKFLOWS/*.yml` with `{REPO_NAME}` | Customized workflows with actual repo name |
| **Configuration** | `pyproject.toml` (DHT as package) | `.dhtconfig` + `pyproject.toml` (user's project) |

### **Template System Workflow**
```
1. User runs: dhtl init
2. DHT reads: src/DHT/GITHUB_WORKFLOWS/ubuntu-tests.yml
   Content: paths-ignore: - '{REPO_NAME}/website/**'
3. DHT replaces: {REPO_NAME} → user-project-name  
4. DHT writes: user-project/.github/workflows/ubuntu-tests.yml
   Content: paths-ignore: - 'user-project-name/website/**'
5. User gets: Fully customized CI/CD for their project
```

---

## ✅ **COMPLETED TASKS**

### **1. Template System Restoration**
- ✅ **Restored GitHub workflow templates** with proper `{REPO_NAME}` placeholders
- ✅ **Restored pre-commit template** with `{REPO_NAME}` placeholder
- ✅ **Updated tests** to verify templates contain placeholders (not remove them)
- ✅ **Fixed critical architectural misunderstanding**

### **2. DHT Infrastructure**
- ✅ **Created DHT's own CI/CD** in `.github/workflows/`
  - `dht-tests.yml`: Tests DHT itself across Python 3.10-3.12
  - `dht-release.yml`: Publishes DHT to PyPI
- ✅ **Separated DHT's workflows from user templates**
- ✅ **Resolved duplicate function issues** (lint_command)

### **3. Code Quality**
- ✅ **Shell script modularity** verified and improved
- ✅ **Template placeholder integrity** maintained
- ✅ **Test coverage** for template system

---

## 🎯 **PRIORITY DEVELOPMENT ROADMAP**

### **Phase 1: Core Template System (HIGH PRIORITY)**

#### **Task 1: Design Template Rendering Engine**
```python
# src/DHT/modules/template_renderer.py
class TemplateRenderer:
    def render_template(self, template_path: Path, variables: dict) -> str:
        """Replace placeholders with actual values"""
        
    def deploy_templates(self, user_project_path: Path, repo_name: str):
        """Deploy all templates to user project"""
```

**Placeholders to support:**
- `{REPO_NAME}` → User's repository name
- `{REPO_OWNER_OR_ORGANIZATION}` → GitHub username/org
- `{AUTHOR_NAME_OR_REPO_OWNER}` → Author name
- `{PYTHON_VERSION}` → Detected Python version
- `{PROJECT_TYPE}` → Detected project type (web-api, cli, library)

#### **Task 2: Implement `dhtl init` Command**
```bash
# User workflow:
cd my-awesome-project/
dhtl init

# DHT actions:
1. Analyze project structure
2. Create .dhtconfig with minimal settings
3. Deploy GitHub workflows from templates
4. Deploy git hooks from templates  
5. Set up Python environment with uv
6. Install development tools
```

#### **Task 3: Implement `dhtl setup` Command**
```bash
# User workflow:
git clone user-repo
cd user-repo
dhtl setup

# DHT actions:
1. Read .dhtconfig
2. Regenerate exact environment
3. Install dependencies with uv sync
4. Validate environment matches expectations
```

---

### **Phase 2: Project Intelligence (MEDIUM PRIORITY)**

#### **Task 4: Project Type Detection**
- **Framework Detection**: Django, Flask, FastAPI, CLI tools, libraries
- **Language Detection**: Multi-language projects (Python + Node.js, etc.)
- **Dependency Analysis**: Parse requirements, detect system dependencies

#### **Task 5: Smart Configuration Generation**
- **Minimal .dhtconfig**: Only store non-inferrable settings
- **Auto-detect**: Python version, project type, required tools
- **Platform Mapping**: System dependencies for different OS

#### **Task 6: Environment Regeneration**
- **Deterministic Builds**: Exact tool versions across platforms
- **UV Integration**: Python version management and virtual environments
- **Validation**: Verify environment matches original developer's setup

---

### **Phase 3: Advanced Features (LOW PRIORITY)**

#### **Task 7: Multi-Platform Support**
- **Windows Compatibility**: Git Bash, PowerShell, WSL
- **macOS/Linux**: Native shell integration
- **Docker Integration**: Containerized development environments

#### **Task 8: CI/CD Enhancement**
- **Multiple CI Providers**: GitHub Actions, GitLab CI, Azure DevOps
- **Testing Strategies**: Unit, integration, end-to-end
- **Security Scanning**: Automated vulnerability detection

---

## 📋 **CURRENT FILE STRUCTURE**

### **DHT Repository Structure**
```
dht/                                    # DHT repository
├── .github/workflows/                  # DHT's own CI/CD ✅
│   ├── dht-tests.yml                  # Tests DHT itself ✅
│   └── dht-release.yml                # Publishes DHT to PyPI ✅
├── src/DHT/
│   ├── modules/                        # DHT core functionality
│   ├── GITHUB_WORKFLOWS/              # TEMPLATES for users ✅
│   │   ├── ubuntu-tests.yml           # Template with {REPO_NAME} ✅
│   │   ├── docker-release.yml         # Template with {REPO_NAME} ✅
│   │   └── ...                        # More templates ✅
│   ├── hooks/                         # TEMPLATES for git hooks ✅
│   │   └── .pre-commit-config.yaml    # Template with {REPO_NAME} ✅
│   └── ...
├── tests/                             # DHT's own tests ✅
│   ├── unit/test_critical_fixes.py    # Validates template system ✅
│   └── ...
└── pyproject.toml                     # DHT as installable package
```

### **Generated User Repository Structure**
```
user-project/                          # User's project (generated by DHT)
├── .github/workflows/                 # Generated FROM DHT templates
│   ├── ubuntu-tests.yml              # Customized for user-project
│   └── ...
├── .dhtconfig                         # DHT configuration
├── .pre-commit-config.yaml           # Generated FROM DHT template
├── pyproject.toml                    # User's project config
└── ...
```

---

## 🔧 **IMPLEMENTATION DETAILS**

### **Template Variables System**
```yaml
# Example .dhtconfig generated by DHT
version: "1.0"
project:
  name: "my-awesome-project"
  type: "web-api"
  owner: "username"
  organization: "my-org"
python:
  version: "3.11"
templates:
  github_workflows: true
  pre_commit_hooks: true
  docker_support: false
```

### **Template Rendering Logic**
```python
def render_github_workflows(project_config: dict):
    """Render all GitHub workflow templates for user project"""
    template_dir = Path("src/DHT/GITHUB_WORKFLOWS")
    user_workflows_dir = Path(project_config['path']) / ".github" / "workflows"
    
    variables = {
        'REPO_NAME': project_config['name'],
        'REPO_OWNER_OR_ORGANIZATION': project_config['owner'],
        'PYTHON_VERSION': project_config['python']['version'],
    }
    
    for template_file in template_dir.glob("*.yml"):
        rendered_content = render_template(template_file, variables)
        output_file = user_workflows_dir / template_file.name
        output_file.write_text(rendered_content)
```

---

## 🚨 **CRITICAL LESSONS LEARNED**

### **1. Template Files Are Not Broken Code**
- ❌ **Wrong**: `{REPO_NAME}` is a syntax error that needs fixing
- ✅ **Correct**: `{REPO_NAME}` is a template placeholder for user substitution

### **2. DHT vs User Repository Separation**
- ❌ **Wrong**: `src/DHT/GITHUB_WORKFLOWS/` are DHT's own workflows
- ✅ **Correct**: They are templates that DHT deploys to user projects

### **3. Template System Architecture**
- ❌ **Wrong**: Fix placeholders to make files compile
- ✅ **Correct**: Preserve placeholders for template rendering system

### **4. Testing Strategy**
- ❌ **Wrong**: Test that templates have no placeholders
- ✅ **Correct**: Test that templates maintain proper placeholders

---

## 📊 **SUCCESS METRICS**

### **Phase 1 Success Criteria**
- [ ] `dhtl init` creates working user project with customized workflows
- [ ] `dhtl setup` reproduces exact environment from .dhtconfig
- [ ] Templates render correctly with user-specific values
- [ ] All template placeholders work across different project types

### **Phase 2 Success Criteria**  
- [ ] Auto-detection works for 10+ common project patterns
- [ ] Cross-platform environment reproduction (Windows, macOS, Linux)
- [ ] Minimal .dhtconfig contains only non-inferrable settings

### **Phase 3 Success Criteria**
- [ ] DHT manages complex multi-language projects
- [ ] Integration with multiple CI/CD providers
- [ ] Docker containerization support

---

## 🔄 **NEXT IMMEDIATE ACTIONS**

1. **Design Template Renderer** - Core engine for placeholder substitution
2. **Implement `dhtl init`** - User project initialization with template deployment  
3. **Implement `dhtl setup`** - Environment regeneration from .dhtconfig
4. **Create Template Tests** - Validate template rendering works correctly
5. **Document Template System** - Guide for adding new templates

This development plan ensures DHT evolves into a comprehensive development toolkit while maintaining the correct architectural understanding of templates vs DHT's own code.