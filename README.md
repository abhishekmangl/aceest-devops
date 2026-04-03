ACEest Fitness & Gym – DevOps CI/CD Pipeline
> **BITS Pilani | Introduction to DevOps (CSIZG514/SEZG514/SEUSZG514) | S2-25 | Assignment 1**
A fully automated CI/CD pipeline for the ACEest Fitness & Gym management application, demonstrating Version Control, Containerisation, Automated Testing, and Continuous Integration using Git/GitHub, Docker, Pytest, GitHub Actions, and Jenkins.
---
Table of Contents
Project Structure
Application Overview
Local Setup & Execution
Running Tests Manually
Docker Build & Run
GitHub Actions Pipeline
Jenkins BUILD Integration
Jenkins Docker Note
API Reference
Version History (Git Strategy)
---
Project Structure
```
aceest-devops/
├── app.py                        # Flask web application
├── test_app.py                   # Pytest test suite (47 test cases)
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Multi-stage, non-root Docker image
├── Jenkinsfile                   # Declarative Jenkins pipeline (7 stages)
├── .gitignore
├── .github/
│   └── workflows/
│       └── main.yml              # GitHub Actions CI/CD pipeline
└── README.md
```
---
Application Overview
The ACEest Flask API exposes RESTful endpoints for managing gym clients and fitness programs. It was modularised from a desktop Tkinter application (versions 1.0 → 3.2.4) into a stateless web service suitable for containerised deployment.
Key capabilities:
List and retrieve fitness programs (Fat Loss, Muscle Gain, Beginner)
Register, update, and delete clients
Automatically calculate personalised daily calorie targets
Track weekly adherence percentages
---
Local Setup & Execution
Prerequisites
Python 3.10 or higher
pip
Docker Desktop (for container steps)
Steps
```bash
# 1. Clone the repository
git clone https://github.com/abhishekmangl/aceest-devops.git
cd aceest-devops

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask application
flask run --host=0.0.0.0 --port=5000

# 5. Verify it is running
curl http://localhost:5000/health
# → {"status": "healthy"}
```
---
Running Tests Manually
```bash
# Activate the virtual environment first (see above)

# Run all tests with verbose output
pytest test_app.py -v

# Run with coverage report
pytest test_app.py -v --cov=app --cov-report=term-missing

# Run a specific test class
pytest test_app.py::TestCalorieCalculation -v

# Run and generate XML reports (same as CI)
pytest test_app.py -v \
  --junitxml=test-results.xml \
  --cov=app --cov-report=xml:coverage.xml
```
Expected output: 47 tests, all passing, ≥70% coverage.
---
Docker Build & Run
Build the image
```bash
docker build -t aceest-fitness:latest .
```
The Dockerfile uses a multi-stage build:
Stage	Purpose
`builder`	Install Python dependencies into an isolated prefix
`runtime`	Slim final image — copies only the installed packages
Security features: runs as a non-root user (`aceest`), no development tools in the final image.
Run the container
```bash
docker run -d \
  --name aceest-app \
  -p 5000:5000 \
  aceest-fitness:latest

# Health check
curl http://localhost:5000/health
# → {"status": "healthy"}
```
Run tests inside the container
```bash
docker run --rm \
  -v $(pwd)/test_app.py:/app/test_app.py:ro \
  --entrypoint python \
  aceest-fitness:latest \
  -m pytest test_app.py -v
```
Stop and remove
```bash
docker stop aceest-app && docker rm aceest-app
```
---
GitHub Actions Pipeline
File: `.github/workflows/main.yml`
Trigger: Every `push` or `pull_request` targeting `main` / `master`.
```
Push / PR
    │
    ▼
┌─────────────────────┐
│  Stage 1: Build &   │  • Installs dependencies
│  Lint               │  • Runs flake8 (syntax + style)
│                     │  • Verifies app imports cleanly
└────────┬────────────┘
         │ on success
         ▼
┌─────────────────────┐
│  Stage 2: Docker    │  • docker/build-push-action (Buildx)
│  Image Assembly     │  • Smoke-tests container via /health
│                     │  • Saves image as pipeline artifact
└────────┬────────────┘
         │ on success
         ▼
┌─────────────────────┐
│  Stage 3: Automated │  • Loads saved Docker image
│  Testing (Pytest)   │  • Runs full Pytest suite inside container
│                     │  • Uploads JUnit XML + coverage reports
└─────────────────────┘
```
Each stage is a separate GitHub Actions job with an explicit `needs:` dependency, so a failure in any stage stops subsequent stages immediately.
> **Docker is fully validated via GitHub Actions** — the Docker image is built, smoke-tested, and pytest is executed inside the container on every push. See the Actions tab for proof.
---
Jenkins BUILD Integration
File: `Jenkinsfile`
Jenkins Setup (one-time)
Install Jenkins (local or Docker):
```bash
   docker run -d -p 8080:8080 -p 50000:50000 \
     -v jenkins_home:/var/jenkins_home \
     jenkins/jenkins:lts
   ```
