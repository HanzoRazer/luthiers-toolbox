"""
RMOS Migration Audit Tool (N8.7)

Validates SQLite database integrity after migration.
Checks schema compliance, foreign keys, required fields, and data consistency.

Exit codes:
- 0: All checks passed
- 1: Validation failures detected
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from ..stores.rmos_stores import get_rmos_stores
from ..core.rmos_db import get_rmos_db

logger = logging.getLogger(__name__)


class RMOSMigrationAuditor:
    """
    Audits RMOS SQLite database for integrity and compliance.
    
    Performs comprehensive validation checks on migrated data
    including schema, foreign keys, required fields, and data types.
    """
    
    def __init__(self):
        """Initialize auditor with database connections."""
        self.stores = get_rmos_stores()
        self.db = get_rmos_db()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            'patterns': 0,
            'strip_families': 0,
            'joblogs': 0,
            'checks_passed': 0,
            'checks_failed': 0
        }
    
    def run_audit(self) -> bool:
        """
        Run all audit checks.
        
        Returns:
            True if all checks passed, False if any failures
            
        Example:
            auditor = RMOSMigrationAuditor()
            success = auditor.run_audit()
            if not success:
                print(f"Errors: {auditor.errors}")
        """
        logger.info("Starting RMOS migration audit")
        
        # Schema checks
        self._check_schema_version()
        self._check_tables_exist()
        self._check_indexes_exist()
        
        # Data integrity checks
        self._check_patterns_integrity()
        self._check_strip_families_integrity()
        self._check_joblogs_integrity()
        
        # Foreign key checks
        self._check_foreign_keys()
        
        # Consistency checks
        self._check_timestamp_consistency()
        self._check_json_fields()
        
        success = len(self.errors) == 0
        
        if success:
            logger.info(f"Audit PASSED: {self.stats['checks_passed']} checks completed")
        else:
            logger.error(f"Audit FAILED: {len(self.errors)} errors, {len(self.warnings)} warnings")
        
        return success
    
    def _check_schema_version(self):
        """Verify schema_version table exists and has valid version."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
                row = cursor.fetchone()
                
                if not row:
                    self.errors.append("Schema version table empty")
                    self.stats['checks_failed'] += 1
                else:
                    version = row[0]
                    if version != 1:
                        self.warnings.append(f"Schema version is {version}, expected 1")
                    self.stats['checks_passed'] += 1
                    logger.debug(f"Schema version: {version}")
        except Exception as e:
            self.errors.append(f"Failed to check schema version: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_tables_exist(self):
        """Verify all required tables exist."""
        required_tables = ['patterns', 'strip_families', 'joblogs', 'schema_version']
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                for table in required_tables:
                    if table not in existing_tables:
                        self.errors.append(f"Required table missing: {table}")
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
                        
                logger.debug(f"Found tables: {existing_tables}")
        except Exception as e:
            self.errors.append(f"Failed to check tables: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_indexes_exist(self):
        """Verify indexes exist for foreign keys and common queries."""
        expected_indexes = [
            'idx_patterns_strip_family',
            'idx_joblogs_pattern',
            'idx_joblogs_strip_family',
            'idx_joblogs_status'
        ]
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
                )
                existing_indexes = {row[0] for row in cursor.fetchall()}
                
                for index in expected_indexes:
                    if index in existing_indexes:
                        self.stats['checks_passed'] += 1
                    else:
                        self.warnings.append(f"Recommended index missing: {index}")
                        
                logger.debug(f"Found indexes: {existing_indexes}")
        except Exception as e:
            self.warnings.append(f"Failed to check indexes: {e}")
    
    def _check_patterns_integrity(self):
        """Validate patterns table data integrity."""
        try:
            patterns = self.stores.patterns.get_all()
            self.stats['patterns'] = len(patterns)
            
            for pattern in patterns:
                # Required fields
                if not pattern.get('id'):
                    self.errors.append(f"Pattern missing ID")
                    self.stats['checks_failed'] += 1
                    continue
                
                if not pattern.get('name'):
                    self.errors.append(f"Pattern {pattern['id']} missing name")
                    self.stats['checks_failed'] += 1
                
                if not isinstance(pattern.get('ring_count'), int) or pattern['ring_count'] < 1:
                    self.errors.append(f"Pattern {pattern['id']} has invalid ring_count")
                    self.stats['checks_failed'] += 1
                
                # Geometry field
                if not pattern.get('geometry'):
                    self.errors.append(f"Pattern {pattern['id']} missing geometry")
                    self.stats['checks_failed'] += 1
                
                # Timestamps
                if not pattern.get('created_at'):
                    self.errors.append(f"Pattern {pattern['id']} missing created_at")
                    self.stats['checks_failed'] += 1
                
                self.stats['checks_passed'] += 1
                
            logger.debug(f"Validated {len(patterns)} patterns")
        except Exception as e:
            self.errors.append(f"Failed to check patterns integrity: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_strip_families_integrity(self):
        """Validate strip_families table data integrity."""
        try:
            families = self.stores.strip_families.get_all()
            self.stats['strip_families'] = len(families)
            
            for family in families:
                # Required fields
                if not family.get('id'):
                    self.errors.append(f"Strip family missing ID")
                    self.stats['checks_failed'] += 1
                    continue
                
                if not family.get('name'):
                    self.errors.append(f"Strip family {family['id']} missing name")
                    self.stats['checks_failed'] += 1
                
                # Dimensions
                if not isinstance(family.get('strip_width_mm'), (int, float)) or family['strip_width_mm'] <= 0:
                    self.errors.append(f"Strip family {family['id']} has invalid strip_width_mm")
                    self.stats['checks_failed'] += 1
                
                if not isinstance(family.get('strip_thickness_mm'), (int, float)) or family['strip_thickness_mm'] <= 0:
                    self.errors.append(f"Strip family {family['id']} has invalid strip_thickness_mm")
                    self.stats['checks_failed'] += 1
                
                # Material type
                if not family.get('material_type'):
                    self.errors.append(f"Strip family {family['id']} missing material_type")
                    self.stats['checks_failed'] += 1
                
                # Strips array
                if not family.get('strips'):
                    self.errors.append(f"Strip family {family['id']} missing strips")
                    self.stats['checks_failed'] += 1
                
                self.stats['checks_passed'] += 1
                
            logger.debug(f"Validated {len(families)} strip families")
        except Exception as e:
            self.errors.append(f"Failed to check strip families integrity: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_joblogs_integrity(self):
        """Validate joblogs table data integrity."""
        try:
            joblogs = self.stores.joblogs.get_all()
            self.stats['joblogs'] = len(joblogs)
            
            valid_job_types = ['slice', 'batch', 'contour', 'assembly']
            valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
            
            for joblog in joblogs:
                # Required fields
                if not joblog.get('id'):
                    self.errors.append(f"JobLog missing ID")
                    self.stats['checks_failed'] += 1
                    continue
                
                # Job type
                if joblog.get('job_type') not in valid_job_types:
                    self.errors.append(f"JobLog {joblog['id']} has invalid job_type: {joblog.get('job_type')}")
                    self.stats['checks_failed'] += 1
                
                # Status
                if joblog.get('status') not in valid_statuses:
                    self.errors.append(f"JobLog {joblog['id']} has invalid status: {joblog.get('status')}")
                    self.stats['checks_failed'] += 1
                
                # Parameters
                if not joblog.get('parameters'):
                    self.warnings.append(f"JobLog {joblog['id']} missing parameters")
                
                # Duration consistency
                if joblog.get('status') == 'completed':
                    if not joblog.get('end_time'):
                        self.errors.append(f"Completed JobLog {joblog['id']} missing end_time")
                        self.stats['checks_failed'] += 1
                    
                    if not isinstance(joblog.get('duration_seconds'), (int, float)):
                        self.warnings.append(f"JobLog {joblog['id']} missing duration_seconds")
                
                self.stats['checks_passed'] += 1
                
            logger.debug(f"Validated {len(joblogs)} joblogs")
        except Exception as e:
            self.errors.append(f"Failed to check joblogs integrity: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_foreign_keys(self):
        """Validate foreign key relationships."""
        try:
            # Check patterns -> strip_families
            patterns = self.stores.patterns.get_all()
            for pattern in patterns:
                if pattern.get('strip_family_id'):
                    family = self.stores.strip_families.get_by_id(pattern['strip_family_id'])
                    if not family:
                        self.errors.append(
                            f"Pattern {pattern['id']} references non-existent strip_family {pattern['strip_family_id']}"
                        )
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
            
            # Check joblogs -> patterns
            joblogs = self.stores.joblogs.get_all()
            for joblog in joblogs:
                if joblog.get('pattern_id'):
                    pattern = self.stores.patterns.get_by_id(joblog['pattern_id'])
                    if not pattern:
                        self.errors.append(
                            f"JobLog {joblog['id']} references non-existent pattern {joblog['pattern_id']}"
                        )
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
                
                # Check joblogs -> strip_families
                if joblog.get('strip_family_id'):
                    family = self.stores.strip_families.get_by_id(joblog['strip_family_id'])
                    if not family:
                        self.errors.append(
                            f"JobLog {joblog['id']} references non-existent strip_family {joblog['strip_family_id']}"
                        )
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
            
            logger.debug("Foreign key checks completed")
        except Exception as e:
            self.errors.append(f"Failed to check foreign keys: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_timestamp_consistency(self):
        """Validate timestamp fields are properly formatted."""
        try:
            all_entities = []
            all_entities.extend(self.stores.patterns.get_all())
            all_entities.extend(self.stores.strip_families.get_all())
            all_entities.extend(self.stores.joblogs.get_all())
            
            for entity in all_entities:
                # Check created_at
                if entity.get('created_at'):
                    try:
                        datetime.fromisoformat(entity['created_at'])
                        self.stats['checks_passed'] += 1
                    except ValueError:
                        self.errors.append(f"Entity {entity.get('id')} has invalid created_at format")
                        self.stats['checks_failed'] += 1
                
                # Check updated_at
                if entity.get('updated_at'):
                    try:
                        datetime.fromisoformat(entity['updated_at'])
                        self.stats['checks_passed'] += 1
                    except ValueError:
                        self.errors.append(f"Entity {entity.get('id')} has invalid updated_at format")
                        self.stats['checks_failed'] += 1
            
            logger.debug("Timestamp consistency checks completed")
        except Exception as e:
            self.errors.append(f"Failed to check timestamp consistency: {e}")
            self.stats['checks_failed'] += 1
    
    def _check_json_fields(self):
        """Validate JSON fields can be parsed."""
        try:
            # Check patterns geometry
            patterns = self.stores.patterns.get_all()
            for pattern in patterns:
                if pattern.get('geometry'):
                    if not isinstance(pattern['geometry'], dict):
                        self.errors.append(f"Pattern {pattern['id']} geometry is not a dict")
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
                
                if pattern.get('metadata'):
                    if not isinstance(pattern['metadata'], dict):
                        self.warnings.append(f"Pattern {pattern['id']} metadata is not a dict")
            
            # Check strip families strips
            families = self.stores.strip_families.get_all()
            for family in families:
                if family.get('strips'):
                    if not isinstance(family['strips'], list):
                        self.errors.append(f"Strip family {family['id']} strips is not a list")
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
            
            # Check joblogs parameters and results
            joblogs = self.stores.joblogs.get_all()
            for joblog in joblogs:
                if joblog.get('parameters'):
                    if not isinstance(joblog['parameters'], dict):
                        self.errors.append(f"JobLog {joblog['id']} parameters is not a dict")
                        self.stats['checks_failed'] += 1
                    else:
                        self.stats['checks_passed'] += 1
                
                if joblog.get('results'):
                    if not isinstance(joblog['results'], dict):
                        self.warnings.append(f"JobLog {joblog['id']} results is not a dict")
            
            logger.debug("JSON field checks completed")
        except Exception as e:
            self.errors.append(f"Failed to check JSON fields: {e}")
            self.stats['checks_failed'] += 1
    
    def print_report(self):
        """Print audit report to console."""
        print("\n" + "=" * 70)
        print("RMOS MIGRATION AUDIT REPORT")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        print("ENTITY COUNTS:")
        print(f"  Patterns:       {self.stats['patterns']}")
        print(f"  Strip Families: {self.stats['strip_families']}")
        print(f"  JobLogs:        {self.stats['joblogs']}")
        print()
        
        print("CHECK RESULTS:")
        print(f"  Passed:  {self.stats['checks_passed']}")
        print(f"  Failed:  {self.stats['checks_failed']}")
        print()
        
        if self.errors:
            print("ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print("WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        success = len(self.errors) == 0
        status = "PASSED" if success else "FAILED"
        print(f"AUDIT STATUS: {status}")
        print("=" * 70)
        print()
        
        return success


def run_audit() -> bool:
    """
    Run RMOS migration audit.
    
    Returns:
        True if audit passed, False if failures detected
        
    Example:
        success = run_audit()
        sys.exit(0 if success else 1)
    """
    auditor = RMOSMigrationAuditor()
    success = auditor.run_audit()
    auditor.print_report()
    return success


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_audit()
    sys.exit(0 if success else 1)
