#!/usr/bin/env python3
"""
Validate .gitignore completeness for Faithful Finances API

This script checks that sensitive files are properly excluded from version control.
Run this script regularly to ensure security and compliance.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Dict
import argparse


class GitIgnoreValidator:
    """Validates .gitignore patterns for security and compliance."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.gitignore_path = self.project_root / ".gitignore"
        
        # Critical patterns that MUST be in .gitignore
        self.critical_patterns = {
            "Environment files": [
                ".env",
                ".env.*",
                "!.env.example"
            ],
            "Security keys": [
                "*.pem",
                "*.key", 
                "*.crt",
                "private_key*",
                "jwt_secret*",
                "api_keys.txt"
            ],
            "Database files": [
                "*.db",
                "*.sqlite",
                "*.sql"
            ],
            "Financial data": [
                "*transactions_export*",
                "*financial_data*",
                "*bank_data*",
                "*.csv",
                "*.xlsx"
            ],
            "Logs": [
                "*.log",
                "logs/",
                "*security.log*"
            ]
        }
        
        # Dangerous file patterns to scan for
        self.dangerous_patterns = [
            r"\.env$",
            r"\.env\.",
            r"secret",
            r"password",
            r"token",
            r"key",
            r"api[_-]key",
            r"private[_-]key",
            r"auth[_-]token",
            r"jwt",
            r"credentials",
            r"config\.json$",
            r"\.pem$",
            r"\.p12$",
            r"\.pfx$"
        ]

    def load_gitignore_patterns(self) -> List[str]:
        """Load patterns from .gitignore file."""
        if not self.gitignore_path.exists():
            return []
        
        patterns = []
        with open(self.gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
        
        return patterns

    def check_critical_patterns(self) -> Tuple[bool, List[str]]:
        """Check if critical security patterns are included."""
        gitignore_patterns = self.load_gitignore_patterns()
        missing_patterns = []
        
        for category, patterns in self.critical_patterns.items():
            for pattern in patterns:
                if pattern not in gitignore_patterns:
                    missing_patterns.append(f"{category}: {pattern}")
        
        return len(missing_patterns) == 0, missing_patterns

    def scan_for_sensitive_files(self) -> List[Tuple[str, str]]:
        """Scan repository for potentially sensitive files."""
        sensitive_files = []
        
        try:
            # Get all tracked files
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                print("Warning: Not in a git repository or git not available")
                return sensitive_files
            
            tracked_files = result.stdout.strip().split('\n')
            
            # Check each file against dangerous patterns
            for file_path in tracked_files:
                for pattern in self.dangerous_patterns:
                    if re.search(pattern, file_path, re.IGNORECASE):
                        sensitive_files.append((file_path, pattern))
                        break
            
        except Exception as e:
            print(f"Error scanning files: {e}")
        
        return sensitive_files

    def check_environment_files(self) -> List[str]:
        """Check for environment files that might be tracked."""
        env_files = []
        env_patterns = [".env*", "config.json", "secrets.*"]
        
        for pattern in env_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file() and file_path.name != ".env.example":
                    # Check if file is tracked by git
                    try:
                        result = subprocess.run(
                            ["git", "ls-files", "--error-unmatch", str(file_path)],
                            capture_output=True,
                            cwd=self.project_root
                        )
                        if result.returncode == 0:
                            env_files.append(str(file_path.relative_to(self.project_root)))
                    except:
                        pass
        
        return env_files

    def validate_file_permissions(self) -> List[str]:
        """Check for files with overly permissive permissions."""
        issues = []
        
        # Check for executable files that shouldn't be
        suspicious_executables = [
            ".env*",
            "*.json",
            "*.yaml", 
            "*.yml",
            "*.txt"
        ]
        
        for pattern in suspicious_executables:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file() and os.access(file_path, os.X_OK):
                    issues.append(f"Executable permission on {file_path.relative_to(self.project_root)}")
        
        return issues

    def check_git_history(self) -> List[str]:
        """Check git history for sensitive data patterns."""
        sensitive_history = []
        
        try:
            # Search git history for sensitive patterns
            sensitive_keywords = [
                "password",
                "secret",
                "token",
                "api.key",
                "private.key",
                "jwt",
                "auth.token"
            ]
            
            for keyword in sensitive_keywords:
                result = subprocess.run([
                    "git", "log", "--all", "--full-history", 
                    f"--grep={keyword}", "--oneline"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.stdout.strip():
                    commits = result.stdout.strip().split('\n')
                    for commit in commits[:3]:  # Limit to first 3 matches
                        sensitive_history.append(f"Potential sensitive commit: {commit}")
        
        except Exception as e:
            print(f"Warning: Could not check git history: {e}")
        
        return sensitive_history

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        report = {
            "critical_patterns_ok": True,
            "missing_patterns": [],
            "sensitive_files": [],
            "tracked_env_files": [],
            "permission_issues": [],
            "history_issues": [],
            "overall_status": "PASS"
        }
        
        # Check critical patterns
        critical_ok, missing = self.check_critical_patterns()
        report["critical_patterns_ok"] = critical_ok
        report["missing_patterns"] = missing
        
        # Scan for sensitive files
        report["sensitive_files"] = self.scan_for_sensitive_files()
        
        # Check environment files
        report["tracked_env_files"] = self.check_environment_files()
        
        # Check file permissions
        report["permission_issues"] = self.validate_file_permissions()
        
        # Check git history
        report["history_issues"] = self.check_git_history()
        
        # Determine overall status
        if (not critical_ok or 
            report["sensitive_files"] or 
            report["tracked_env_files"] or
            report["permission_issues"]):
            report["overall_status"] = "FAIL"
        elif report["history_issues"]:
            report["overall_status"] = "WARNING"
        
        return report

    def print_report(self, report: Dict, verbose: bool = False):
        """Print validation report."""
        status_colors = {
            "PASS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow  
            "FAIL": "\033[91m",  # Red
            "RESET": "\033[0m"
        }
        
        status = report["overall_status"]
        color = status_colors.get(status, "")
        reset = status_colors["RESET"]
        
        print(f"\n{'='*60}")
        print(f"🔒 GITIGNORE SECURITY VALIDATION REPORT")
        print(f"{'='*60}")
        print(f"Status: {color}{status}{reset}")
        print(f"Project: {self.project_root.absolute()}")
        print()
        
        # Critical patterns check
        if report["critical_patterns_ok"]:
            print("✅ Critical security patterns: PRESENT")
        else:
            print("❌ Critical security patterns: MISSING")
            for pattern in report["missing_patterns"]:
                print(f"   - {pattern}")
        print()
        
        # Sensitive files check
        if report["sensitive_files"]:
            print("❌ Potentially sensitive files found in repository:")
            for file_path, pattern in report["sensitive_files"]:
                print(f"   - {file_path} (matches: {pattern})")
        else:
            print("✅ No sensitive files found in tracked files")
        print()
        
        # Environment files check
        if report["tracked_env_files"]:
            print("❌ Environment files tracked by git:")
            for file_path in report["tracked_env_files"]:
                print(f"   - {file_path}")
        else:
            print("✅ No environment files tracked by git")
        print()
        
        # Permission issues
        if report["permission_issues"]:
            print("⚠️  File permission issues:")
            for issue in report["permission_issues"]:
                print(f"   - {issue}")
        else:
            print("✅ No file permission issues found")
        print()
        
        # History issues (only if verbose or there are issues)
        if report["history_issues"] and (verbose or status == "WARNING"):
            print("⚠️  Potential sensitive data in git history:")
            for issue in report["history_issues"]:
                print(f"   - {issue}")
            print()
        
        # Recommendations
        if status != "PASS":
            print("🔧 RECOMMENDED ACTIONS:")
            
            if report["missing_patterns"]:
                print("1. Add missing .gitignore patterns:")
                for pattern in report["missing_patterns"]:
                    print(f"   echo '{pattern.split(': ')[1]}' >> .gitignore")
            
            if report["sensitive_files"]:
                print("2. Remove sensitive files from git:")
                for file_path, _ in report["sensitive_files"]:
                    print(f"   git rm --cached {file_path}")
            
            if report["tracked_env_files"]:
                print("3. Remove environment files from git:")
                for file_path in report["tracked_env_files"]:
                    print(f"   git rm --cached {file_path}")
            
            if report["history_issues"]:
                print("4. Consider cleaning git history:")
                print("   git filter-branch --force --index-filter \\")
                print("     'git rm --cached --ignore-unmatch <sensitive-file>' \\")
                print("     --prune-empty --tag-name-filter cat -- --all")
        
        print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(
        description="Validate .gitignore for security and compliance"
    )
    parser.add_argument(
        "--project-root", 
        default=".",
        help="Path to project root (default: current directory)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including git history check"
    )
    parser.add_argument(
        "--fix",
        action="store_true", 
        help="Automatically fix common issues"
    )
    
    args = parser.parse_args()
    
    validator = GitIgnoreValidator(args.project_root)
    report = validator.generate_report()
    validator.print_report(report, args.verbose)
    
    # Auto-fix option
    if args.fix and report["overall_status"] != "PASS":
        print("\n🔧 Auto-fixing issues...")
        
        # Add missing critical patterns
        if report["missing_patterns"]:
            with open(validator.gitignore_path, "a") as f:
                f.write("\n# Auto-added critical security patterns\n")
                for pattern in report["missing_patterns"]:
                    pattern_only = pattern.split(": ")[1]
                    f.write(f"{pattern_only}\n")
            print("✅ Added missing .gitignore patterns")
        
        # Remove sensitive files from git
        for file_path, _ in report["sensitive_files"]:
            try:
                subprocess.run(
                    ["git", "rm", "--cached", file_path],
                    cwd=validator.project_root,
                    check=True
                )
                print(f"✅ Removed {file_path} from git tracking")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to remove {file_path} from git")
    
    # Exit with appropriate code
    if report["overall_status"] == "FAIL":
        sys.exit(1)
    elif report["overall_status"] == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()