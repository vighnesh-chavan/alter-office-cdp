# Customer Data Platform (CDP) API

## Overview

This project implements a Customer Data Platform (CDP) API using FastAPI, MongoDB, and OpenAI's GPT models. It ingests user data, merges and segments user profiles, and enables querying of user cohorts and profiles. The system is designed for scalable, asynchronous processing and leverages background tasks for efficient data handling.

---

## Features

- **User Data Ingestion**: Bulk ingest user data (email, cookie, demographics, interests, etc.) via a REST API.
- **Profile Merging**: Automatically merges user records based on email or cookie, deduplicating and updating interests, demographics, and other fields.
- **Background Processing**: Uses FastAPI's background tasks to process and segment users asynchronously after ingestion.
- **AI-Powered Segmentation**: Assigns users to cohorts using OpenAI's GPT models, based on their interests and a set of predefined cohorts.
- **Cohort Querying**: Retrieve users in a given cohort, sorted by similarity score.
- **Profile Querying**: Fetch a user's profile by email or cookie.
- **MongoDB Integration**: All data is stored and managed in MongoDB, with robust connection and CRUD utilities.
- **Dockerized**: Includes a Docker Compose setup for easy local development and deployment.

---

## Architecture

- **FastAPI**: Main API server (`main.py`).
- **MongoDB**: Data storage, managed via `services/mongo_service.py`.
- **OpenAI GPT**: Used for cohort segmentation in `services/ai_service.py` and `utils/segmentation_prompt.py`.
- **Background Tasks**: User processing and segmentation are performed asynchronously after ingestion.
- **Data Models**: Defined using Pydantic in `utils/data_models.py`.

---

## API Endpoints

### 1. Ingest User Data

`POST /api/ingest`

- Accepts a batch of user data.
- Stores raw data in MongoDB.
- Triggers background processing for merging and segmentation.

### 2. Get User Profile

`GET /api/user?email=...&cookie=...`

- Fetches a user profile by email or cookie.

### 3. Get Users by Cohort

`GET /api/cohort/users?cohort=...&limit=...&offset=...`

- Returns users in a specified cohort, sorted by similarity score, with pagination.

---

## Data Flow

1. **Ingestion**: User data is posted to `/api/ingest`.
2. **Raw Storage**: Data is stored in the `raw_data` collection.
3. **Background Processing**:
   - Merges user profiles (by email/cookie).
   - Updates interests, demographics, and other fields.
   - Calls OpenAI GPT to assign cohorts based on interests.
   - Stores cohort assignments in `cohort_data` and updates user profiles.
4. **Querying**: Users and cohorts can be queried via the API.

---

## Background Processing

- Implemented using FastAPI's `BackgroundTasks`.
- Each ingested user is processed asynchronously:
  - Merging logic ensures deduplication and up-to-date profiles.
  - Segmentation logic assigns cohorts using AI.
- This design ensures the API remains responsive and scalable.

---

## AI Segmentation

- Uses OpenAI's GPT-4.1-nano model to map user interests to predefined cohorts.
- Prompts are defined in `utils/segmentation_prompt.py`.
- Only valid JSON responses are accepted; retries up to 5 times for valid output.
- Cohorts and similarity scores are stored for each user.

---

## MongoDB Usage

- Connection and CRUD utilities in `services/mongo_service.py`.
- Collections:
  - `raw_data`: Stores all ingested raw user data.
  - `user_profiles`: Stores merged user profiles.
  - `cohort_data`: Stores cohort assignments and similarity scores.

---

## Docker Compose

The project includes a `docker-compose.yml` for local development:

```yaml
version: "3.8"

services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: cdp
    # Data is not persisted between runs (no volumes enabled)
```

- **MongoDB** runs in a container on port 27017.
- The default database is `cdp`.
- Data is ephemeral by default (no persistent volume).

---

## Setup & Running

### 1. Clone the Repository

```bash
git clone <repo-url>
cd alter-office-cdp
```

### 2. Setup & Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file with:

```
MONGO_URI=mongodb://localhost:27017/cdp
OPENAI_API_KEY=your_openai_api_key
```

### 4. Start MongoDB (via Docker Compose)

```bash
docker compose up -d
```

### 5. Run the API Server

```bash
uvicorn main:app --reload
```

---

## File Structure

```
.
├── main.py                      # FastAPI app and API endpoints
├── services/
│   ├── ai_service.py            # OpenAI GPT integration for segmentation
│   └── mongo_service.py         # MongoDB connection and CRUD utilities
├── utils/
│   ├── data_handling.py         # User merging, segmentation, and background logic
│   ├── data_models.py           # Pydantic models for API and DB
│   └── segmentation_prompt.py   # Prompt templates for AI segmentation
├── docker-compose.yml           # Docker Compose for MongoDB
└── ...
```

---

## Testing

This project includes two main test scripts to validate the core functionality of user merging and API endpoints:

### 1. testmerging.py

- **Purpose**: Validates the user merging logic, ensuring that users are correctly merged based on email and/or cookie, and not merged when identities are distinct.
- **What it tests:**
  - Ingesting a new user.
  - Merging users with the same cookie but different emails.
  - Merging users with the same email but different cookies.
  - Ensuring users with different emails and cookies are not merged.
- **How to use:**
  - Run this script first to set up and verify the merging logic:
    ```bash
    python testmerging.py
    ```

### 2. testapi.py

- **Purpose**: Tests the main API endpoints for ingestion, user profile retrieval, and cohort querying.
- **What it tests:**
  - Ingesting multiple users via the API.
  - Fetching user profiles by email and cookie.
  - Retrieving users by cohort with pagination.
- **How to use:**
  - After running `testmerging.py`, run this script to validate the API endpoints:
    ```bash
    python testapi.py
    ```

> **Note:** Ensure the FastAPI server is running (`uvicorn main:app --reload`) and MongoDB is up before running the tests.

