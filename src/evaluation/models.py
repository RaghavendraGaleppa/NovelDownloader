"""
Pydantic models for Reference-Based Translation Evaluation.

This module defines the data structures for scoring LLM translations
against human reference translations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ReferenceBasedScore(BaseModel):
    """
    Score for a single translation evaluated against human reference.
    
    The Judge LLM compares the AI Candidate against the Human Reference,
    treating the Human Reference as the "Ground Truth" for style and accuracy.
    """
    
    # Comparison Logic
    comparison_analysis: str = Field(
        ..., 
        description="Analyze how the Candidate differs from the Human Reference. Note missing nuances or shifts in tone."
    )
    
    # Specific Scores
    reference_alignment: int = Field(
        ..., 
        ge=1, 
        le=10, 
        description="1-10: How closely does it match the human's meaning and terminology?"
    )
    
    fluency: int = Field(
        ..., 
        ge=1, 
        le=10, 
        description="1-10: Is the English natural? (Independent of reference)"
    )
    
    critical_errors: List[str] = Field(
        ..., 
        description="List of major deviations from the Human Reference (e.g., wrong numbers, missing names)."
    )
    
    better_than_human: bool = Field(
        ..., 
        description="Rare case: Is the AI translation actually better/smoother than the human reference?"
    )
    
    @property
    def final_score(self) -> float:
        """
        Calculate weighted final score.
        Heavily weights alignment with the human expert.
        """
        return (self.reference_alignment * 0.6) + (self.fluency * 0.4)


class EvaluationResult(BaseModel):
    """Result for a single chapter evaluation."""
    
    chapter_name: str = Field(..., description="Name of the test chapter file")
    translation_provider: str = Field(..., description="Provider that produced the translation")
    
    # Texts
    source_text: str = Field(..., description="Original Chinese text")
    human_reference: str = Field(..., description="Human-translated ground truth")
    candidate_translation: str = Field(..., description="LLM-generated translation")
    
    # Pre-check score (BERTScore)
    bert_score: Optional[float] = Field(None, description="BERTScore F1 (0-1) for quick sanity check")
    
    # LLM Judge score
    score: Optional[ReferenceBasedScore] = Field(None, description="Detailed score from LLM Judge")
    
    # Metadata
    translation_time_seconds: Optional[float] = None
    evaluation_time_seconds: Optional[float] = None
    error: Optional[str] = Field(None, description="Error message if evaluation failed")
    
    @property
    def final_score(self) -> Optional[float]:
        """Get the weighted final score if available."""
        if self.score:
            return self.score.final_score
        return None


class ProviderSummary(BaseModel):
    """Aggregated summary for a single translation provider."""
    
    provider_name: str
    chapters_evaluated: int
    
    # Average scores
    avg_reference_alignment: float
    avg_fluency: float
    avg_final_score: float
    
    # BERTScore stats
    avg_bert_score: Optional[float] = None
    
    # Counts
    better_than_human_count: int = 0
    failure_count: int = 0
    
    # Critical errors across all chapters
    all_critical_errors: List[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """Full evaluation report comparing multiple providers."""
    
    report_name: str = Field(default="Translation Quality Evaluation")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Configuration
    test_data_dir: str
    judge_provider: str
    translation_providers: List[str]
    
    # All individual results
    results: List[EvaluationResult] = Field(default_factory=list)
    
    # Summaries per provider
    provider_summaries: List[ProviderSummary] = Field(default_factory=list)
    
    def add_result(self, result: EvaluationResult):
        """Add an evaluation result to the report."""
        self.results.append(result)
    
    def compute_summaries(self):
        """Compute provider summaries from individual results."""
        from collections import defaultdict
        
        # Group results by provider
        by_provider = defaultdict(list)
        for result in self.results:
            by_provider[result.translation_provider].append(result)
        
        self.provider_summaries = []
        
        for provider, results in by_provider.items():
            valid_results = [r for r in results if r.score is not None]
            
            if not valid_results:
                self.provider_summaries.append(ProviderSummary(
                    provider_name=provider,
                    chapters_evaluated=len(results),
                    avg_reference_alignment=0,
                    avg_fluency=0,
                    avg_final_score=0,
                    failure_count=len(results)
                ))
                continue
            
            # Calculate averages
            avg_alignment = sum(r.score.reference_alignment for r in valid_results) / len(valid_results)
            avg_fluency = sum(r.score.fluency for r in valid_results) / len(valid_results)
            avg_final = sum(r.final_score for r in valid_results) / len(valid_results)
            
            # BERTScore average
            bert_scores = [r.bert_score for r in valid_results if r.bert_score is not None]
            avg_bert = sum(bert_scores) / len(bert_scores) if bert_scores else None
            
            # Counts
            better_count = sum(1 for r in valid_results if r.score.better_than_human)
            
            # Collect all critical errors
            all_errors = []
            for r in valid_results:
                all_errors.extend(r.score.critical_errors)
            
            self.provider_summaries.append(ProviderSummary(
                provider_name=provider,
                chapters_evaluated=len(results),
                avg_reference_alignment=round(avg_alignment, 2),
                avg_fluency=round(avg_fluency, 2),
                avg_final_score=round(avg_final, 2),
                avg_bert_score=round(avg_bert, 3) if avg_bert else None,
                better_than_human_count=better_count,
                failure_count=len(results) - len(valid_results),
                all_critical_errors=all_errors[:20]  # Limit to top 20
            ))
        
        # Sort by final score descending
        self.provider_summaries.sort(key=lambda x: x.avg_final_score, reverse=True)
