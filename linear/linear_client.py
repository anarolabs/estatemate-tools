#!/usr/bin/env python3
"""
Linear API client for EstateMate.
Provides authenticated GraphQL requests against the EstateMate Improvements workspace (EST2).

Setup:
    1. Get your API key from Linear: Settings > API > Personal API keys
    2. Create credentials file at ~/.linear_api/estatemate-product-credentials.json:
       {"api_key": "lin_api_...", "team_id": "YOUR_TEAM_ID", "team_key": "EST2"}
    3. Get your team_id: run this script with --teams flag
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

LINEAR_API_URL = "https://api.linear.app/graphql"
CREDENTIALS_FILE = Path.home() / ".linear_api/estatemate-product-credentials.json"


def load_credentials():
    """Load Linear API credentials from secure location."""
    if not CREDENTIALS_FILE.exists():
        print("CREDENTIALS_MISSING", file=sys.stderr)
        print(f"Create file at {CREDENTIALS_FILE} with:", file=sys.stderr)
        print('{"api_key": "lin_api_...", "team_id": "...", "team_key": "EST2"}', file=sys.stderr)
        print("", file=sys.stderr)
        print("To get your API key:", file=sys.stderr)
        print("  1. Go to Linear > Settings > API > Personal API keys", file=sys.stderr)
        print("  2. Create a new key with a label like 'CLI scripts'", file=sys.stderr)
        print("  3. Copy the key (starts with lin_api_)", file=sys.stderr)
        print("", file=sys.stderr)
        print("To get your team_id:", file=sys.stderr)
        print("  Run: python3 linear_client.py --teams", file=sys.stderr)
        print("  (requires api_key to be set, team_id can be placeholder)", file=sys.stderr)
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        return json.load(f)


def get_headers():
    """Get authorization headers for Linear API."""
    creds = load_credentials()
    return {
        "Content-Type": "application/json",
        "Authorization": creds["api_key"]
    }


def execute_query(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Linear API."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    data = json.dumps(payload).encode("utf-8")
    headers = get_headers()

    req = urllib.request.Request(LINEAR_API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("AUTH_ERROR: Invalid or expired API key", file=sys.stderr)
            print("Check your API key at: Linear > Settings > API > Personal API keys", file=sys.stderr)
            sys.exit(1)
        elif e.code == 429:
            print("RATE_LIMITED: Too many requests - wait a moment and try again", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"HTTP_ERROR: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)
    except urllib.error.URLError as e:
        print(f"NETWORK_ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

    if "errors" in result:
        error_msgs = [e.get("message", str(e)) for e in result["errors"]]
        print(f"GRAPHQL_ERROR: {'; '.join(error_msgs)}", file=sys.stderr)
        sys.exit(1)

    return result.get("data", {})


def get_team_id():
    """Get the configured team ID."""
    return load_credentials()["team_id"]


def get_team_key():
    """Get the configured team key."""
    return load_credentials().get("team_key", "EST2")


def list_teams():
    """List all teams the API key has access to (helper for setup)."""
    creds = load_credentials()
    headers = {
        "Content-Type": "application/json",
        "Authorization": creds["api_key"]
    }
    query = '{"query": "{ teams { nodes { id name key } } }"}'
    req = urllib.request.Request(LINEAR_API_URL, data=query.encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            teams = result.get("data", {}).get("teams", {}).get("nodes", [])
            print("Teams you have access to:")
            print("-" * 60)
            for t in teams:
                print(f"  Key: {t['key']:10s}  Name: {t['name']:30s}  ID: {t['id']}")
            print("-" * 60)
            print(f"\nUse the team with key 'EST2' (Estatemate-Product).")
            print(f"Copy its ID into your credentials file as team_id.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Linear API client setup helper")
    parser.add_argument("--teams", action="store_true", help="List available teams (for finding your team_id)")
    args = parser.parse_args()

    if args.teams:
        list_teams()
    else:
        creds = load_credentials()
        print(f"Credentials loaded from: {CREDENTIALS_FILE}")
        print(f"Team key: {creds.get('team_key', 'not set')}")
        print(f"API key: {creds['api_key'][:12]}...")
        print("Run with --teams to list available teams.")
