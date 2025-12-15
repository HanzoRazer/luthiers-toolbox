"""
RMOS Migration Report Generator (N8.7)

Generates detailed migration reports in JSON, HTML, and PDF formats.
Analyzes migration results and produces human-readable summaries.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RMOSMigrationReport:
    """
    Generates migration reports in multiple formats.
    
    Transforms raw migration statistics into formatted reports
    with timestamps, entity details, and validation summaries.
    """
    
    def __init__(self, stats: Dict[str, Any], output_dir: Optional[Path] = None):
        """
        Initialize report generator.
        
        Args:
            stats: Migration statistics from run_migration()
            output_dir: Directory to save reports (default: ./migration_reports)
        """
        self.stats = stats
        self.output_dir = output_dir or Path("./migration_reports")
        self.timestamp = datetime.now().isoformat()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all(self) -> Dict[str, Path]:
        """
        Generate all report formats.
        
        Returns:
            Dictionary mapping format names to file paths
            
        Example:
            reporter = RMOSMigrationReport(stats)
            files = reporter.generate_all()
            print(f"JSON report: {files['json']}")
        """
        reports = {}
        
        reports['json'] = self.generate_json()
        reports['html'] = self.generate_html()
        reports['txt'] = self.generate_text()
        
        logger.info(f"Generated {len(reports)} reports in {self.output_dir}")
        return reports
    
    def generate_json(self) -> Path:
        """Generate JSON report with full statistics."""
        timestamp_safe = self.timestamp.replace(':', '-').replace('.', '-')
        filename = f"migration_report_{timestamp_safe}.json"
        filepath = self.output_dir / filename
        
        report = {
            'timestamp': self.timestamp,
            'summary': self._calculate_summary(),
            'entities': self.stats,
            'success': self._is_successful()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"JSON report saved to {filepath}")
        return filepath
    
    def generate_html(self) -> Path:
        """Generate HTML report with visual formatting."""
        timestamp_safe = self.timestamp.replace(':', '-').replace('.', '-')
        filename = f"migration_report_{timestamp_safe}.html"
        filepath = self.output_dir / filename
        
        summary = self._calculate_summary()
        success = self._is_successful()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RMOS Migration Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: {'#28a745' if success else '#dc3545'};
            border-bottom: 3px solid {'#28a745' if success else '#dc3545'};
            padding-bottom: 10px;
        }}
        .summary {{
            background: #e9ecef;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #ccc;
        }}
        .summary-item:last-child {{
            border-bottom: none;
        }}
        .entity-section {{
            margin: 30px 0;
        }}
        .entity-title {{
            font-size: 1.3em;
            color: #495057;
            margin-bottom: 15px;
            border-left: 4px solid #007bff;
            padding-left: 10px;
        }}
        .entity-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #007bff;
        }}
        .stat-label {{
            font-weight: bold;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .stat-value {{
            font-size: 1.8em;
            color: #212529;
            margin-top: 5px;
        }}
        .success {{
            color: #28a745;
        }}
        .warning {{
            color: #ffc107;
        }}
        .danger {{
            color: #dc3545;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
            text-align: right;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RMOS Migration Report</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-item">
                <span>Total Found:</span>
                <span class="stat-value">{summary['total_found']}</span>
            </div>
            <div class="summary-item">
                <span>Total Migrated:</span>
                <span class="stat-value success">{summary['total_migrated']}</span>
            </div>
            <div class="summary-item">
                <span>Total Skipped:</span>
                <span class="stat-value warning">{summary['total_skipped']}</span>
            </div>
            <div class="summary-item">
                <span>Total Failed:</span>
                <span class="stat-value {'success' if summary['total_failed'] == 0 else 'danger'}">{summary['total_failed']}</span>
            </div>
            <div class="summary-item">
                <span>Success Rate:</span>
                <span class="stat-value {'success' if summary['success_rate'] >= 95 else 'warning'}">{summary['success_rate']:.1f}%</span>
            </div>
        </div>
"""
        
        # Add entity sections
        for entity_type, counts in self.stats.items():
            html += f"""
        <div class="entity-section">
            <div class="entity-title">{entity_type.replace('_', ' ').title()}</div>
            <div class="entity-stats">
                <div class="stat-card">
                    <div class="stat-label">Found</div>
                    <div class="stat-value">{counts['found']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Migrated</div>
                    <div class="stat-value success">{counts['migrated']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Skipped</div>
                    <div class="stat-value warning">{counts['skipped']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value {'success' if counts['failed'] == 0 else 'danger'}">{counts['failed']}</div>
                </div>
            </div>
        </div>
"""
        
        html += f"""
        <div class="timestamp">Generated: {self.timestamp}</div>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        logger.info(f"HTML report saved to {filepath}")
        return filepath
    
    def generate_text(self) -> Path:
        """Generate plain text report for console/logs."""
        timestamp_safe = self.timestamp.replace(':', '-').replace('.', '-')
        filename = f"migration_report_{timestamp_safe}.txt"
        filepath = self.output_dir / filename
        
        summary = self._calculate_summary()
        success = self._is_successful()
        
        lines = [
            "=" * 60,
            "RMOS MIGRATION REPORT",
            "=" * 60,
            f"Timestamp: {self.timestamp}",
            f"Status: {'SUCCESS' if success else 'FAILED'}",
            "",
            "SUMMARY:",
            "-" * 60,
            f"Total Found:     {summary['total_found']}",
            f"Total Migrated:  {summary['total_migrated']}",
            f"Total Skipped:   {summary['total_skipped']}",
            f"Total Failed:    {summary['total_failed']}",
            f"Success Rate:    {summary['success_rate']:.1f}%",
            "",
        ]
        
        for entity_type, counts in self.stats.items():
            lines.extend([
                f"{entity_type.upper()}:",
                "-" * 60,
                f"  Found:     {counts['found']}",
                f"  Migrated:  {counts['migrated']}",
                f"  Skipped:   {counts['skipped']}",
                f"  Failed:    {counts['failed']}",
                "",
            ])
        
        lines.append("=" * 60)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Text report saved to {filepath}")
        return filepath
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        total_found = sum(c['found'] for c in self.stats.values())
        total_migrated = sum(c['migrated'] for c in self.stats.values())
        total_skipped = sum(c['skipped'] for c in self.stats.values())
        total_failed = sum(c['failed'] for c in self.stats.values())
        
        success_rate = (total_migrated / total_found * 100) if total_found > 0 else 0
        
        return {
            'total_found': total_found,
            'total_migrated': total_migrated,
            'total_skipped': total_skipped,
            'total_failed': total_failed,
            'success_rate': success_rate
        }
    
    def _is_successful(self) -> bool:
        """Determine if migration was successful (no failures)."""
        return all(c['failed'] == 0 for c in self.stats.values())


def generate_reports(stats: Dict[str, Any], output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Generate migration reports in all formats.
    
    Args:
        stats: Migration statistics from run_migration()
        output_dir: Directory to save reports
        
    Returns:
        Dictionary mapping format names to file paths
        
    Example:
        stats = run_migration()
        files = generate_reports(stats)
        print(f"HTML: {files['html']}")
        print(f"JSON: {files['json']}")
    """
    reporter = RMOSMigrationReport(stats, output_dir)
    return reporter.generate_all()


if __name__ == "__main__":
    import sys
    
    # Command-line usage: python rmos_migration_report.py <stats_json_file>
    if len(sys.argv) < 2:
        print("Usage: python rmos_migration_report.py <stats_json_file>")
        sys.exit(1)
    
    stats_file = Path(sys.argv[1])
    if not stats_file.exists():
        print(f"Error: Stats file not found: {stats_file}")
        sys.exit(1)
    
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    files = generate_reports(stats)
    
    print("\n=== Reports Generated ===")
    for format_name, filepath in files.items():
        print(f"{format_name.upper()}: {filepath}")
