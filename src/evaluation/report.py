"""
Report Generation - Create evaluation reports in various formats.

This module generates markdown and JSON reports from evaluation results.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table

from src.evaluation.models import EvaluationReport

console = Console()


def generate_markdown_report(report: EvaluationReport) -> str:
    """Generate a markdown summary report."""
    lines = [
        f"# Translation Quality Evaluation Report",
        f"",
        f"**Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Configuration",
        f"",
        f"- **Test Data:** `{report.test_data_dir}`",
        f"- **Judge Provider:** {report.judge_provider}",
        f"- **Translation Providers:** {', '.join(report.translation_providers)}",
        f"- **Total Evaluations:** {len(report.results)}",
        f"",
        f"---",
        f"",
        f"## Provider Rankings",
        f"",
        f"| Rank | Provider | Final Score | Alignment | Fluency | Better Count | Failures |",
        f"|------|----------|-------------|-----------|---------|--------------|----------|",
    ]
    
    for i, summary in enumerate(report.provider_summaries, 1):
        lines.append(
            f"| {i} | **{summary.provider_name}** | "
            f"{summary.avg_final_score:.2f} | "
            f"{summary.avg_reference_alignment:.1f} | "
            f"{summary.avg_fluency:.1f} | "
            f"{summary.better_than_human_count} | "
            f"{summary.failure_count} |"
        )
    
    lines.extend([
        f"",
        f"---",
        f"",
        f"## Detailed Results by Chapter",
        f"",
    ])
    
    # Group by chapter
    chapters = {}
    for result in report.results:
        if result.chapter_name not in chapters:
            chapters[result.chapter_name] = []
        chapters[result.chapter_name].append(result)
    
    for chapter_name, results in chapters.items():
        lines.extend([
            f"### {chapter_name}",
            f"",
        ])
        
        for result in results:
            score_str = "N/A"
            if result.score:
                score_str = f"{result.score.final_score:.2f}"
            
            lines.append(f"- **{result.translation_provider}**: {score_str}")
            
            if result.score:
                lines.append(f"  - Alignment: {result.score.reference_alignment}, Fluency: {result.score.fluency}")
                if result.score.better_than_human:
                    lines.append(f"  - 🌟 _Better than human reference_")
                if result.score.critical_errors:
                    lines.append(f"  - Critical Errors: {', '.join(result.score.critical_errors[:3])}")
            
            if result.error:
                lines.append(f"  - ❌ Error: {result.error}")
        
        lines.append("")
    
    # Critical errors summary
    lines.extend([
        f"---",
        f"",
        f"## Common Critical Errors",
        f"",
    ])
    
    for summary in report.provider_summaries:
        if summary.all_critical_errors:
            lines.extend([
                f"### {summary.provider_name}",
                f"",
            ])
            for error in summary.all_critical_errors[:10]:
                lines.append(f"- {error}")
            lines.append("")
    
    return "\n".join(lines)


def generate_json_report(report: EvaluationReport) -> str:
    """Generate a JSON report with all details."""
    return report.model_dump_json(indent=2)


def save_report(report: EvaluationReport, output_dir: str):
    """Save reports to the output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save markdown report
    md_file = output_path / f"evaluation_report_{timestamp}.md"
    md_content = generate_markdown_report(report)
    md_file.write_text(md_content, encoding='utf-8')
    console.print(f"📄 Saved: {md_file}", style="green")
    
    # Save JSON report
    json_file = output_path / f"evaluation_report_{timestamp}.json"
    json_content = generate_json_report(report)
    json_file.write_text(json_content, encoding='utf-8')
    console.print(f"📄 Saved: {json_file}", style="green")
    
    return md_file, json_file


def print_summary(report: EvaluationReport):
    """Print a summary table to the console."""
    table = Table(title="Evaluation Summary")
    
    table.add_column("Provider", style="cyan")
    table.add_column("Final Score", justify="right", style="bold")
    table.add_column("Alignment", justify="right")
    table.add_column("Fluency", justify="right")
    table.add_column("Better", justify="right", style="yellow")
    table.add_column("Failed", justify="right", style="red")
    
    for summary in report.provider_summaries:
        table.add_row(
            summary.provider_name,
            f"{summary.avg_final_score:.2f}",
            f"{summary.avg_reference_alignment:.1f}",
            f"{summary.avg_fluency:.1f}",
            str(summary.better_than_human_count),
            str(summary.failure_count)
        )
    
    console.print(table)
