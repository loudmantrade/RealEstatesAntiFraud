#!/usr/bin/env python3
"""Interactive wrapper for create_github_issues.py"""
import getpass
import os
import sys


def main():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("\nNo GITHUB_TOKEN found. Get token at: https://github.com/settings/tokens")
        token = getpass.getpass("Enter GitHub Personal Access Token: ").strip()
        if not token:
            print("Error: No token provided")
            sys.exit(1)
        os.environ["GITHUB_TOKEN"] = token

    sys.path.insert(0, os.path.dirname(__file__))
    from create_github_issues import create_issues

    create_issues()


if __name__ == "__main__":
    main()
