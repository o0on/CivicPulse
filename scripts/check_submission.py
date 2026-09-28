#!/usr/bin/env python3
import os
import re
import sys

def check_hardcoded_secrets(root_dir):
    secret_patterns = [
        re.compile(r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\'][a-zA-Z0-9_-]{10,}["\']'),
        re.compile(r'(?i)ghp_[a-zA-Z0-9]{36}'),
        re.compile(r'(?i)sk-[a-zA-Z0-9]{48}')
    ]
    issues = []
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath or 'node_modules' in dirpath or 'venv' in dirpath:
            continue
        for filename in filenames:
            if not filename.endswith(('.py', '.js', '.ts', '.yaml', '.yml', '.env.example')):
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        for pattern in secret_patterns:
                            if pattern.search(line):
                                issues.append(f"{filepath}:{i+1}: Potential hardcoded secret found.")
            except Exception:
                pass
    return issues

def check_latest_tags(root_dir):
    issues = []
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(('.yaml', '.yml')):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if 'image:' in line and ':latest' in line:
                                issues.append(f"{filepath}:{i+1}: Found ':latest' tag in image reference.")
                except Exception:
                    pass
    return issues

def check_localhost_usage(root_dir):
    issues = []
    for dirpath, _, filenames in os.walk(root_dir):
        if 'test' in dirpath or '.git' in dirpath or 'scripts' in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(('.py', '.yaml', '.yml')):
                if 'test' in filename.lower():
                    continue
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if 'localhost' in line:
                                issues.append(f"{filepath}:{i+1}: Found 'localhost' in non-test file.")
                except Exception:
                    pass
    return issues

def check_statefulset_pvcs(root_dir):
    issues = []
    k8s_dir = os.path.join(root_dir, 'k8s')
    if not os.path.exists(k8s_dir):
        return [f"{k8s_dir} not found."]
    for dirpath, _, filenames in os.walk(k8s_dir):
        for filename in filenames:
            if filename.endswith(('.yaml', '.yml')):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'kind: StatefulSet' in content and 'volumeClaimTemplates' not in content:
                            issues.append(f"{filepath}: StatefulSet missing volumeClaimTemplates (PVCs).")
                except Exception:
                    pass
    return issues

def check_cd_workflow_needs(root_dir):
    issues = []
    cd_file = os.path.join(root_dir, '.github', 'workflows', 'cd.yml')
    if not os.path.exists(cd_file):
        return [f"{cd_file} not found."]
    try:
        with open(cd_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'needs:' not in content:
                issues.append(f"{cd_file}: CD workflow missing 'needs:' clause to depend on CI.")
    except Exception:
        pass
    return issues

if __name__ == "__main__":
    root_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    all_issues = []
    all_issues.extend(check_hardcoded_secrets(root_directory))
    all_issues.extend(check_latest_tags(root_directory))
    all_issues.extend(check_localhost_usage(root_directory))
    all_issues.extend(check_statefulset_pvcs(root_directory))
    all_issues.extend(check_cd_workflow_needs(root_directory))

    if all_issues:
        print("Automatic Deductions Found:")
        for issue in all_issues:
            print(f"- {issue}")
        sys.exit(1)
    else:
        print("No automatic deductions found! Great job.")
        sys.exit(0)
