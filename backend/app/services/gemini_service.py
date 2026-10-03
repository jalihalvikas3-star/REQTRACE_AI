import os

from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=api_key
)


# =========================================================
# GEMINI RESPONSE
# =========================================================

def generate_response(prompt):

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        if not response or not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text

    except Exception as e:

        error_message = str(e)

        # ---------------------------------------------
        # Quota / rate limit
        # ---------------------------------------------

        if (
            "QuotaFailure" in error_message
            or "quota" in error_message.lower()
            or "rate limit" in error_message.lower()
            or "429" in error_message
        ):

            raise RuntimeError(
                "Gemini API quota/rate limit exceeded. "
                "Use the configured fallback."
            ) from e

        # ---------------------------------------------
        # Other Gemini errors
        # ---------------------------------------------

        raise RuntimeError(
            f"Gemini API request failed: {error_message}"
        ) from e