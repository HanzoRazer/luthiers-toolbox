#!/usr/bin/env python3
"""
Deployment Validation Harness

Systematically checks for common deployment issues:
1. Missing Python dependencies (imports vs requirements.txt)
2. Missing Docker directories (env vars need corresponding mkdir)
3. Missing environment variable definitions
4. Frontend cross-origin URL patterns (relative URLs in deployed clients)
5. API field mapping mismatches (backend snake_case vs frontend camelCase)

Usage:
    python scripts/ci/validate_deployment.py [--fix] [--verbose]

Exit codes:
    0 = All checks passed
    1 = Warnings found (non-blocking)
    2 = Errors found (blocking)
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
API_ROOT = REPO_ROOT / "services" / "api"
CLIENT_ROOT = REPO_ROOT / "packages" / "client"

# Known optional dependencies that may not be installed in all environments
OPTIONAL_DEPS = {
    "anthropic",  # Optional AI provider
    "psycopg2",   # PostgreSQL driver (not needed for SQLite)
    "psycopg2-binary",
}

# Critical external dependencies that commonly get forgotten
# Only these are checked to avoid false positives from internal imports
CRITICAL_DEPS = {
    "openai": "Required for DALL-E image generation",
    "httpx": "Required for async HTTP client",
    "pydantic": "Required for data validation",
    "fastapi": "Required for API framework",
    "uvicorn": "Required for ASGI server",
    "numpy": "Required for numerical operations",
    "shapely": "Required for geometry operations",
    "pillow": "Required for image processing (imported as PIL)",
    "PIL": "Required for image processing",
    "cv2": "Required for computer vision (opencv-python)",
    "ezdxf": "Required for DXF file handling",
    "jsonschema": "Required for schema validation",
}

# Directories that must exist in Docker for corresponding env vars
DOCKER_DIR_ENV_MAPPING = {
    "RMOS_RUNS_DIR": "/app/app/data/runs/rmos",
    "CAM_BACKUP_DIR": "/app/app/data/backups/cam",
    "RMOS_RUN_ATTACHMENTS_DIR": "/app/app/data/run_attachments",
}

# Frontend patterns that indicate cross-origin URL issues
CROSS_ORIGIN_PATTERNS = [
    # Direct relative URL usage in img/src without API_BASE check
    (r':src="[^"]*\.url"', "Possible relative URL in :src binding - ensure API_BASE prefix for deployed clients"),
    (r"fetch\(['\"]\/api", "Relative URL in fetch() - ensure API_BASE prefix"),
]

# API field mapping rules (backend → frontend)
FIELD_MAPPING_RULES = {
    "configured": "available",  # Vision provider status
    "created_at_utc": "createdAt",
    "updated_at_utc": "updatedAt",
    "run_id": "runId",
}


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    category: str
    severity: str  # "error", "warning", "info"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_hint: Optional[str] = None


@dataclass
class ValidationReport:
    """Aggregated validation results."""
    results: list = field(default_factory=list)

    def add(self, result: ValidationResult):
        self.results.append(result)

    def errors(self) -> list:
        return [r for r in self.results if r.severity == "error"]

    def warnings(self) -> list:
        return [r for r in self.results if r.severity == "warning"]

    def print_report(self, verbose: bool = False):
        """Print human-readable report."""
        errors = self.errors()
        warnings = self.warnings()

        if not self.results:
            print("[OK] All deployment checks passed")
            return

        if errors:
            print(f"\n{'='*60}")
            print(f"ERRORS ({len(errors)}) - These MUST be fixed before deployment")
            print(f"{'='*60}")
            for r in errors:
                self._print_result(r, verbose)

        if warnings:
            print(f"\n{'='*60}")
            print(f"WARNINGS ({len(warnings)}) - Review recommended")
            print(f"{'='*60}")
            for r in warnings:
                self._print_result(r, verbose)

        print(f"\nSummary: {len(errors)} errors, {len(warnings)} warnings")

    def _print_result(self, r: ValidationResult, verbose: bool):
        icon = "[ERROR]" if r.severity == "error" else "[WARN]"
        print(f"\n{icon} [{r.category}] {r.message}")
        if r.file_path:
            loc = r.file_path
            if r.line_number:
                loc += f":{r.line_number}"
            print(f"  Location: {loc}")
        if r.fix_hint and verbose:
            print(f"  Fix: {r.fix_hint}")


# =============================================================================
# VALIDATORS
# =============================================================================

def check_python_dependencies(report: ValidationReport, verbose: bool = False):
    """Check that critical external packages are in requirements.txt."""
    requirements_path = API_ROOT / "requirements.txt"

    if not requirements_path.exists():
        report.add(ValidationResult(
            category="dependencies",
            severity="error",
            message="requirements.txt not found",
            file_path=str(requirements_path),
        ))
        return

    # Parse requirements.txt
    installed_packages = set()
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Handle various requirement formats
            # package>=1.0, package==1.0, package[extra], git+...
            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if match:
                pkg_name = match.group(1).lower().replace("-", "_")
                installed_packages.add(pkg_name)
                # Also add common aliases
                if pkg_name == "pillow":
                    installed_packages.add("pil")
                if pkg_name == "opencv_python":
                    installed_packages.add("cv2")

    if verbose:
        print(f"Found {len(installed_packages)} packages in requirements.txt")

    # Scan Python files for imports of CRITICAL dependencies only
    app_path = API_ROOT / "app"
    critical_imports_found = {}  # pkg -> (file, line)

    for py_file in app_path.rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                pkg = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split(".")[0]
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split(".")[0]

                if pkg and pkg.lower() in CRITICAL_DEPS:
                    if pkg.lower() not in critical_imports_found:
                        critical_imports_found[pkg.lower()] = (str(py_file), node.lineno)
        except (SyntaxError, UnicodeDecodeError):
            continue

    if verbose:
        print(f"Found critical imports: {list(critical_imports_found.keys())}")

    # Check that critical imports are in requirements
    for pkg, (file_path, line) in critical_imports_found.items():
        pkg_normalized = pkg.lower().replace("-", "_")

        if pkg_normalized not in installed_packages:
            reason = CRITICAL_DEPS.get(pkg, "Required dependency")
            report.add(ValidationResult(
                category="dependencies",
                severity="error",
                message=f"Critical package '{pkg}' is imported but not in requirements.txt ({reason})",
                file_path=file_path,
                line_number=line,
                fix_hint=f"Add '{pkg}' to services/api/requirements.txt",
            ))


def check_docker_directories(report: ValidationReport, verbose: bool = False):
    """Check that Dockerfile creates directories for all env vars."""
    dockerfile_path = API_ROOT / "Dockerfile"

    if not dockerfile_path.exists():
        report.add(ValidationResult(
            category="docker",
            severity="warning",
            message="API Dockerfile not found",
            file_path=str(dockerfile_path),
        ))
        return

    with open(dockerfile_path) as f:
        dockerfile_content = f.read()

    # Find ENV declarations
    env_vars = re.findall(r'ENV\s+(\w+)=([^\n]+)', dockerfile_content)
    env_dict = {k: v for k, v in env_vars}

    # Find mkdir commands - handle multi-line with backslash continuation
    # First, normalize continuation lines
    normalized = dockerfile_content.replace('\\\n', ' ')

    # Find all paths in mkdir -p commands
    mkdir_paths = set()
    for match in re.finditer(r'mkdir\s+-p\s+([^&\n]+)', normalized):
        paths_str = match.group(1)
        # Split on whitespace to get individual paths
        for path in paths_str.split():
            path = path.strip()
            if path.startswith('/'):
                mkdir_paths.add(path)

    if verbose:
        print(f"Found ENV vars: {list(env_dict.keys())}")
        print(f"Found mkdir paths: {mkdir_paths}")

    # Check known directory mappings
    for env_var, expected_path in DOCKER_DIR_ENV_MAPPING.items():
        if env_var in env_dict:
            actual_path = env_dict[env_var].strip('"').strip("'")
            if actual_path not in mkdir_paths:
                report.add(ValidationResult(
                    category="docker",
                    severity="error",
                    message=f"ENV {env_var}={actual_path} but directory not created by mkdir",
                    file_path=str(dockerfile_path),
                    fix_hint=f"Add 'mkdir -p {actual_path}' to Dockerfile before setting ENV",
                ))
        else:
            report.add(ValidationResult(
                category="docker",
                severity="warning",
                message=f"Expected ENV {env_var} not found in Dockerfile",
                file_path=str(dockerfile_path),
                fix_hint=f"Add 'ENV {env_var}={expected_path}' to Dockerfile",
            ))


def check_cross_origin_urls(report: ValidationReport, verbose: bool = False, full_scan: bool = False):
    """Check for frontend patterns that may break in cross-origin deployments."""
    src_path = CLIENT_ROOT / "src"

    if not src_path.exists():
        report.add(ValidationResult(
            category="cross-origin",
            severity="warning",
            message="Client src directory not found",
            file_path=str(src_path),
        ))
        return

    if full_scan:
        # Scan ALL frontend files
        files_to_check = list(src_path.rglob("*.vue")) + list(src_path.rglob("*.ts"))
    else:
        # Only check specific high-risk directories
        high_risk_dirs = ["features/ai_images", "views", "components/ai"]
        files_to_check = []

        for risk_dir in high_risk_dirs:
            check_path = src_path / risk_dir
            if check_path.exists():
                files_to_check.extend(check_path.rglob("*.vue"))
                files_to_check.extend(check_path.rglob("*.ts"))

    if verbose:
        print(f"Checking {len(files_to_check)} {'total' if full_scan else 'high-risk'} files for cross-origin issues")

    for file_path in files_to_check:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check if file has API_BASE defined at all
            has_api_base = "API_BASE" in content or "VITE_API_BASE" in content

            for pattern, message in CROSS_ORIGIN_PATTERNS:
                for match in re.finditer(pattern, content):
                    # Get line number
                    line_start = content[:match.start()].count("\n") + 1

                    # Check if this specific usage is handled
                    context_start = max(0, match.start() - 200)
                    context_end = min(len(content), match.end() + 200)
                    context = content[context_start:context_end]

                    if "resolveAssetUrl" in context or "${API_BASE}" in context or "`${API_BASE}" in context:
                        continue  # This specific usage is handled

                    # If file has API_BASE but this usage doesn't, it's a warning
                    # If file doesn't have API_BASE at all, it's an error for ai_images
                    severity = "warning"
                    if "ai_images" in str(file_path) and not has_api_base:
                        severity = "error"

                    report.add(ValidationResult(
                        category="cross-origin",
                        severity=severity,
                        message=message,
                        file_path=str(file_path),
                        line_number=line_start,
                        fix_hint="Use resolveAssetUrl() or prepend VITE_API_BASE to relative URLs",
                    ))
        except UnicodeDecodeError:
            continue


def check_api_field_mapping(report: ValidationReport, verbose: bool = False):
    """Check for potential field mapping issues between backend and frontend."""
    # This is a heuristic check - looks for patterns that commonly cause issues

    src_path = CLIENT_ROOT / "src"
    if not src_path.exists():
        return

    # Look for response mapping code
    for ts_file in src_path.rglob("*.ts"):
        try:
            with open(ts_file, encoding="utf-8") as f:
                content = f.read()

            # Look for response mapping patterns
            # e.g., "p.available" when API returns "p.configured"
            for backend_field, frontend_field in FIELD_MAPPING_RULES.items():
                # Check if frontend code references the backend field directly
                # This would indicate a potential mismatch
                pattern = rf'[a-z]\.' + backend_field + r'\b'
                if re.search(pattern, content):
                    # Now check if there's proper mapping
                    mapping_pattern = rf'{frontend_field}.*{backend_field}|{backend_field}.*{frontend_field}'
                    if not re.search(mapping_pattern, content, re.IGNORECASE):
                        # Check for fallback patterns like "?? false" or "|| false"
                        if f".{backend_field}" in content and f"?? " not in content and f"|| " not in content:
                            report.add(ValidationResult(
                                category="field-mapping",
                                severity="warning",
                                message=f"Potential field mapping issue: '{backend_field}' used without fallback",
                                file_path=str(ts_file),
                                fix_hint=f"Consider: {frontend_field}: p.{frontend_field} ?? p.{backend_field} ?? defaultValue",
                            ))
        except UnicodeDecodeError:
            continue


def _get_stdlib_modules() -> set:
    """Get set of Python standard library module names."""
    # Common stdlib modules - not exhaustive but covers most cases
    return {
        "abc", "aifc", "argparse", "array", "ast", "asyncio", "atexit",
        "base64", "binascii", "bisect", "builtins", "bz2",
        "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code",
        "codecs", "codeop", "collections", "colorsys", "compileall",
        "concurrent", "configparser", "contextlib", "contextvars", "copy",
        "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses",
        "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
        "distutils", "doctest", "email", "encodings", "enum", "errno",
        "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
        "fractions", "ftplib", "functools", "gc", "getopt", "getpass",
        "gettext", "glob", "graphlib", "grp", "gzip", "hashlib", "heapq",
        "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp",
        "importlib", "inspect", "io", "ipaddress", "itertools", "json",
        "keyword", "lib2to3", "linecache", "locale", "logging", "lzma",
        "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap",
        "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
        "numbers", "operator", "optparse", "os", "ossaudiodev", "pathlib",
        "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
        "plistlib", "poplib", "posix", "posixpath", "pprint", "profile",
        "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue",
        "quopri", "random", "re", "readline", "reprlib", "resource",
        "rlcompleter", "runpy", "sched", "secrets", "select", "selectors",
        "shelve", "shlex", "shutil", "signal", "site", "smtpd", "smtplib",
        "sndhdr", "socket", "socketserver", "spwd", "sqlite3", "ssl",
        "stat", "statistics", "string", "stringprep", "struct", "subprocess",
        "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
        "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
        "threading", "time", "timeit", "tkinter", "token", "tokenize",
        "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
        "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid",
        "venv", "warnings", "wave", "weakref", "webbrowser", "winreg",
        "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
        "zipfile", "zipimport", "zlib", "_thread",
    }


# =============================================================================
# MAIN
# =============================================================================

def check_hardcoded_urls(report: ValidationReport, verbose: bool = False):
    """Check for hardcoded localhost/production URLs that should use env vars."""
    src_path = CLIENT_ROOT / "src"

    if not src_path.exists():
        return

    hardcoded_patterns = [
        (r'https?://localhost:\d+', "Hardcoded localhost URL"),
        (r'https?://127\.0\.0\.1:\d+', "Hardcoded 127.0.0.1 URL"),
        (r'https?://[a-z0-9-]+\.up\.railway\.app', "Hardcoded Railway URL"),
        (r'https?://[a-z0-9-]+\.vercel\.app', "Hardcoded Vercel URL"),
    ]

    files_checked = 0
    for file_path in src_path.rglob("*.ts"):
        if "node_modules" in str(file_path) or ".spec." in str(file_path):
            continue
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            files_checked += 1

            for pattern, message in hardcoded_patterns:
                for match in re.finditer(pattern, content):
                    line_num = content[:match.start()].count("\n") + 1
                    report.add(ValidationResult(
                        category="hardcoded-url",
                        severity="warning",
                        message=f"{message}: {match.group()}",
                        file_path=str(file_path),
                        line_number=line_num,
                        fix_hint="Use VITE_API_BASE environment variable instead",
                    ))
        except UnicodeDecodeError:
            continue

    if verbose:
        print(f"Checked {files_checked} TypeScript files for hardcoded URLs")


def check_env_var_usage(report: ValidationReport, verbose: bool = False):
    """Check that critical env vars are used consistently."""
    src_path = CLIENT_ROOT / "src"

    if not src_path.exists():
        return

    # Count files that make API calls vs files that use VITE_API_BASE
    api_call_files = set()
    env_var_files = set()

    for file_path in src_path.rglob("*.ts"):
        if "node_modules" in str(file_path):
            continue
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if re.search(r"fetch\(['\"]\/api", content):
                api_call_files.add(str(file_path))
            if "VITE_API_BASE" in content or "API_BASE" in content:
                env_var_files.add(str(file_path))
        except UnicodeDecodeError:
            continue

    # Files making API calls without API_BASE
    missing_base = api_call_files - env_var_files

    if verbose:
        print(f"Files with API calls: {len(api_call_files)}, Files with API_BASE: {len(env_var_files)}")

    if missing_base and verbose:
        report.add(ValidationResult(
            category="env-vars",
            severity="info",
            message=f"{len(missing_base)} files make API calls without explicit API_BASE import",
            fix_hint="Consider centralizing API calls through SDK modules that handle base URL",
        ))


def main():
    parser = argparse.ArgumentParser(description="Validate deployment configuration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--full", action="store_true", help="Full codebase scan (slower, more comprehensive)")
    args = parser.parse_args()

    report = ValidationReport()

    mode = "FULL CODEBASE" if args.full else "TARGETED"
    print(f"Running deployment validation checks ({mode})...\n")

    print("1. Checking Python dependencies...")
    check_python_dependencies(report, args.verbose)

    print("2. Checking Docker directory configuration...")
    check_docker_directories(report, args.verbose)

    print("3. Checking cross-origin URL patterns...")
    check_cross_origin_urls(report, args.verbose, full_scan=args.full)

    print("4. Checking API field mappings...")
    check_api_field_mapping(report, args.verbose)

    if args.full:
        print("5. Checking for hardcoded URLs...")
        check_hardcoded_urls(report, args.verbose)

        print("6. Checking environment variable usage...")
        check_env_var_usage(report, args.verbose)

    if args.json:
        results = [
            {
                "category": r.category,
                "severity": r.severity,
                "message": r.message,
                "file_path": r.file_path,
                "line_number": r.line_number,
                "fix_hint": r.fix_hint,
            }
            for r in report.results
        ]
        print(json.dumps({"results": results}, indent=2))
    else:
        report.print_report(args.verbose)

    # Exit code
    if report.errors():
        sys.exit(2)
    elif report.warnings():
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
