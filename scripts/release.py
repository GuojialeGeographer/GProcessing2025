#!/usr/bin/env python3
"""SVIPro Release Script."""
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result

def clean():
    print("\n🧹 Cleaning...")
    for pattern in ['dist', 'build', '*.egg-info']:
        if '*' in pattern:
            for path in Path('.').glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
        else:
            path = Path(pattern)
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
    print("✓ Cleaned")

def build():
    print("\n📦 Building...")
    run_command("python -m build")
    print("✓ Built")

def check():
    print("\n🔍 Checking...")
    run_command("twine check dist/*")
    print("✓ Checked")

def upload(mode='test'):
    if mode == 'production':
        print("\n🚀 Production Upload")
        if input("Sure? (yes/no): ") == 'yes':
            run_command("twine upload dist/*")
    else:
        print("\n🧪 Test Upload")
        run_command("twine upload --repository testpypi dist/*")
        print("\nTest: pip install --index-url https://test.pypi.org/simple/ svipro")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'test'
    print(f"SVIPro Release - {mode}")
    
    if not Path('pyproject.toml').exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    clean()
    build()
    check()
    upload(mode)
    print("\n✅ Done!")

if __name__ == '__main__':
    main()
