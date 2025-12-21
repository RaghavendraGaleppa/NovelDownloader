"""
LLM-as-Judge for Reference-Based Translation Evaluation.

This module implements a "triangulated" evaluation where the Judge LLM
compares: Source (Chinese) + Candidate (LLM) + Reference (Human)
"""

import json
import time
import requests
from typing import Optional, Tuple
from rich.console import Console

from src.evaluation.models import ReferenceBasedScore

console = Console()


# Judge System Prompt - Emphasizes reference comparison
JUDGE_SYSTEM_PROMPT = """You are a Senior Editor at a translation publishing house.
You are evaluating a Machine Translation (Candidate) against a verified Human Translation (Reference).

Your Task:
1. Compare the Candidate against the Reference.
2. The Human Reference is considered 100% correct in meaning and tone.
3. If the Candidate diverges from the Reference in meaning, penalize it heavily.
4. If the Candidate diverges in wording but keeps the exact meaning (synonyms), that is acceptable.
5. If the Candidate misses a specific term (e.g., "Flying Sword" vs "Gliding Blade") that is consistent in the Reference, penalize it.

Scoring Rubric (Reference Alignment):
- 10: Captures 100% of the Reference's nuance. Distinctive style is identical.
- 8: Meaning is perfect, but style/tone is slightly flatter than the Reference.
- 5: Missed key details that the Human captured.
- 1: Completely different meaning from the Reference.

Scoring Rubric (Fluency):
- 10: Reads like a native English novel. Smooth and engaging.
- 8: Good flow, minor awkward phrasing.
- 5: Noticeable "Chinglish" or unnatural constructions.
- 1: Barely readable, broken English.

You MUST respond with ONLY a valid JSON object matching this exact schema:
{
    "comparison_analysis": "<detailed analysis of how the Candidate differs from the Human Reference>",
    "reference_alignment": <1-10>,
    "fluency": <1-10>,
    "critical_errors": ["<error1>", "<error2>", ...],
    "better_than_human": <true/false>
}

Do not include any text before or after the JSON object."""


def _build_evaluation_prompt(source_text: str, candidate_text: str, reference_text: str) -> str:
    """Build the user prompt for the judge."""
    return f"""Evaluate this translation:

=== ORIGINAL CHINESE ===
{source_text}

=== HUMAN REFERENCE (Ground Truth) ===
{reference_text}

=== AI CANDIDATE (To Evaluate) ===
{candidate_text}

Return your evaluation as a JSON object."""


def _parse_judge_response(response_text: str) -> Optional[ReferenceBasedScore]:
    """Parse the judge's JSON response into a ReferenceBasedScore."""
    try:
        # Try to extract JSON from the response
        # Handle cases where model might include markdown code blocks
        text = response_text.strip()
        
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        data = json.loads(text)
        return ReferenceBasedScore(**data)
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"  ⚠️  Failed to parse judge response: {e}", style="yellow")
        console.print(f"  Raw response: {response_text[:500]}...", style="dim")
        return None


def evaluate_translation(
    source_text: str,
    candidate_text: str,
    reference_text: str,
    judge_key_info: dict
) -> Tuple[Optional[ReferenceBasedScore], float]:
    """
    Evaluate a candidate translation against the human reference.
    
    Args:
        source_text: Original Chinese text
        candidate_text: LLM-generated translation to evaluate
        reference_text: Human-translated ground truth
        judge_key_info: API key info dict for the judge model
        
    Returns:
        Tuple of (ReferenceBasedScore or None, time_taken_seconds)
    """
    from src.translation.openrouter import api_providers
    
    provider_name = judge_key_info.get("provider")
    api_key = judge_key_info.get("key")
    key_name = judge_key_info.get("name", f"Judge: {provider_name}")
    
    if not provider_name or not api_key:
        console.print("  ❌ Invalid judge key info", style="red")
        return None, 0
    
    if provider_name not in api_providers:
        console.print(f"  ❌ Unknown judge provider: {provider_name}", style="red")
        return None, 0
    
    provider_config = api_providers[provider_name]
    api_url = provider_config["url"]
    model_name = provider_config["model_names"][0]  # Use first model
    
    console.print(f"  🔍 Evaluating with {key_name} ({model_name})", style="dim")
    
    start_time = time.time()
    
    # Build the prompt
    user_prompt = _build_evaluation_prompt(source_text, candidate_text, reference_text)
    
    try:
        if provider_name == "google":
            # Google Gemini API format
            headers = {"X-goog-api-key": api_key, "Content-Type": "application/json"}
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": JUDGE_SYSTEM_PROMPT + "\n\n" + user_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
                ]
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=5*60)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data and response_data.get("candidates"):
                response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                console.print("  ❌ No response from Google API", style="red")
                return None, time.time() - start_time
        
        else:
            # OpenAI-compatible APIs
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            
            messages = [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.1,  # Low temperature for consistent evaluation
                "max_tokens": 4096
            }
            
            # Add JSON mode for supported providers
            if provider_name in ["openrouter", "groq"]:
                payload["response_format"] = {"type": "json_object"}
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=5*60)
            response.raise_for_status()
            response_data = response.json()
            
            if response_data and response_data.get("choices"):
                response_text = response_data["choices"][0]["message"]["content"]
            else:
                console.print("  ❌ No response from API", style="red")
                return None, time.time() - start_time
        
        elapsed = time.time() - start_time
        
        # Parse the response
        score = _parse_judge_response(response_text)
        
        if score:
            console.print(f"  ✅ Evaluation complete (alignment: {score.reference_alignment}, fluency: {score.fluency})", style="green")
        
        return score, elapsed
        
    except requests.exceptions.HTTPError as e:
        console.print(f"  ❌ HTTP Error: {e}", style="red")
        return None, time.time() - start_time
    except Exception as e:
        console.print(f"  ❌ Error during evaluation: {e}", style="red")
        return None, time.time() - start_time


def quick_bert_check(candidate: str, reference: str) -> Optional[float]:
    """
    Quick sanity check using BERTScore.
    
    Returns a 0-1 similarity score, or None if BERTScore is not available.
    If score < 0.7, the translation is likely garbage.
    """
    try:
        from bert_score import score as bert_score
        
        console.print("  📊 Running BERTScore sanity check...", style="dim")
        
        # Calculate BERTScore
        P, R, F1 = bert_score([candidate], [reference], lang="en", verbose=False)
        f1_score = F1.mean().item()
        
        console.print(f"  BERTScore F1: {f1_score:.3f}", style="dim")
        
        return f1_score
        
    except ImportError:
        # BERTScore not installed, skip
        return None
    except Exception as e:
        console.print(f"  ⚠️  BERTScore failed: {e}", style="yellow")
        return None
