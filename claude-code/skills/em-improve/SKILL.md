---
name: em-improve
description: File a structured EstateMate product improvement
context: fork
allowed-tools: Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion
model: opus
---

# File an EstateMate product improvement

Takes raw observations (text, screenshots, loose thoughts) and structures them into rigorous, actionable improvement tickets in Linear.

**Target:** EST2 team > EstateMate Improvements project
**Labels available:** `Bug`, `Feature`, `Improvement` + module labels (`01-property-management` through `14-infrastructure`)

## Step 1: Collect the observation

Read any input the user has provided (text description, screenshot paths, URLs). If the user provides a screenshot path, read it with the Read tool to see the image.

If the input is insufficient, ask targeted questions using AskUserQuestion. You need at minimum:
- **What they observed** (the problem or idea)
- **Where in the product** (page, view, or feature area)

Optional but valuable:
- Screenshot or visual reference
- What they were trying to accomplish (user journey context)
- Who this affects (Ari's team? Demo audience?)

## Step 2: Classify the ticket

Determine the ticket type by analyzing the observation:

| Type | When to use |
|------|-------------|
| **Bug** | Something is broken, showing wrong data, or behaving unexpectedly |
| **Improvement** | Something works but could be better (UX, copy, performance, polish) |
| **Feature** | Something entirely new that doesn't exist yet |

Determine the module label by matching to these categories:

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

Determine priority:
- **Urgent**: Blocks demo or customer-facing workflows
- **High**: Noticeable quality issue, affects core experience
- **Medium**: Should be fixed but not blocking
- **Low**: Nice to have, polish item

## Step 3: Structure the ticket

Format the description using this exact template. Every section must be filled in (use "N/A" if truly not applicable, never leave blank):

```markdown
## Current behavior
[What happens now. Be specific: exact text shown, exact values displayed, exact behavior observed. Reference any screenshot.]

## Expected behavior
[What should happen instead. Be concrete - not "should work better" but "should show the actual monthly rent from the lease data".]

## Location
[Navigation path to reproduce: e.g., Portfolios > Birnbaum und Schwarzbaum > Brandenburgische Str 29 > Unit 3.OG links]
[URL path if known: e.g., /portfolios/123/properties/456]

## Impact
[Who is affected and how: e.g., "Ari's team sees wrong rent data during daily operations" or "Demo to Debbie would show broken KPIs"]

## Visual reference
[If screenshot was provided: "See attached screenshot" or describe what the screenshot shows]
[If no screenshot: "No screenshot provided - visual confirmation recommended"]

## Reproduction steps (for bugs)
1. Navigate to [location]
2. [Action taken]
3. Observe [incorrect behavior]

## Suggested approach (optional)
[Any ideas on how to fix, or design direction for improvements]
```

## Step 4: Present the structured ticket for review

Show the user the complete structured ticket before creating it. Display:
- **Title** (concise, starts with type prefix for bugs: "Bug: ...")
- **Type label** (Bug/Feature/Improvement)
- **Module label** (from the list above)
- **Priority** (urgent/high/medium/low)
- **Full description** (the structured template filled in)

Ask the user to confirm or adjust using AskUserQuestion:

```
"Ready to file this improvement?"
Options:
- "File it" - Create the issue as-is
- "Adjust" - Let me modify something first
- "Add more" - I have additional context to add
```

## Step 5: Create the Linear issue

**Find the scripts directory.** Look for `linear_operations.py` in these locations (in order):
1. `linear/` relative to the repo root (if working inside the estatemate-tools repo)
2. `~/estatemate-tools/linear/`
3. Any directory containing `linear_operations.py` with a sibling `linear_client.py`

Create the issue using:

```bash
python3 [SCRIPTS_DIR]/linear_operations.py --create \
  --title "[TITLE]" \
  --description "[STRUCTURED DESCRIPTION]" \
  --priority [PRIORITY] \
  --project "EstateMate Improvements" \
  --labels "[TYPE_LABEL],[MODULE_LABEL]"
```

After creation, output:
```
Filed: [EST2-XXX] [Title]
Labels: [type], [module]
Priority: [priority]
URL: [linear URL]
```

If the user has a screenshot file, remind them: "Attach your screenshot to the issue in Linear: [URL]"

## Step 6: Batch mode

If the user has multiple improvements to file, loop back to Step 1 after each ticket is created. Ask:

```
"Want to file another improvement?"
Options:
- "Yes, next one"
- "Done for now"
```

## Quality checklist (internal - verify before filing)

Before creating any ticket, verify:
- [ ] Title is specific and scannable (not "Fix the thing" but "Bug: Portfolio view shows 0 EUR for all Monatsmiete values")
- [ ] Current vs expected behavior are clearly separated
- [ ] Location is specific enough to navigate to the issue
- [ ] Impact explains WHY this matters (not just what's wrong)
- [ ] The right module label is applied (not just Bug/Feature/Improvement)
- [ ] Priority matches actual impact (not everything is urgent)
- [ ] Description would make sense to someone who has never used the product
- [ ] An LLM reading this ticket could understand the full context without additional information