In the Jenkins UI, install the Pipeline and JUnit plugins.
Create a new Pipeline project → set SCM to your GitHub repo → set Script Path to `Jenkinsfile`.
Ensure the Jenkins agent has Python 3, pip, Docker, and curl available.
Jenkins Pipeline Stages
Stage	Description	Status
Checkout	Pulls latest code from GitHub via `checkout scm`	✅ Passing
Environment Setup	Creates a Python venv and installs all dependencies	✅ Passing
Lint	Runs `flake8` — fails the build on syntax errors	✅ Passing
Unit Tests	Runs `pytest` — 47 tests with JUnit XML output	✅ Passing
Docker Build	Builds the production Docker image	✅ Documented*
Docker Smoke Test	Spins up container and hits `/health`	✅ Documented*
Quality Gate	Fails if coverage drops below 70%	✅ Passing
How the Jenkins BUILD relates to GitHub Actions
```
Developer pushes code
        │
        ├──→ GitHub Actions (automatic, cloud)
        │         └── Lint → Docker Build → Pytest in container
        │
        └──→ Jenkins (webhook or manual trigger, self-hosted)
                  └── Checkout → Lint → Pytest → Docker Build
                      → Smoke Test → Quality Gate
```
Jenkins acts as a secondary, controlled build environment — it validates that the code compiles and passes tests in an environment you fully control, independent of GitHub's infrastructure.
---
Jenkins Docker Note
> **Infrastructure Note for Evaluators**
The Jenkins server used for this assignment is hosted on an AWS EC2 instance. The Jenkins process runs under the `jenkins` OS user which does not have permission to access `/var/run/docker.sock` on this particular server configuration (permission denied error on the Docker daemon socket).
Docker containerisation is fully demonstrated via GitHub Actions where:
The Docker image is built successfully using `docker/build-push-action`
The container is smoke-tested via `/health` endpoint
The full Pytest suite (47 tests) is executed inside the Docker container
To enable Docker in Jenkins on a standard server, the fix is:
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```
The Jenkinsfile is fully written with Docker Build and Smoke Test stages — they will execute correctly on any Jenkins server where the jenkins user has Docker socket access.
---
API Reference
Method	Endpoint	Description
GET	`/`	Service info
GET	`/health`	Health check
GET	`/programs`	List all programs
GET	`/programs/<n>`	Program details
GET	`/clients`	List all clients
POST	`/clients`	Create a client
GET	`/clients/<n>`	Get a client
PUT	`/clients/<n>`	Update a client
DELETE	`/clients/<n>`	Delete a client
GET	`/clients/<n>/calories`	Get calorie target
Example: Create a client
```bash
curl -X POST http://localhost:5000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Arjun Kumar",
    "age": 28,
    "weight_kg": 75.0,
    "program": "Fat Loss (FL)"
  }'
```
Response `201`:
```json
{
  "name": "Arjun Kumar",
  "age": 28,
  "weight_kg": 75.0,
  "program": "Fat Loss (FL)",
  "calories_per_day": 1650,
  "adherence_pct": 0
}
```
---
Version History (Git Strategy)
Commits follow the Conventional Commits standard. Branches follow a simple feature-branch workflow:
```
main           ← stable, protected branch
  └── feature/flask-api          (Phase 1 – app modularisation)
  └── feature/pytest-suite       (Phase 3 – unit tests)
  └── feature/dockerise          (Phase 4 – Dockerfile)
  └── feature/github-actions     (Phase 6 – CI/CD YAML)
  └── feature/jenkinsfile        (Phase 5 – Jenkins pipeline)
```
Example commit messages used in this project:
```
feat: initialise Flask app from ACEest v3.2.4 baseline
feat: add /programs and /clients REST endpoints
feat: add validate_client_payload and calculate_calories helpers
test: add 47 pytest cases covering CRUD, validation, calories
docker: add multi-stage Dockerfile with non-root runtime user
ci: add GitHub Actions pipeline with lint, docker-build, pytest stages
ci: add Jenkinsfile with quality gate (>=70% coverage)
fix: add Docker socket permission note in README
docs: write comprehensive README
```
---
ACEest Fitness & Gym | BITS Pilani DevOps Assignment 1 | 2026
