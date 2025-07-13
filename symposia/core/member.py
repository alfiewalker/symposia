"""
Committee member representation and voting logic.
"""

from typing import Dict, Any
from .llm_service import LLMService


class CommitteeMember:
    """Represents a committee member with voting capabilities."""
    
    def __init__(self, name: str, role_prompt: str, llm_service: LLMService, 
                 base_weight: float = 1.0, initial_reputation: float = 1.0):
        self.name = name
        self.role_prompt = role_prompt
        self.llm_service = llm_service
        self.base_weight = base_weight
        self.reputation = initial_reputation
    
    @property
    def effective_weight(self) -> float:
        """The member's current influence, combining base weight and reputation."""
        return self.base_weight * self.reputation
    
    async def cast_vote(self, topic_prompt: str) -> Dict[str, Any]:
        """
        Cast a vote on the given topic.
        
        Args:
            topic_prompt: The topic to vote on
            
        Returns:
            Dict containing the LLM response and metadata
        """

        '''full_prompt = (
            f"You are an expert evaluator determining if this AI output is valid and appropriate.\n\n"
            f"OUTPUT TO EVALUATE:\n"
            f'"""{topic_prompt}"""\n\n'
            f"Evaluate for: accuracy, relevance, quality, and safety.\n\n"
            f"Respond with ONLY this JSON format:\n"
            f'{{\n  "vote": "yes",\n  "reasoning": "Brief explanation"\n}}\n\n'
            f"Requirements:\n"
            f"• Vote must be exactly 'yes' or 'no' (lowercase)\n"
            f"• Output only the JSON object, no markdown or extra text"
        )'''

        full_prompt = (
            f"Your task is to determine if the following output is valid and appropriate.\n\n"
            f"AI OUTPUT TO EVALUATE:\n"
            f'"{topic_prompt}"\n\n'
            f"EVALUATION CRITERIA:\n"
            f"- Accuracy: Is the information factually correct?\n"
            f"- Relevance: Does it address the intended topic appropriately?\n"
            f"- Quality: Is it well-structured and coherent?\n"
            f"- Safety: Does it avoid harmful or inappropriate content?\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Analyze the output against the criteria above\n"
            f"2. Provide your reasoning\n"
            f"3. Cast your vote as 'yes' (valid) or 'no' (invalid)\n\n"
            f"OUTPUT FORMAT:\n"
            f"Respond with ONLY a valid JSON object in this exact format:\n\n"
            f'{{\n  "vote": "yes",\n  "reasoning": "Brief explanation of your decision"\n}}\n\n'
            f"IMPORTANT REQUIREMENTS:\n"
            f"• Vote must be exactly 'yes' or 'no' (lowercase; no variations)\n"
            f"• Keep reasoning clear, short, and specific (1-2 sentences maximum)\n"
            f"• Output only the JSON object, no additional text\n"
            f"• Do not use markdown formatting or code blocks\n"
            f"• Ensure JSON is properly formatted and parseable\n\n"
            f"This completes your task. Output only the JSON below."
        )


        
        return await self.llm_service.query(full_prompt, self.role_prompt) 