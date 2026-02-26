# EstateMate product feedback tools

## Why this exists

Now that the MVP is live, we need a structured way to capture what's working and what isn't. Ari uses the product daily with his team across 1,600 units - he sees things nobody else will. Christof needs those observations to land as clear, actionable tickets he can prioritize and build from.

This repo contains the tooling to make that loop work. It connects to Linear, where we track all product improvements. There are two ways to use it: a Python CLI for direct ticket management, and a Claude Code skill that takes raw observations and structures them automatically.

## How things fit together

**The flow:** You observe something in the product (a bug, an idea, a rough "this feels off") -> you submit it -> it lands in Linear as a structured ticket -> Christof picks it up.

**Where tickets go:** Linear > Estatemate-Product team (EST2) > EstateMate Improvements project.

**Every ticket gets two labels:** a type (Bug, Feature, or Improvement) and a module (which part of the product it touches, like `01-property-management` or `03-financial-intelligence`). Christof filters by module and priority to plan his sprints.

## What's in here

```
estatemate-tools/
├── README.md                              # This file - start here
├── linear/
│   ├── linear_client.py                   # Handles API auth and connectivity
│   └── linear_operations.py               # Create, update, list, comment on tickets
└── claude-code/
    └── skills/
        └── em-improve/
            └── SKILL.md                   # AI skill that structures tickets for you
```

## Onboarding sequence

Follow these steps in order. The whole setup takes about 10 minutes.

### Step 1: Clone this repo

```bash
git clone https://github.com/anarolabs/estatemate-tools.git
cd estatemate-tools
```

### Step 2: Make sure you have Python

You need Python 3.8 or higher. No additional packages - everything uses Python's standard library.

```bash
python3 --version
```

If this shows 3.8+ you're good. If not, install Python from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python3`).

### Step 3: Get your Linear API key

