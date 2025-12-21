"""
Evaluation Runner - Orchestrates translation and evaluation.

This module loads test data, runs translations through specified providers,
and evaluates them against human references using the LLM Judge.
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.evaluation.models import EvaluationResult, EvaluationReport
from src.evaluation.judge import evaluate_translation, quick_bert_check
from src.translation.openrouter import translate_chinese_to_english, LOADED_API_KEYS

console = Console()


def load_test_data(test_data_dir: str) -> List[dict]:
    """
    Load test data from the test_data directory.
    
    Expected structure:
        test_data/
        ├── raws/
        │   ├── chapter_001.txt
        │   └── chapter_002.txt
        └── translated/
            ├── chapter_001.txt
            └── chapter_002.txt
    
    Returns:
        List of dicts with 'name', 'source', 'reference' keys
    """
    raws_dir = Path(test_data_dir) / "raws"
    translated_dir = Path(test_data_dir) / "translated"
    
    if not raws_dir.exists():
        console.print(f"❌ Raws directory not found: {raws_dir}", style="red")
        return []
    
    if not translated_dir.exists():
        console.print(f"❌ Translated directory not found: {translated_dir}", style="red")
        return []
    
    test_data = []
    
    # Find all raw files
    for raw_file in sorted(raws_dir.glob("*.txt")):
        name = raw_file.stem
        ref_file = translated_dir / f"{name}.txt"
        
        if not ref_file.exists():
            console.print(f"  ⚠️  Missing reference for {name}, skipping", style="yellow")
            continue
        
        try:
            source_text = raw_file.read_text(encoding='utf-8').strip()
            reference_text = ref_file.read_text(encoding='utf-8').strip()
            
            if source_text and reference_text:
                test_data.append({
                    'name': name,
                    'source': source_text,
                    'reference': reference_text
                })
                console.print(f"  ✅ Loaded: {name} ({len(source_text)} chars)", style="dim")
        except Exception as e:
            console.print(f"  ❌ Error loading {name}: {e}", style="red")
    
    return test_data


def get_provider_key(provider_name: str) -> Optional[dict]:
    """Get the API key info for a specific provider."""
    for key_info in LOADED_API_KEYS:
        if key_info.get("provider") == provider_name:
            return key_info
    return None


def translate_with_provider(text: str, provider_name: str) -> tuple[str, float]:
    """
    Translate text using a specific provider.
    
    Returns:
        Tuple of (translated_text, time_taken_seconds)
    """
    key_info = get_provider_key(provider_name)
    
    if not key_info:
        return f"Error: No key found for provider {provider_name}", 0
    
    start_time = time.time()
    translated, _ = translate_chinese_to_english(text, key_override=key_info)
    elapsed = time.time() - start_time
    
    return translated, elapsed


def run_evaluation(
    test_data_dir: str,
    translation_providers: List[str],
    judge_provider: str,
    use_bert_precheck: bool = True
) -> EvaluationReport:
    """
    Run full evaluation on test data.
    
    Args:
        test_data_dir: Path to test_data directory
        translation_providers: List of provider names to test
        judge_provider: Provider to use as the judge
        use_bert_precheck: Whether to run BERTScore sanity check
        
    Returns:
        EvaluationReport with all results
    """
    console.print(f"\n{'='*60}", style="bold cyan")
    console.print("📊 Translation Quality Evaluation", style="bold cyan")
    console.print(f"{'='*60}\n", style="bold cyan")
    
    # Load test data
    console.print("📂 Loading test data...", style="bold")
    test_data = load_test_data(test_data_dir)
    
    if not test_data:
        console.print("❌ No test data found!", style="red")
        return EvaluationReport(
            test_data_dir=test_data_dir,
            judge_provider=judge_provider,
            translation_providers=translation_providers
        )
    
    console.print(f"✅ Loaded {len(test_data)} test samples\n", style="green")
    
    # Get judge key
    judge_key = get_provider_key(judge_provider)
    if not judge_key:
        console.print(f"❌ No key found for judge provider: {judge_provider}", style="red")
        return EvaluationReport(
            test_data_dir=test_data_dir,
            judge_provider=judge_provider,
            translation_providers=translation_providers
        )
    
    # Create report
    report = EvaluationReport(
        test_data_dir=test_data_dir,
        judge_provider=judge_provider,
        translation_providers=translation_providers
    )
    
    # Process each test sample with each provider
    total_tasks = len(test_data) * len(translation_providers)
    current_task = 0
    
    for sample in test_data:
        console.print(f"\n📖 Sample: {sample['name']}", style="bold blue")
        console.print("-" * 40, style="blue")
        
        for provider in translation_providers:
            current_task += 1
            console.print(f"\n  [{current_task}/{total_tasks}] Provider: {provider}", style="bold")
            
            result = EvaluationResult(
                chapter_name=sample['name'],
                translation_provider=provider,
                source_text=sample['source'],
                human_reference=sample['reference'],
                candidate_translation=""
            )
            
            # Step 1: Translate
            console.print("  🔄 Translating...", style="cyan")
            translated, translate_time = translate_with_provider(sample['source'], provider)
            result.candidate_translation = translated
            result.translation_time_seconds = translate_time
            
            if translated.startswith("Error:"):
                console.print(f"  ❌ Translation failed: {translated[:100]}", style="red")
                result.error = translated
                report.add_result(result)
                continue
            
            console.print(f"  ✅ Translated ({translate_time:.1f}s)", style="green")
            
            # Step 2: BERTScore pre-check (optional)
            if use_bert_precheck:
                bert_f1 = quick_bert_check(translated, sample['reference'])
                result.bert_score = bert_f1
                
                if bert_f1 is not None and bert_f1 < 0.5:
                    console.print(f"  ⚠️  Low BERTScore ({bert_f1:.3f}) - translation may be poor", style="yellow")
            
            # Step 3: LLM Judge evaluation
            console.print("  🔍 Running LLM Judge evaluation...", style="cyan")
            score, eval_time = evaluate_translation(
                source_text=sample['source'],
                candidate_text=translated,
                reference_text=sample['reference'],
                judge_key_info=judge_key
            )
            
            result.score = score
            result.evaluation_time_seconds = eval_time
            
            if score:
                console.print(f"  📊 Final Score: {score.final_score:.2f} (align: {score.reference_alignment}, fluency: {score.fluency})", style="bold green")
                if score.better_than_human:
                    console.print("  🌟 Better than human!", style="bold yellow")
                if score.critical_errors:
                    console.print(f"  ⚠️  Critical errors: {len(score.critical_errors)}", style="yellow")
            else:
                result.error = "Judge evaluation failed"
            
            report.add_result(result)
    
    # Compute summaries
    report.compute_summaries()
    
    console.print(f"\n{'='*60}", style="bold green")
    console.print("✅ Evaluation Complete!", style="bold green")
    console.print(f"{'='*60}\n", style="bold green")
    
    return report
