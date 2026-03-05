# Quick Setup Guide (Production / Separate PC)

This guide explains how to deploy the Intelligent Examination Submission Framework on a brand new machine in under 5 minutes. 

You **do not** need to download the source code, install Python packages, or compile machine learning models. Everything is pre-built, optimized, and hosted on Docker Hub.

## Prerequisites

1. A computer or server running **Linux, Windows, or macOS**.
2. **Docker installed**. ([Download Docker Desktop](https://www.docker.com/products/docker-desktop/) or install the Docker Engine).

## Installation Steps

### Step 1: Create a Project Folder
On the new PC, open your terminal (or Command Prompt) and create an empty folder for the project:
```bash
mkdir exam-framework-deployment
cd exam-framework-deployment
```

### Step 2: Download the Deployment Configuration
Download the pre-configured `docker-compose.hub.yml` file. This single file contains all the instructions Docker needs to fetch and wire the cloud images together.

*(You can copy this file manually, or use `curl` to download it if it's hosted publicly)*:

```yaml
curl -O "https://raw.githubusercontent.com/d-kavinraja/Intelligent-Examination-Submission-Framework-for-LMS/complete-application-setup-local-remote/docker-compose.hub.yml?v=2"
```

### Step 3: Start the Framework!
Run the following command to download the pre-compiled images from Docker Hub and start the entire stack in the background:

```bash
docker compose -f docker-compose.hub.yml up -d
```

> **Note:** The first time you run this command, it will take several minutes to download the Machine Learning image because it contains the PyTorch AI libraries (~5 GB). 

## Verification & Usage

Once Docker finishes downloading and the console says `Running`, the platform is live locally!

You can access the services in any web browser on that PC:

1. **Main Gateway & Landing Page**: [http://localhost:8080](http://localhost:8080)
2. **Staff Portal**: [http://localhost:8000/portal/staff](http://localhost:8000/portal/staff)
   - *Default Login*: Username `admin` / Password `admin123`
3. **Student Portal**: [http://localhost:8000/portal/student](http://localhost:8000/portal/student)
4. **Email / Notification Testing (MailHog)**: [http://localhost:8025](http://localhost:8025)
5. **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Managing the Deployment

- **To Stop the Servers:**
  ```bash
  docker compose -f docker-compose.hub.yml down
  ```
  *(Don't worry, your database records and uploaded examination sheets are safely persisted behind the scenes!)*

- **To View Real-time Logs (e.g., if there's an error):**
  ```bash
  docker compose -f docker-compose.hub.yml logs -f
  ```

- **To Update to the Latest Version:**
  If the developers push new code to Docker Hub, you can update your stack by running:
  ```bash
  docker compose -f docker-compose.hub.yml pull
  docker compose -f docker-compose.hub.yml up -d
  ```
