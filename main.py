from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from services.mongo_service import *
from utils.data_models import *
from utils.data_handling import process_and_segment_user
from utils.data_handling import flatten_dict
from dotenv import load_dotenv

load_dotenv()

# ---------------------- FastAPI App ----------------------

app = FastAPI(title="Customer Data Platform API")


# Background Task Placeholder


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_user_data(payload: IngestRequest, background_tasks: BackgroundTasks):
    try:
        users_data = [user.dict() for user in payload.data]

        # ✅ 1. Bulk insert raw data (no change)
        insert_into_mongo("raw_data", users_data)

        # ✅ 2. Process each user in the background (merging + segmentation together)
        for user in users_data:
            background_tasks.add_task(process_and_segment_user, user)

        return IngestResponse(
            status="success", records_processed=len(users_data), errors=[]
        )

    except Exception as e:
        return IngestResponse(status="failure", records_processed=0, errors=[str(e)])


# Get User Endpoint


@app.get("/api/user", response_model=UserProfileResponse)
async def get_user(
    cookie: Optional[str] = Query(None), email: Optional[EmailStr] = Query(None)
):
    if not cookie and not email:
        raise HTTPException(
            status_code=400, detail="Either cookie or email must be provided."
        )

    # Query using emails and cookies arrays
    query = {"$or": []}
    if email:
        query["$or"].append({"emails": email})
    if cookie:
        query["$or"].append({"cookies": cookie})
    if not query["$or"]:
        raise HTTPException(
            status_code=400, detail="No valid query parameter provided."
        )

    results = fetch_from_mongo("user_profiles", query)

    if not results:
        raise HTTPException(status_code=404, detail="User not found.")

    user = results[0]
    user.pop("_id", None)

    return UserProfileResponse(user_profile=user)


# Get Users by Cohort Endpoint


@app.get("/api/cohort/users", response_model=SimilarUsersResponse)
async def get_users_from_cohort(
    cohort: str, limit: int = Query(10, ge=1), offset: int = Query(0, ge=0)
):
    if not cohort:
        raise HTTPException(status_code=400, detail="Cohort must be provided.")
    # 1. Lowercase the cohort
    cohort_lower = cohort.lower()
    # 2. Query the 'cohort_data' collection for the cohort
    query = {"cohort": cohort_lower}
    # 3. Only return email and similarity_score, 4. Order by similarity_score desc, updated_at desc, email asc
    sort = [("similarity_score", -1), ("updated_at", -1), ("email", 1)]

    # Direct pymongo usage for projection and pagination

    client = connect_to_mongo()
    db = client.get_default_database()
    collection = db["cohort_data"]
    cursor = (
        collection.find(query, {"email": 1, "similarity_score": 1, "_id": 0})
        .sort(sort)
        .skip(offset)
        .limit(limit)
    )

    users = []
    for doc in cursor:
        email = doc.get("email", "unknown@example.com")
        similarity_score = doc.get("similarity_score", 0)
        # 5. Divide similarity_score by 100 and return as float
        similarity_score = float(similarity_score) / 100.0
        users.append({"email": email, "similarity_score": similarity_score})

    return SimilarUsersResponse(cohort=cohort, users=users)
