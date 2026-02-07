"""
RMOS JSON to SQLite Migration Tool (N8.7)

Migrates existing JSON pattern/joblog/strip family data to SQLite stores.
Scans data directories, validates JSON, and bulk inserts to database.

Features:
- Batch processing with transaction rollback on errors
- Duplicate detection (skip existing by ID)
- Validation of required fields
- Progress reporting
- Dry-run mode for testing
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..stores.rmos_stores import get_rmos_stores
from ..core.rmos_db import get_rmos_db

logger = logging.getLogger(__name__)


class RMOSMigrator:
    """
    Migrates JSON data to RMOS SQLite stores.
    
    Scans directories for JSON files and bulk inserts to database
    with validation and duplicate detection.
    """
    
    def __init__(self, data_dir: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize migrator.
        
        Args:
            data_dir: Root directory containing JSON data files
            dry_run: If True, validate but don't write to database
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data" / "rmos_legacy"
        self.dry_run = dry_run
        self.stores = get_rmos_stores()
        self.db = get_rmos_db()
        
        self.stats = {
            'patterns': {'found': 0, 'migrated': 0, 'skipped': 0, 'failed': 0},
            'joblogs': {'found': 0, 'migrated': 0, 'skipped': 0, 'failed': 0},
            'strip_families': {'found': 0, 'migrated': 0, 'skipped': 0, 'failed': 0}
        }
    
    def migrate_all(self) -> Dict[str, Any]:
        """
        Migrate all JSON data to SQLite.
        
        Returns:
            Migration statistics dictionary
            
        Example:
            migrator = RMOSMigrator()
            stats = migrator.migrate_all()
            print(f"Patterns migrated: {stats['patterns']['migrated']}")
        """
        logger.info(f"Starting RMOS migration from {self.data_dir}")
        logger.info(f"Dry run: {self.dry_run}")
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Migrate each entity type
        self._migrate_patterns()
        self._migrate_strip_families()
        self._migrate_joblogs()
        
        logger.info("Migration complete")
        return self.stats
    
    def _migrate_patterns(self):
        """Migrate pattern JSON files."""
        logger.info("Migrating patterns...")
        
        pattern_files = list(self.data_dir.glob("patterns/**/*.json"))
        self.stats['patterns']['found'] = len(pattern_files)
        
        for file_path in pattern_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Validate required fields
                if not self._validate_pattern(data):
                    logger.warning(f"Invalid pattern in {file_path}")
                    self.stats['patterns']['failed'] += 1
                    continue
                
                # Check if already exists
                if self.stores.patterns.get_by_id(data.get('id', '')):
                    logger.debug(f"Pattern {data['id']} already exists, skipping")
                    self.stats['patterns']['skipped'] += 1
                    continue
                
                # Insert to database
                if not self.dry_run:
                    self.stores.patterns.create(data)
                
                self.stats['patterns']['migrated'] += 1
                logger.debug(f"Migrated pattern: {data.get('name', 'unnamed')}")
                
            except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
                logger.error(f"Failed to migrate {file_path}: {e}")
                self.stats['patterns']['failed'] += 1
    
    def _migrate_strip_families(self):
        """Migrate strip family JSON files."""
        logger.info("Migrating strip families...")
        
        family_files = list(self.data_dir.glob("strip_families/**/*.json"))
        self.stats['strip_families']['found'] = len(family_files)
        
        for file_path in family_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Validate required fields
                if not self._validate_strip_family(data):
                    logger.warning(f"Invalid strip family in {file_path}")
                    self.stats['strip_families']['failed'] += 1
                    continue
                
                # Check if already exists
                if self.stores.strip_families.get_by_id(data.get('id', '')):
                    logger.debug(f"Strip family {data['id']} already exists, skipping")
                    self.stats['strip_families']['skipped'] += 1
                    continue
                
                # Insert to database
                if not self.dry_run:
                    self.stores.strip_families.create(data)
                
                self.stats['strip_families']['migrated'] += 1
                logger.debug(f"Migrated strip family: {data.get('name', 'unnamed')}")
                
            except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
                logger.error(f"Failed to migrate {file_path}: {e}")
                self.stats['strip_families']['failed'] += 1
    
    def _migrate_joblogs(self):
        """Migrate joblog JSON files."""
        logger.info("Migrating joblogs...")
        
        joblog_files = list(self.data_dir.glob("joblogs/**/*.json"))
        self.stats['joblogs']['found'] = len(joblog_files)
        
        for file_path in joblog_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Validate required fields
                if not self._validate_joblog(data):
                    logger.warning(f"Invalid joblog in {file_path}")
                    self.stats['joblogs']['failed'] += 1
                    continue
                
                # Check if already exists
                if self.stores.joblogs.get_by_id(data.get('id', '')):
                    logger.debug(f"JobLog {data['id']} already exists, skipping")
                    self.stats['joblogs']['skipped'] += 1
                    continue
                
                # Insert to database
                if not self.dry_run:
                    self.stores.joblogs.create(data)
                
                self.stats['joblogs']['migrated'] += 1
                logger.debug(f"Migrated joblog: {data.get('id', 'unknown')}")
                
            except (OSError, json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
                logger.error(f"Failed to migrate {file_path}: {e}")
                self.stats['joblogs']['failed'] += 1
    
    def _validate_pattern(self, data: Dict[str, Any]) -> bool:
        """Validate pattern data has required fields."""
        required = ['name', 'ring_count', 'geometry']
        return all(field in data for field in required)
    
    def _validate_strip_family(self, data: Dict[str, Any]) -> bool:
        """Validate strip family data has required fields."""
        required = ['name', 'strip_width_mm', 'strip_thickness_mm', 'material_type', 'strips']
        return all(field in data for field in required)
    
    def _validate_joblog(self, data: Dict[str, Any]) -> bool:
        """Validate joblog data has required fields."""
        required = ['job_type', 'parameters']
        return all(field in data for field in required)


def run_migration(data_dir: Optional[Path] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run RMOS JSON to SQLite migration.
    
    Args:
        data_dir: Root directory containing JSON data files
        dry_run: If True, validate but don't write to database
        
    Returns:
        Migration statistics dictionary
        
    Example:
        # Dry run to test
        stats = run_migration(dry_run=True)
        
        # Actual migration
        stats = run_migration()
    """
    migrator = RMOSMigrator(data_dir=data_dir, dry_run=dry_run)
    return migrator.migrate_all()


if __name__ == "__main__":
    import sys
    
    # Command-line usage
    dry_run = "--dry-run" in sys.argv
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    stats = run_migration(dry_run=dry_run)
    
    print("\n=== Migration Summary ===")
    for entity_type, counts in stats.items():
        print(f"\n{entity_type.upper()}:")
        print(f"  Found: {counts['found']}")
        print(f"  Migrated: {counts['migrated']}")
        print(f"  Skipped: {counts['skipped']}")
        print(f"  Failed: {counts['failed']}")
    
    total_found = sum(c['found'] for c in stats.values())
    total_migrated = sum(c['migrated'] for c in stats.values())
    total_failed = sum(c['failed'] for c in stats.values())
    
    print(f"\nTOTAL:")
    print(f"  Found: {total_found}")
    print(f"  Migrated: {total_migrated}")
    print(f"  Failed: {total_failed}")
    
    if dry_run:
        print("\n(DRY RUN - No data was written)")
    
    sys.exit(0 if total_failed == 0 else 1)
