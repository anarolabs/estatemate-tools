#!/usr/bin/env python3
"""
Linear CRUD operations for EstateMate Improvements.
Create, update, list, comment, and manage issues in the EST2 workspace.

Quick start:
    # List all open issues
    python3 linear_operations.py --list

    # Create an improvement
    python3 linear_operations.py --create --title "Bug: Portfolio shows 0 EUR" --priority high --labels "Bug,01-property-management"

    # Update status
    python3 linear_operations.py --update EST2-42 --status "In Progress"

    # See full issue details
    python3 linear_operations.py --get EST2-42

Full usage: python3 linear_operations.py --help
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))
from linear_client import execute_query, get_team_id, get_team_key


# Priority mapping (Linear uses 0-4, with 0 being no priority)
PRIORITY_MAP = {
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "low": 4,
    "none": 0
}

# Reverse priority map for display
PRIORITY_DISPLAY = {v: k for k, v in PRIORITY_MAP.items()}


def get_workflow_states():
    """Get all workflow states for the team."""
    team_id = get_team_id()
    query = f"""
    {{
        team(id: "{team_id}") {{
            states {{
                nodes {{
                    id
                    name
                    type
                }}
            }}
        }}
    }}
    """
    result = execute_query(query)
    return result.get("team", {}).get("states", {}).get("nodes", [])


def get_state_id(status_name: str) -> str:
    """Get state ID by name (case-insensitive partial match)."""
    states = get_workflow_states()
    status_lower = status_name.lower()

    for state in states:
        if status_lower in state["name"].lower():
            return state["id"]

    available = [s["name"] for s in states]
    print(f"ERROR: Status '{status_name}' not found. Available: {', '.join(available)}", file=sys.stderr)
    sys.exit(1)


def get_projects():
    """Get all projects for the team."""
    team_id = get_team_id()
    query = f"""
    {{
        team(id: "{team_id}") {{
            projects {{
                nodes {{
                    id
                    name
                    state
                }}
            }}
        }}
    }}
    """
    result = execute_query(query)
    return result.get("team", {}).get("projects", {}).get("nodes", [])


def get_project_id(project_name: str) -> str:
    """Get project ID by name (case-insensitive partial match)."""
    projects = get_projects()
    name_lower = project_name.lower()

    for project in projects:
        if name_lower in project["name"].lower():
            return project["id"]

    available = [p["name"] for p in projects]
    print(f"ERROR: Project '{project_name}' not found. Available: {', '.join(available)}", file=sys.stderr)
    sys.exit(1)


def get_labels():
    """Get all labels for the team."""
    team_id = get_team_id()
    query = f"""
    {{
        team(id: "{team_id}") {{
            labels {{
                nodes {{
                    id
                    name
                    color
                }}
            }}
        }}
    }}
    """
    result = execute_query(query)
    return result.get("team", {}).get("labels", {}).get("nodes", [])


def get_label_ids(label_names: list) -> list:
    """Get label IDs from list of names (case-insensitive partial match)."""
    labels = get_labels()
    label_ids = []

    for name in label_names:
        name_lower = name.strip().lower()
        found = False
        for label in labels:
            if name_lower in label["name"].lower():
                label_ids.append(label["id"])
                found = True
                break
        if not found:
            available = [l["name"] for l in labels]
            print(f"ERROR: Label '{name}' not found. Available: {', '.join(available)}", file=sys.stderr)
            sys.exit(1)

    return label_ids


def get_users():
    """Get all active users in the organization."""
    query = """
    {
        users {
            nodes {
                id
                name
                email
                active
            }
        }
    }
    """
    result = execute_query(query)
    return result.get("users", {}).get("nodes", [])


def get_user_id(user_name: str) -> str:
    """Get user ID by name or email (case-insensitive partial match)."""
    users = get_users()
    name_lower = user_name.lower()

    for user in users:
        if user.get("active") and (
            name_lower in user["name"].lower() or
            name_lower in user.get("email", "").lower()
        ):
            return user["id"]

    available = [u["name"] for u in users if u.get("active")]
    print(f"ERROR: User '{user_name}' not found. Available: {', '.join(available)}", file=sys.stderr)
    sys.exit(1)


def get_issue_id(identifier: str) -> str:
    """Get issue UUID from identifier (e.g., EST2-42)."""
    query = f"""
    {{
        issue(id: "{identifier}") {{
            id
        }}
    }}
    """
    result = execute_query(query)
    issue = result.get("issue")
    if not issue:
        print(f"ERROR: Issue '{identifier}' not found", file=sys.stderr)
        sys.exit(1)
    return issue["id"]


def get_issue_with_labels(identifier: str) -> dict:
    """Get issue with current labels for add/remove operations."""
    query = f"""
    {{
        issue(id: "{identifier}") {{
            id
            identifier
            labels {{
                nodes {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    result = execute_query(query)
    issue = result.get("issue")
    if not issue:
        print(f"ERROR: Issue '{identifier}' not found", file=sys.stderr)
        sys.exit(1)
    return issue


def escape_graphql(text: str) -> str:
    """Escape text for GraphQL string literal."""
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def validate_date(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD."""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))


def create_issue(title: str, description: str = None, priority: str = None,
                 project: str = None, parent: str = None, labels: list = None,
                 due_date: str = None, assignee: str = None, status: str = None):
    """Create a new issue."""
    team_id = get_team_id()
    title_escaped = escape_graphql(title)
    input_fields = [f'teamId: "{team_id}"', f'title: "{title_escaped}"']

    if description:
        desc_escaped = escape_graphql(description)
        input_fields.append(f'description: "{desc_escaped}"')

    if priority:
        priority_value = PRIORITY_MAP.get(priority.lower(), 0)
        input_fields.append(f'priority: {priority_value}')

    if project:
        project_id = get_project_id(project)
        input_fields.append(f'projectId: "{project_id}"')

    if parent:
        parent_id = get_issue_id(parent)
        input_fields.append(f'parentId: "{parent_id}"')

    if labels:
        label_ids = get_label_ids(labels)
        ids_str = ", ".join([f'"{lid}"' for lid in label_ids])
        input_fields.append(f'labelIds: [{ids_str}]')

    if due_date:
        if not validate_date(due_date):
            print(f"ERROR: Invalid date format '{due_date}'. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
        input_fields.append(f'dueDate: "{due_date}"')

    if assignee:
        user_id = get_user_id(assignee)
        input_fields.append(f'assigneeId: "{user_id}"')

    if status:
        state_id = get_state_id(status)
        input_fields.append(f'stateId: "{state_id}"')

    input_str = ", ".join(input_fields)

    mutation = f"""
    mutation {{
        issueCreate(input: {{{input_str}}}) {{
            success
            issue {{
                id
                identifier
                title
                url
                parent {{
                    identifier
                }}
                labels {{
                    nodes {{
                        name
                    }}
                }}
                dueDate
                assignee {{
                    name
                }}
            }}
        }}
    }}
    """

    result = execute_query(mutation)
    issue_data = result.get("issueCreate", {})

    if issue_data.get("success"):
        issue = issue_data.get("issue", {})
        output = {
            "success": True,
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "url": issue.get("url")
        }
        if issue.get("parent"):
            output["parent"] = issue["parent"]["identifier"]
        if issue.get("labels", {}).get("nodes"):
            output["labels"] = [l["name"] for l in issue["labels"]["nodes"]]
        if issue.get("dueDate"):
            output["due_date"] = issue["dueDate"]
        if issue.get("assignee"):
            output["assignee"] = issue["assignee"]["name"]
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to create issue"}))
        sys.exit(1)


def update_issue(identifier: str, status: str = None, priority: str = None,
                 title: str = None, description: str = None, project: str = None,
                 parent: str = None, labels: list = None, due_date: str = None,
                 assignee: str = None):
    """Update an existing issue."""
    issue_id = get_issue_id(identifier)
    input_fields = []

    if status:
        state_id = get_state_id(status)
        input_fields.append(f'stateId: "{state_id}"')

    if priority:
        priority_value = PRIORITY_MAP.get(priority.lower(), 0)
        input_fields.append(f'priority: {priority_value}')

    if title:
        title_escaped = escape_graphql(title)
        input_fields.append(f'title: "{title_escaped}"')

    if description:
        desc_escaped = escape_graphql(description)
        input_fields.append(f'description: "{desc_escaped}"')

    if project:
        project_id = get_project_id(project)
        input_fields.append(f'projectId: "{project_id}"')

    if parent:
        parent_id = get_issue_id(parent)
        input_fields.append(f'parentId: "{parent_id}"')

    if labels:
        label_ids = get_label_ids(labels)
        ids_str = ", ".join([f'"{lid}"' for lid in label_ids])
        input_fields.append(f'labelIds: [{ids_str}]')

    if due_date:
        if not validate_date(due_date):
            print(f"ERROR: Invalid date format '{due_date}'. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
        input_fields.append(f'dueDate: "{due_date}"')

    if assignee:
        user_id = get_user_id(assignee)
        input_fields.append(f'assigneeId: "{user_id}"')

    if not input_fields:
        print("ERROR: No updates specified.", file=sys.stderr)
        sys.exit(1)

    input_str = ", ".join(input_fields)

    mutation = f"""
    mutation {{
        issueUpdate(id: "{issue_id}", input: {{{input_str}}}) {{
            success
            issue {{
                id
                identifier
                title
                state {{
                    name
                }}
                priority
                url
                parent {{
                    identifier
                }}
                project {{
                    name
                }}
                labels {{
                    nodes {{
                        name
                    }}
                }}
                dueDate
                assignee {{
                    name
                }}
            }}
        }}
    }}
    """

    result = execute_query(mutation)
    update_data = result.get("issueUpdate", {})

    if update_data.get("success"):
        issue = update_data.get("issue", {})
        output = {
            "success": True,
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "status": issue.get("state", {}).get("name"),
            "priority": PRIORITY_DISPLAY.get(issue.get("priority"), "none"),
            "url": issue.get("url")
        }
        if issue.get("parent"):
            output["parent"] = issue["parent"]["identifier"]
        if issue.get("project"):
            output["project"] = issue["project"]["name"]
        if issue.get("labels", {}).get("nodes"):
            output["labels"] = [l["name"] for l in issue["labels"]["nodes"]]
        if issue.get("dueDate"):
            output["due_date"] = issue["dueDate"]
        if issue.get("assignee"):
            output["assignee"] = issue["assignee"]["name"]
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to update issue"}))
        sys.exit(1)


def list_issues(status: str = None, project: str = None, priority: str = None,
                label: str = None, assignee: str = None, limit: int = 25):
    """List/search issues with filters."""
    team_id = get_team_id()
    filters = []

    if status:
        status_escaped = escape_graphql(status)
        filters.append(f'state: {{ name: {{ containsIgnoreCase: "{status_escaped}" }} }}')

    if project:
        project_escaped = escape_graphql(project)
        filters.append(f'project: {{ name: {{ containsIgnoreCase: "{project_escaped}" }} }}')

    if priority:
        priority_value = PRIORITY_MAP.get(priority.lower(), 0)
        filters.append(f'priority: {{ eq: {priority_value} }}')

    if label:
        label_escaped = escape_graphql(label)
        filters.append(f'labels: {{ name: {{ containsIgnoreCase: "{label_escaped}" }} }}')

    if assignee:
        assignee_escaped = escape_graphql(assignee)
        filters.append(f'assignee: {{ name: {{ containsIgnoreCase: "{assignee_escaped}" }} }}')

    filter_str = ", ".join(filters) if filters else ""
    filter_clause = f', filter: {{ {filter_str} }}' if filter_str else ""

    query = f"""
    {{
        team(id: "{team_id}") {{
            issues(first: {limit}, orderBy: updatedAt{filter_clause}) {{
                nodes {{
                    identifier
                    title
                    priority
                    dueDate
                    state {{
                        name
                    }}
                    project {{
                        name
                    }}
                    assignee {{
                        name
                    }}
                    labels {{
                        nodes {{
                            name
                        }}
                    }}
                    parent {{
                        identifier
                    }}
                    url
                }}
            }}
        }}
    }}
    """

    result = execute_query(query)
    issues = result.get("team", {}).get("issues", {}).get("nodes", [])

    output = []
    for issue in issues:
        item = {
            "identifier": issue["identifier"],
            "title": issue["title"],
            "status": issue.get("state", {}).get("name"),
            "priority": PRIORITY_DISPLAY.get(issue.get("priority"), "none"),
            "url": issue["url"]
        }
        if issue.get("project"):
            item["project"] = issue["project"]["name"]
        if issue.get("assignee"):
            item["assignee"] = issue["assignee"]["name"]
        if issue.get("labels", {}).get("nodes"):
            item["labels"] = [l["name"] for l in issue["labels"]["nodes"]]
        if issue.get("parent"):
            item["parent"] = issue["parent"]["identifier"]
        if issue.get("dueDate"):
            item["due_date"] = issue["dueDate"]
        output.append(item)

    print(json.dumps(output, indent=2))


def add_labels_to_issue(identifier: str, label_names: list):
    """Add labels to an issue (preserves existing labels)."""
    issue = get_issue_with_labels(identifier)
    issue_id = issue["id"]
    current_label_ids = [l["id"] for l in issue.get("labels", {}).get("nodes", [])]
    new_label_ids = get_label_ids(label_names)
    all_label_ids = list(set(current_label_ids + new_label_ids))
    ids_str = ", ".join([f'"{lid}"' for lid in all_label_ids])

    mutation = f"""
    mutation {{
        issueUpdate(id: "{issue_id}", input: {{labelIds: [{ids_str}]}}) {{
            success
            issue {{
                identifier
                labels {{
                    nodes {{
                        name
                    }}
                }}
            }}
        }}
    }}
    """

    result = execute_query(mutation)
    update_data = result.get("issueUpdate", {})

    if update_data.get("success"):
        issue = update_data.get("issue", {})
        print(json.dumps({
            "success": True,
            "identifier": issue.get("identifier"),
            "labels": [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
        }, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to add labels"}))
        sys.exit(1)


def remove_labels_from_issue(identifier: str, label_names: list):
    """Remove labels from an issue."""
    issue = get_issue_with_labels(identifier)
    issue_id = issue["id"]
    current_labels = issue.get("labels", {}).get("nodes", [])
    current_label_ids = [l["id"] for l in current_labels]
    remove_ids = set(get_label_ids(label_names))
    remaining_ids = [lid for lid in current_label_ids if lid not in remove_ids]
    ids_str = ", ".join([f'"{lid}"' for lid in remaining_ids]) if remaining_ids else ""

    mutation = f"""
    mutation {{
        issueUpdate(id: "{issue_id}", input: {{labelIds: [{ids_str}]}}) {{
            success
            issue {{
                identifier
                labels {{
                    nodes {{
                        name
                    }}
                }}
            }}
        }}
    }}
    """

    result = execute_query(mutation)
    update_data = result.get("issueUpdate", {})

    if update_data.get("success"):
        issue = update_data.get("issue", {})
        print(json.dumps({
            "success": True,
            "identifier": issue.get("identifier"),
            "labels": [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
        }, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to remove labels"}))
        sys.exit(1)


def add_comment(identifier: str, body: str):
    """Add a comment to an issue."""
    issue_id = get_issue_id(identifier)
    body_escaped = escape_graphql(body)

    mutation = f"""
    mutation {{
        commentCreate(input: {{issueId: "{issue_id}", body: "{body_escaped}"}}) {{
            success
            comment {{
                id
                body
                createdAt
            }}
        }}
    }}
    """

    result = execute_query(mutation)
    comment_data = result.get("commentCreate", {})

    if comment_data.get("success"):
        comment = comment_data.get("comment", {})
        print(json.dumps({
            "success": True,
            "comment_id": comment.get("id"),
            "created_at": comment.get("createdAt")
        }, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to add comment"}))
        sys.exit(1)


def archive_issue(identifier: str):
    """Archive (soft-delete) an issue."""
    issue_id = get_issue_id(identifier)

    mutation = f"""
    mutation {{
        issueArchive(id: "{issue_id}") {{
            success
        }}
    }}
    """

    result = execute_query(mutation)
    archive_data = result.get("issueArchive", {})

    if archive_data.get("success"):
        print(json.dumps({
            "success": True,
            "message": f"Issue {identifier} archived"
        }, indent=2))
    else:
        print(json.dumps({"success": False, "error": "Failed to archive issue"}))
        sys.exit(1)


def get_issue(identifier: str):
    """Get full details of an issue."""
    query = f"""
    {{
        issue(id: "{identifier}") {{
            id
            identifier
            title
            description
            priority
            dueDate
            state {{
                name
                type
            }}
            project {{
                name
            }}
            parent {{
                identifier
                title
            }}
            children {{
                nodes {{
                    identifier
                    title
                    state {{
                        name
                    }}
                }}
            }}
            assignee {{
                name
                email
            }}
            labels {{
                nodes {{
                    id
                    name
                    color
                }}
            }}
            comments {{
                nodes {{
                    body
                    createdAt
                    user {{
                        name
                    }}
                }}
            }}
            url
            createdAt
            updatedAt
        }}
    }}
    """

    result = execute_query(query)
    issue = result.get("issue")

    if not issue:
        print(f"ERROR: Issue '{identifier}' not found", file=sys.stderr)
        sys.exit(1)

    output = {
        "identifier": issue.get("identifier"),
        "title": issue.get("title"),
        "description": issue.get("description"),
        "status": issue.get("state", {}).get("name"),
        "priority": PRIORITY_DISPLAY.get(issue.get("priority"), "none"),
        "project": issue.get("project", {}).get("name") if issue.get("project") else None,
        "assignee": issue.get("assignee", {}).get("name") if issue.get("assignee") else None,
        "url": issue.get("url"),
        "created_at": issue.get("createdAt"),
        "updated_at": issue.get("updatedAt"),
    }

    if issue.get("parent"):
        output["parent"] = {
            "identifier": issue["parent"]["identifier"],
            "title": issue["parent"]["title"]
        }

    if issue.get("children", {}).get("nodes"):
        output["children"] = [
            {
                "identifier": c["identifier"],
                "title": c["title"],
                "status": c.get("state", {}).get("name")
            }
            for c in issue["children"]["nodes"]
        ]

    if issue.get("labels", {}).get("nodes"):
        output["labels"] = [l["name"] for l in issue["labels"]["nodes"]]

    if issue.get("dueDate"):
        output["due_date"] = issue["dueDate"]

    output["comments"] = [
        {
            "body": c.get("body"),
            "author": c.get("user", {}).get("name"),
            "created_at": c.get("createdAt")
        }
        for c in issue.get("comments", {}).get("nodes", [])
    ]

    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Linear operations for EstateMate Improvements (EST2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create an improvement ticket
  python3 linear_operations.py --create --title "Bug: Portfolio shows 0 EUR" \\
    --priority high --labels "Bug,01-property-management" \\
    --project "EstateMate Improvements"

  # List open issues
  python3 linear_operations.py --list --status "Todo"
  python3 linear_operations.py --list --priority high
  python3 linear_operations.py --list --label "Bug"

  # Update an issue
  python3 linear_operations.py --update EST2-42 --status "In Progress"
  python3 linear_operations.py --update EST2-42 --assignee "Christof"

  # Add/remove labels
  python3 linear_operations.py --add-labels EST2-42 --labels "urgent"
  python3 linear_operations.py --remove-labels EST2-42 --labels "urgent"

  # Comment and details
  python3 linear_operations.py --comment EST2-42 --body "Found the root cause"
  python3 linear_operations.py --get EST2-42

  # Archive
  python3 linear_operations.py --archive EST2-42
"""
    )

    # Operation flags (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Create a new issue")
    group.add_argument("--update", metavar="ISSUE", help="Update issue (e.g., EST2-42)")
    group.add_argument("--list", action="store_true", help="List/search issues with filters")
    group.add_argument("--add-labels", metavar="ISSUE", help="Add labels to issue (preserves existing)")
    group.add_argument("--remove-labels", metavar="ISSUE", help="Remove labels from issue")
    group.add_argument("--comment", metavar="ISSUE", help="Add comment to issue")
    group.add_argument("--archive", metavar="ISSUE", help="Archive issue")
    group.add_argument("--get", metavar="ISSUE", help="Get issue details")

    # Issue attributes
    parser.add_argument("--title", help="Issue title (required for --create)")
    parser.add_argument("--description", help="Issue description (markdown supported)")
    parser.add_argument("--priority", choices=["urgent", "high", "medium", "low", "none"], help="Issue priority")
    parser.add_argument("--project", help="Project name (default: EstateMate Improvements)")
    parser.add_argument("--status", help="Issue status (e.g., 'In Progress', 'Done', 'Backlog', 'Todo')")
    parser.add_argument("--parent", help="Parent issue identifier (e.g., EST2-10)")
    parser.add_argument("--labels", help="Comma-separated label names (e.g., 'Bug,01-property-management')")
    parser.add_argument("--due-date", help="Due date in YYYY-MM-DD format")
    parser.add_argument("--assignee", help="Assignee name or email")
    parser.add_argument("--body", help="Comment body (required for --comment)")
    parser.add_argument("--label", help="Filter by label name (for --list)")
    parser.add_argument("--limit", type=int, default=25, help="Max results for --list (default: 25)")

    args = parser.parse_args()

    # Parse comma-separated labels
    label_list = [l.strip() for l in args.labels.split(",")] if args.labels else None

    if args.create:
        if not args.title:
            parser.error("--create requires --title")
        create_issue(
            args.title,
            args.description,
            args.priority,
            args.project,
            args.parent,
            label_list,
            args.due_date,
            args.assignee,
            args.status
        )

    elif args.update:
        update_issue(
            args.update,
            args.status,
            args.priority,
            args.title,
            args.description,
            args.project,
            args.parent,
            label_list,
            args.due_date,
            args.assignee
        )

    elif args.list:
        list_issues(
            args.status,
            args.project,
            args.priority,
            args.label,
            args.assignee,
            args.limit
        )

    elif args.add_labels:
        if not label_list:
            parser.error("--add-labels requires --labels")
        add_labels_to_issue(args.add_labels, label_list)

    elif args.remove_labels:
        if not label_list:
            parser.error("--remove-labels requires --labels")
        remove_labels_from_issue(args.remove_labels, label_list)

    elif args.comment:
        if not args.body:
            parser.error("--comment requires --body")
        add_comment(args.comment, args.body)

    elif args.archive:
        archive_issue(args.archive)

    elif args.get:
        get_issue(args.get)


if __name__ == "__main__":
    main()
