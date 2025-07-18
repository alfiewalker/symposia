"""
Deliberation result representation and tracing.
"""

from typing import List, Dict, Any

class DeliberationResult:
    """Represents the result of a committee deliberation with full traceability."""
    
    def __init__(self, topic: str, strategy_used: str, final_result: Any, 
                 trace: List[Dict[str, Any]], total_tokens: int, total_cost: float):
        self.topic = topic
        self.strategy_used = strategy_used
        self.final_result = final_result
        self.trace = trace
        self.total_tokens = total_tokens
        self.total_cost = total_cost
    
    def display_trace(self) -> None:
        """Display a detailed trace of the deliberation process."""
        report = [
            "\n" + "="*25 + " Deliberation Traceability Report " + "="*25,
            f"Topic: {self.topic}",
            f"Voting Strategy: {self.strategy_used}",
            "-" * 80
        ]
        
        for i, step in enumerate(self.trace):
            report.extend([
                f"Step {i+1}: Member '{step['member_name']}' "
                f"(Rep: {step['reputation']:.2f}, Eff. W: {step['effective_weight']:.2f})",
                f"  - LLM Service: {step['llm_service']}",
                f"  - Raw LLM Opinion: \"{step['raw_opinion']}\"",
                f"  - Parsed Vote Data: {step['parsed_vote']}",
                f"  - Status: {step['status']}",
                f"  - Cost: ${step['cost']:.6f} | Tokens: {step['tokens_used']}",
                "-" * 80
            ])
        
        report.extend([
            f"Final Aggregated Result: {self.final_result}",
            f"Total Cost: ${self.total_cost:.6f} | Total Tokens: {self.total_tokens}",
            "=" * 80
        ])
        
        print("\n".join(report)) 