1. Open [Linear](https://linear.app) and log in
2. Go to **Settings** (gear icon, bottom-left) > **API** > **Personal API keys**
3. Click **Create key**
4. Label it something like "CLI scripts"
5. Copy the key - it starts with `lin_api_`

This key is personal to you. Don't share it or commit it to the repo.

### Step 4: Create your credentials file

The scripts read your API key from a local file that stays outside the repo (so it's never committed).

```bash
mkdir -p ~/.linear_api
```

Create the file `~/.linear_api/estatemate-product-credentials.json` with your API key:

```json
{
  "api_key": "lin_api_YOUR_KEY_HERE",
  "team_id": "placeholder",
  "team_key": "EST2"
}
```

You'll fill in the real `team_id` in the next step.

### Step 5: Look up your team ID

Run the built-in helper to list all teams your API key can access:

```bash
python3 linear/linear_client.py --teams
```

You'll see output like:

```
Teams you have access to:
------------------------------------------------------------
  Key: EST2        Name: Estatemate-Product              ID: abc123...
------------------------------------------------------------
```

Copy the **ID** value for the team with key **EST2** and paste it into your credentials file as the `team_id`.

### Step 6: Verify the connection

```bash
python3 linear/linear_operations.py --list --limit 5
```

If you see a JSON array of issues, you're set up. If you see an error, check the [troubleshooting section](#troubleshooting) below.

### Step 7 (optional): Install the Claude Code skill

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), you can install the `/em-improve` skill. This is the fastest way to file tickets - you describe what you see in plain language and Claude handles the classification, formatting, and filing.

```bash
mkdir -p ~/.claude/skills/em-improve
cp claude-code/skills/em-improve/SKILL.md ~/.claude/skills/em-improve/SKILL.md
```

Then in Claude Code, type `/em-improve` and describe what you observed. That's it.

---

## Day-to-day usage

Once you're set up, here's how the two workflows look in practice.

### Option A: Use `/em-improve` in Claude Code (recommended)

This is the low-friction path. You don't need to think about labels, priority, or formatting.

1. Open Claude Code
2. Type `/em-improve`
3. Say what you saw:
   - "The rent column shows 0 EUR for everything on Brandenburgische Str"
   - "I want a way to bulk-upload documents for a whole property at once"
   - Drop a screenshot path and say "this looks wrong"
4. Claude structures it, classifies it, shows you the ticket for review
5. Confirm and it's filed to Linear

The skill handles type classification, module labeling, priority, and the full ticket template. You just provide the observation.

### Option B: Use the scripts directly

For when you want more control, or you're already in the terminal.

**Create a ticket:**

```bash
python3 linear/linear_operations.py --create \
  --title "Bug: Portfolio shows 0 EUR for Monatsmiete" \
  --priority high \
  --project "EstateMate Improvements" \
  --labels "Bug,01-property-management" \
  --description "## Current behavior
Portfolio view shows 0 EUR for all Monatsmiete values.

## Expected behavior
Should show the actual monthly rent from the lease data.

## Location
Portfolios > Birnbaum und Schwarzbaum > Overview

## Impact
Team sees wrong rent data during daily operations."
```

**List issues:**

```bash
# Everything recent
python3 linear/linear_operations.py --list

# Just bugs
python3 linear/linear_operations.py --list --label "Bug"

# High priority, not started
python3 linear/linear_operations.py --list --status "Todo" --priority high

# What Christof is working on
python3 linear/linear_operations.py --list --assignee "Christof" --status "In Progress"
```

**Update, comment, manage:**

```bash
# Move to in progress
python3 linear/linear_operations.py --update EST2-42 --status "In Progress"

# Add context
python3 linear/linear_operations.py --comment EST2-42 --body "This also affects the export PDF."

# Bump priority
python3 linear/linear_operations.py --update EST2-42 --priority urgent

# Full details on a ticket
python3 linear/linear_operations.py --get EST2-42

# Add/remove labels
python3 linear/linear_operations.py --add-labels EST2-42 --labels "urgent"
python3 linear/linear_operations.py --remove-labels EST2-42 --labels "urgent"

# Archive something that's no longer relevant
python3 linear/linear_operations.py --archive EST2-42
```

---

## Reference

### Ticket template

When creating tickets (manually or via scripts), use this structure:

```markdown
## Current behavior
[What happens now - be specific about exact text, values, behavior]

## Expected behavior
[What should happen instead - be concrete, not vague]

## Location
[Navigation path: e.g., Portfolios > Portfolio Name > Property > Unit]

## Impact
[Who is affected and why it matters]

## Visual reference
[Screenshot description or "No screenshot provided"]

## Reproduction steps (for bugs)
1. Navigate to [location]
2. [Action taken]
3. Observe [incorrect behavior]

## Suggested approach (optional)
[Ideas on how to fix or design direction]
```

### Type labels (pick one per ticket)

| Type | When to use |
|------|-------------|
| **Bug** | Something is broken, shows wrong data, or behaves unexpectedly |
| **Improvement** | Something works but could be better (UX, copy, performance, polish) |
| **Feature** | Something entirely new that doesn't exist yet |

### Module labels (pick one per ticket)

| Label | Covers |
|-------|--------|
| `00-foundation` | Auth, navigation, layout, theming, i18n |
| `01-property-management` | Properties, units, tenants, leases, hierarchy |
| `02-document-management` | DMS, document upload, OCR, classification |
| `03-financial-intelligence` | Rent tracking, forecasts, KPIs, cashflow |
| `04-workflow-engine` | Approval flows, task routing, automation |
| `05-treasury-liquidity` | Cash planning, liquidity dashboards |
| `06-banking-integration` | Bank connections, PSD2, reconciliation |
| `07-approval-system` | Invoice approvals, signature workflows |
| `08-reports` | Dashboards, PDF export, report builder |
| `09-alerts` | Notifications, reminders, triggers |
| `10-user-management` | Roles, permissions, user accounts |
| `11-multi-tenancy` | Data segregation, tenant isolation |
| `12-compliance-security` | Audit trail, GoB, data retention |
| `13-data-migration` | M-Files import, data onboarding |
| `14-infrastructure` | Hosting, deployment, performance |
| `calculations` | Financial formulas, calculation engine |

### Priority

| Priority | Meaning |
|----------|---------|
| Urgent | Blocks a demo, customer-facing workflow, or MVP rollout |
| High | Noticeable quality issue, affects core experience |
| Medium | Should be fixed but not blocking |
| Low | Nice to have, polish item |

---

## Troubleshooting

**"CREDENTIALS_MISSING" error**
Your credentials file doesn't exist or is in the wrong location. It should be at `~/.linear_api/estatemate-product-credentials.json`. Re-run steps 4-5 above.

**"AUTH_ERROR: Invalid or expired API key"**
Your API key is wrong or was revoked. Generate a new one in Linear > Settings > API > Personal API keys.

**"Label not found" error**
The label name doesn't match what's in Linear. Labels use case-insensitive partial matching, so `"Bug"` will match `"Bug"` and `"property"` will match `"01-property-management"`. Double-check spelling.

**"Project not found" error**
Make sure you're using `--project "EstateMate Improvements"` (the exact project name in Linear).

**Python version issues**
These scripts need Python 3.8+. Check with `python3 --version`. No pip install needed - everything uses the standard library.

**"NETWORK_ERROR"**
Check your internet connection. Linear's API is at `https://api.linear.app/graphql` - make sure it's reachable.
