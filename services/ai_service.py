import json
from utils import segmentation_prompt
import re
import ast
from openai import OpenAI
import os


def clean_response(response_str):
    """
    Cleans a model response string by removing markdown/code block artifacts.

    Specifically removes:
    - Triple backticks and optional language identifiers (e.g., ```python)
    - Leading/trailing whitespace and newlines

    Args:
        response_str (str): The raw response string from the model.

    Returns:
        object: The parsed Python object if it's a valid literal (like dict, list, or quoted string),
                otherwise returns the cleaned string as-is.
    """
    cleaned = re.sub(
        r"^```(?:python|json)?\s*|\s*```$",
        "",
        response_str.strip(),
        flags=re.IGNORECASE | re.MULTILINE,
    ).strip()

    try:
        # Try parsing it as a Python literal
        return ast.literal_eval(cleaned)
    except (ValueError, SyntaxError):
        # If it's not a valid Python literal, return as plain string
        return cleaned


def ai_call(system_prompt: str, user_prompt: str) -> str:
    """
    Calls the OpenAI chat completion API with the given system and user prompts.

    Args:
        system_prompt (str): The system prompt to set the assistant's behavior.
        user_prompt (str): The user's input prompt.

    Returns:
        str: The cleaned response from the model.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=500,
    )

    reply = response.choices[0].message.content.strip()

    return clean_response(reply)


def get_cohorts_from_interests(user_id, user_interests) -> list:
    """
    Assigns user interests to cohorts using the OpenAI GPT-4o model.

    Args:
        user_id (str or int): The unique identifier for the user.
        user_interests (list): List of user interests (strings).

    Returns:
        list: List of dictionaries, each with keys 'cohort' and 'score'.
              Returns an empty list if the correct structure is not obtained after 5 attempts.
    """
    user_prompt = segmentation_prompt.user_prompt.format(interests=user_interests)
    for _ in range(5):
        segments = ai_call(segmentation_prompt.system_prompt, user_prompt)
        # Check if segments is a list of dicts with 'cohort' and 'score' keys
        if isinstance(segments, list) and all(
            isinstance(item, dict) and "cohort" in item and "similarity_score" in item
            for item in segments
        ):
            unique_cohorts = set()
            unique_segments = []
            for item in segments:
                cohort = item["cohort"]
                if cohort not in unique_cohorts:
                    unique_cohorts.add(cohort)
                    unique_segments.append(item)
            return unique_segments
    print(f"Having issue in cohorts for user id: {user_id}")
    return []


# ---------- Example Usage ----------
if __name__ == "__main__":
    interests = ["hiking", "camping", "backpacking", "kayaking"]
    cohorts = ["Outdoor Adventurers", "Tech Enthusiasts", "Foodies", "Fitness Buffs"]

    output = get_cohorts_from_interests(interests, cohorts)
    print(json.dumps(output, indent=2))
