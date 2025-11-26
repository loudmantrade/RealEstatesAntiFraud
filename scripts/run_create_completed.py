#!/usr/bin/env python3
import os, sys, getpass
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("\nGitHub token needed to create completed bootstrap issues")
    token = getpass.getpass("Enter token: ").strip()
    if not token: sys.exit(1)
    os.environ["GITHUB_TOKEN"] = token
sys.path.insert(0, os.path.dirname(__file__))
from create_completed_issues import create_completed_issues
create_completed_issues()
