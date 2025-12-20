"""
Job Analytics Engine (N9.0)

Analyzes job performance, success rates, duration trends, and throughput.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from ...stores.rmos_stores import get_rmos_stores

logger = logging.getLogger(__name__)


class JobAnalytics:
    """
    Analytics engine for manufacturing job logs.
    
    Provides:
    - Success rate trends over time
    - Duration analysis by job type
    - Status distribution
    - Throughput metrics (jobs per day/week)
    - Failure analysis
    """
    
    def __init__(self):
        """Initialize analytics engine with store access."""
        self.stores = get_rmos_stores()
    
    def get_success_rate_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate success rate trends over time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Daily success rates and overall trend
        """
        joblogs = self.stores.joblogs.get_all()
        
        # Group by date
        daily_stats = defaultdict(lambda: {"total": 0, "completed": 0, "failed": 0})
        
        for job in joblogs:
            created_at = job.get("created_at")
            if not created_at:
                continue
            
            try:
                # Extract date part
                date = created_at.split('T')[0]
                status = job.get("status")
                
                daily_stats[date]["total"] += 1
                if status == "completed":
                    daily_stats[date]["completed"] += 1
                elif status == "failed":
                    daily_stats[date]["failed"] += 1
            except Exception:
                continue
        
        # Convert to sorted list with success rates
        trends = []
        for date, stats in sorted(daily_stats.items()):
            total = stats["total"]
            completed = stats["completed"]
            
            trends.append({
                "date": date,
                "total_jobs": total,
                "completed": completed,
                "failed": stats["failed"],
                "success_rate": (completed / total * 100) if total > 0 else 0
            })
        
        # Calculate overall metrics
        if trends:
            overall_success_rate = sum(t["success_rate"] for t in trends) / len(trends)
        else:
            overall_success_rate = 0
        
        return {
            "period_days": days,
            "daily_trends": trends[-days:],  # Last N days
            "overall_success_rate": overall_success_rate,
            "total_days_with_data": len(trends)
        }
    
    def get_duration_analysis_by_job_type(self) -> Dict[str, Any]:
        """
        Analyze job duration statistics per job type.
        
        Returns:
            Min, max, avg, median duration for each job type
        """
        joblogs = self.stores.joblogs.get_all()
        
        # Group by job type
        type_durations = defaultdict(list)
        
        for job in joblogs:
            job_type = job.get("job_type", "unknown")
            duration = job.get("duration_seconds", 0)
            status = job.get("status")
            
            # Only consider completed jobs for duration analysis
            if status == "completed" and duration > 0:
                type_durations[job_type].append(duration)
        
        # Calculate statistics
        result = {}
        for job_type, durations in type_durations.items():
            if not durations:
                continue
            
            sorted_durations = sorted(durations)
            
            result[job_type] = {
                "count": len(durations),
                "min_seconds": min(durations),
                "max_seconds": max(durations),
                "avg_seconds": sum(durations) / len(durations),
                "median_seconds": sorted_durations[len(sorted_durations) // 2],
                "min_minutes": min(durations) / 60,
                "max_minutes": max(durations) / 60,
                "avg_minutes": sum(durations) / len(durations) / 60,
                "median_minutes": sorted_durations[len(sorted_durations) // 2] / 60
            }
        
        return {
            "by_job_type": result,
            "total_job_types": len(result)
        }
    
    def get_status_distribution(self) -> Dict[str, Any]:
        """
        Analyze distribution of job statuses.
        
        Returns:
            Count and percentage per status
        """
        joblogs = self.stores.joblogs.get_all()
        
        if not joblogs:
            return {
                "total_jobs": 0,
                "distribution": {},
                "most_common": None
            }
        
        # Count by status
        status_counts = defaultdict(int)
        for job in joblogs:
            status = job.get("status", "unknown")
            status_counts[status] += 1
        
        total = len(joblogs)
        distribution = {
            status: {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
            for status, count in status_counts.items()
        }
        
        most_common = max(status_counts.items(), key=lambda x: x[1]) if status_counts else None
        
        return {
            "total_jobs": total,
            "distribution": distribution,
            "most_common": {
                "status": most_common[0],
                "count": most_common[1],
                "percentage": (most_common[1] / total * 100) if total > 0 else 0
            } if most_common else None
        }
    
    def get_throughput_metrics(self) -> Dict[str, Any]:
        """
        Calculate throughput metrics (jobs per time period).
        
        Returns:
            Jobs per day, week, month averages
        """
        joblogs = self.stores.joblogs.get_all()
        
        if not joblogs:
            return {
                "total_jobs": 0,
                "avg_jobs_per_day": 0,
                "avg_jobs_per_week": 0,
                "avg_jobs_per_month": 0
            }
        
        # Group by date
        daily_counts = defaultdict(int)
        
        for job in joblogs:
            created_at = job.get("created_at")
            if not created_at:
                continue
            
            try:
                date = created_at.split('T')[0]
                daily_counts[date] += 1
            except Exception:
                continue
        
        # Calculate averages
        total_days = len(daily_counts)
        total_jobs = len(joblogs)
        
        avg_jobs_per_day = total_jobs / total_days if total_days > 0 else 0
        avg_jobs_per_week = avg_jobs_per_day * 7
        avg_jobs_per_month = avg_jobs_per_day * 30
        
        # Find peak day
        peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        
        return {
            "total_jobs": total_jobs,
            "total_days_with_jobs": total_days,
            "avg_jobs_per_day": avg_jobs_per_day,
            "avg_jobs_per_week": avg_jobs_per_week,
            "avg_jobs_per_month": avg_jobs_per_month,
            "peak_day": {
                "date": peak_day[0],
                "jobs": peak_day[1]
            } if peak_day else None
        }
    
    def get_failure_analysis(self) -> Dict[str, Any]:
        """
        Analyze failed jobs for patterns.
        
        Returns:
            Failure rates by job type, pattern, material
        """
        joblogs = self.stores.joblogs.get_all()
        patterns = self.stores.patterns.get_all()
        families = self.stores.strip_families.get_all()
        
        # Create lookup maps
        pattern_map = {p["id"]: p for p in patterns}
        family_map = {f["id"]: f for f in families}
        
        # Group failures
        failure_by_type = defaultdict(lambda: {"total": 0, "failed": 0})
        failure_by_pattern = defaultdict(lambda: {"total": 0, "failed": 0})
        failure_by_material = defaultdict(lambda: {"total": 0, "failed": 0})
        
        for job in joblogs:
            job_type = job.get("job_type", "unknown")
            pattern_id = job.get("pattern_id")
            family_id = job.get("strip_family_id")
            status = job.get("status")
            
            # By job type
            failure_by_type[job_type]["total"] += 1
            if status == "failed":
                failure_by_type[job_type]["failed"] += 1
            
            # By pattern
            if pattern_id and pattern_id in pattern_map:
                pattern_name = pattern_map[pattern_id].get("name", "Unnamed")
                failure_by_pattern[pattern_name]["total"] += 1
                if status == "failed":
                    failure_by_pattern[pattern_name]["failed"] += 1
            
            # By material
            if family_id and family_id in family_map:
                material = family_map[family_id].get("material_type", "Unknown")
                failure_by_material[material]["total"] += 1
                if status == "failed":
                    failure_by_material[material]["failed"] += 1
        
        # Calculate failure rates
        def calculate_rates(data_dict):
            return [
                {
                    "name": name,
                    "total": stats["total"],
                    "failed": stats["failed"],
                    "failure_rate": (stats["failed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                }
                for name, stats in sorted(data_dict.items(), key=lambda x: x[1]["failed"], reverse=True)
            ]
        
        return {
            "by_job_type": calculate_rates(failure_by_type),
            "by_pattern": calculate_rates(failure_by_pattern)[:10],  # Top 10
            "by_material": calculate_rates(failure_by_material),
            "total_failures": sum(j.get("status") == "failed" for j in joblogs),
            "total_jobs": len(joblogs)
        }
    
    def get_job_type_distribution(self) -> Dict[str, Any]:
        """
        Analyze distribution of job types.
        
        Returns:
            Count and percentage per job type
        """
        joblogs = self.stores.joblogs.get_all()
        
        if not joblogs:
            return {
                "total_jobs": 0,
                "distribution": {}
            }
        
        # Count by job type
        type_counts = defaultdict(int)
        for job in joblogs:
            job_type = job.get("job_type", "unknown")
            type_counts[job_type] += 1
        
        total = len(joblogs)
        distribution = {
            job_type: {
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0
            }
            for job_type, count in type_counts.items()
        }
        
        return {
            "total_jobs": total,
            "distribution": distribution,
            "job_type_count": len(type_counts)
        }
    
    def get_recent_job_summary(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get summary of most recent jobs.
        
        Args:
            limit: Max jobs to return
            
        Returns:
            Recent jobs with key metrics
        """
        recent_jobs = self.stores.joblogs.get_recent(limit=limit)
        patterns = self.stores.patterns.get_all()
        
        # Create pattern lookup
        pattern_map = {p["id"]: p.get("name", "Unnamed") for p in patterns}
        
        # Enrich job data
        summary = []
        for job in recent_jobs:
            pattern_id = job.get("pattern_id")
            pattern_name = pattern_map.get(pattern_id, "Unknown") if pattern_id else "None"
            
            summary.append({
                "id": job["id"],
                "job_type": job.get("job_type"),
                "pattern_name": pattern_name,
                "status": job.get("status"),
                "duration_minutes": job.get("duration_seconds", 0) / 60,
                "created_at": job.get("created_at")
            })
        
        return {
            "recent_jobs": summary,
            "count": len(summary)
        }


def get_job_analytics() -> JobAnalytics:
    """
    Get singleton job analytics instance.
    
    Returns:
        JobAnalytics engine
    """
    return JobAnalytics()
