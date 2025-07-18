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
        text_to_parse = response_text.strip()
        
        # Check for markdown code blocks (```json ... ```) and extract content if present
        if text_to_parse.startswith("```") and "```" in text_to_parse[3:]:
            # Find the end of the code block
            start_pos = text_to_parse.find("{")
            end_pos = text_to_parse.rfind("}")
            
            if start_pos >= 0 and end_pos >= 0:
                # Extract just the JSON content
                text_to_parse = text_to_parse[start_pos:end_pos+1]
        
        # Try to parse the JSON
        return json.loads(text_to_parse)
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to decode JSON: {str(e)}",
            "raw": response_text
        }

