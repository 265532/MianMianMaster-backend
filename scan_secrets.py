import os
import re

def scan_directory(directory):
    email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    ip_regex = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    key_regex = re.compile(r'(?i)(secret|password|token|key)[\s]*[=:]\s*[\'\"].{5,}?[\'\"]')

    issues_found = False

    for root, dirs, files in os.walk(directory):
        if any(ignored in root for ignored in ['.git', '__pycache__', '.trae', 'alembic', 'tests', 'venv', 'env']):
            continue
        for file in files:
            if file.endswith('.py') or file.endswith('.md') or file.endswith('.yml') or file == 'Dockerfile':
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_no, line in enumerate(f, 1):
                            if email_regex.search(line):
                                print(f'Potential Email found in {file_path}:{line_no} - {line.strip()}')
                                issues_found = True
                            if ip_regex.search(line) and '0.0.0.0' not in line and '127.0.0.1' not in line:
                                print(f'Potential Hardcoded IP found in {file_path}:{line_no} - {line.strip()}')
                                issues_found = True
                            if key_regex.search(line):
                                print(f'Potential Sensitive Key found in {file_path}:{line_no} - {line.strip()}')
                                issues_found = True
                except Exception as e:
                    pass
    if not issues_found:
        print('No sensitive information found.')

if __name__ == '__main__':
    scan_directory('.')