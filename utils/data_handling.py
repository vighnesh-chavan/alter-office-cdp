import uuid
from datetime import datetime
from services.mongo_service import *
from services.ai_service import get_cohorts_from_interests
from decimal import Decimal, ROUND_HALF_UP


def flatten_dict(d):
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            items.extend(flatten_dict(v).items())
        else:
            items.append((k, v))
    return dict(items)


async def perform_segmentation(user_id):
    """
    For a given user_id, fetch the user from 'user_profiles', extract interests and emails,
    call get_cohorts_from_interests, and insert cohort data into 'cohort_data'.
    For each email and each cohort segment, insert a record (email, cohort as composite key).
    Also update the user's 'cohorts' field in user_profiles with the new cohort names.
    """
    # Fetch user document
    users = fetch_from_mongo("user_profiles", {"user_id": user_id})
    if not users:
        return  # User not found
    user = users[0]
    interests = user.get("interests", [])
    emails = user.get("emails", [])
    if not interests or not emails:
        return  # No interests or emails to segment

    segments = get_cohorts_from_interests(user_id, interests)
    if not segments:
        return  # No segments to insert

    cohort_entries = []
    cohort_names = set()
    for email in emails:
        # Delete all cohort_data entries for this email before inserting new ones
        delete_from_mongo("cohort_data", {"email": email})
        seen_cohorts = set()
        for segment in segments:
            cohort = segment.get("cohort")
            similarity_score = segment.get("similarity_score")
            if cohort and similarity_score is not None and cohort not in seen_cohorts:
                seen_cohorts.add(cohort)
                print("before similarity_score", similarity_score)
                similarity_score = int(float(similarity_score) * 100)
                print("similarity_score", similarity_score)
                cohort_entries.append(
                    {
                        "user_id": user_id,
                        "email": email,
                        "cohort": cohort,
                        "similarity_score": similarity_score,
                    }
                )
                cohort_names.add(cohort)
    if cohort_entries:
        insert_into_mongo("cohort_data", cohort_entries)
    # Update the user's cohorts field in user_profiles
    if cohort_names:
        update_in_mongo(
            "user_profiles",
            {"user_id": user_id},
            {"$set": {"cohorts": list(cohort_names)}},
        )


async def process_and_segment_user(user: dict):
    """
    Merges or creates user profile using UUID, updates emails, cookies, interests,
    and performs segmentation.
    """

    email = user.get("email")
    cookie = user.get("cookie")

    if not email and not cookie:
        return  # Skip processing if no identity present

    query = {"$or": []}
    if email:
        query["$or"].append({"emails": email})
    if cookie:
        query["$or"].append({"cookies": cookie})

    existing_users = fetch_from_mongo("user_profiles", query) if query["$or"] else []

    if existing_users:
        # Merge into first matched user
        existing_user = existing_users[0]
        user_id = existing_user["user_id"]

        # Merge emails
        updated_emails = set(existing_user.get("emails", []))
        incoming_email = user.get("email")
        if incoming_email:
            updated_emails.add(incoming_email)

        # Merge cookies
        updated_cookies = set(existing_user.get("cookies", []))
        incoming_cookie = user.get("cookie")
        if incoming_cookie:
            updated_cookies.add(incoming_cookie)

        # Merge interests (case-insensitive, new first, no duplicates)
        incoming_interests = user.get("interests", []) or []
        existing_interests = existing_user.get("interests", []) or []

        seen_lower = set()
        combined_interests = []

        for interest in incoming_interests + existing_interests:
            if not isinstance(interest, str):
                continue  # safety check
            interest_lower = interest.lower()
            if interest_lower not in seen_lower:
                seen_lower.add(interest_lower)
                combined_interests.append(interest)

        # Merge demographics and location (prefer new if present)
        demographics = user.get("demographics") or existing_user.get("demographics")
        location = user.get("location") or existing_user.get("location")

        update_fields = {
            "demographics": demographics,
            "location": location,
            "emails": list(updated_emails),
            "cookies": list(updated_cookies),
            "interests": combined_interests,
            "updated_at": datetime.now(),
        }
        # Add any other top-level fields from user that are not handled above
        for k, v in user.items():
            if k not in update_fields and k not in [
                "email",
                "cookie",
                "interests",
                "demographics",
                "location",
            ]:
                update_fields[k] = v

        update_query = {"$set": update_fields}
        update_in_mongo("user_profiles", {"user_id": user_id}, update_query)

    else:
        # New user creation
        user_id = str(uuid.uuid4())
        incoming_email = user.get("email")
        incoming_cookie = user.get("cookie")
        incoming_interests = user.get("interests", []) or []

        # Deduplicate interests in case new user sends duplicates
        seen_lower = set()
        unique_interests = []
        for interest in incoming_interests:
            if not isinstance(interest, str):
                continue
            interest_lower = interest.lower()
            if interest_lower not in seen_lower:
                seen_lower.add(interest_lower)
                unique_interests.append(interest)

        new_user = {
            "user_id": user_id,
            "emails": [incoming_email] if incoming_email else [],
            "cookies": [incoming_cookie] if incoming_cookie else [],
            "interests": unique_interests,
            "cohorts": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        # Add demographics and location if present
        if user.get("demographics"):
            new_user["demographics"] = user["demographics"]
        if user.get("location"):
            new_user["location"] = user["location"]
        # Add any other top-level fields from user that are not handled above
        for k, v in user.items():
            if k not in new_user and k not in [
                "email",
                "cookie",
                "interests",
                "demographics",
                "location",
            ]:
                new_user[k] = v

        insert_into_mongo("user_profiles", new_user)

    # Perform segmentation
    await perform_segmentation(user_id)
