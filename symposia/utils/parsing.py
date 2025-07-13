"""
Utilities for parsing LLM responses.
"""

import json
from typing import Any, Dict

def parse_llm_json_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the LLM's response assuming it returns a well-formed JSON object.

    This function is designed for optimistic parsing — where the LLM is instructed 
    to respond with *only* a valid JSON object and no additional prose, markdown, or formatting.

    Best practices when using this parser:
    - Ensure your prompt clearly instructs the model to respond **only** with JSON.
    - Avoid markdown formatting (e.g., triple backticks or ```json blocks).
    - Use `.strip()` to remove leading/trailing whitespace.

    Args:
        response_text (str): Raw response text from the LLM.

    Returns:
        Dict[str, Any]: Parsed JSON dictionary. If parsing fails, returns a dictionary
                        with an `"error"` key and optionally includes the raw response for inspection.
    """
    try:
        # Strip to remove whitespace/newlines that could break parsing
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to decode JSON: {str(e)}",
            "raw": response_text
        }

