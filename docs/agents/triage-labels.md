# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those
roles to what this repo's tracker actually uses.

Azure DevOps has no "labels". The closest analogue is the free-form
**`System.Tags`** field, so the five roles are tags, and the tag string is
identical to the role name.

| Label in mattpocock/skills | Tag in our tracker | Meaning                                  |
| -------------------------- | ------------------ | ---------------------------------------- |
| `needs-triage`             | `needs-triage`     | Maintainer needs to evaluate this item   |
| `needs-info`               | `needs-info`       | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`  | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`  | Requires human implementation            |
| `wontfix`                  | `wontfix`          | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), set the
corresponding tag from this table.

## Tags are not the State field

Triage tags are orthogonal to `System.State` (`New` / `Active` / `Resolved` /
`Closed` in the Agile template). A tag records *what triage decided*; the state
records *where the work is*. Setting `wontfix` does not close the item — close
it separately, as `docs/agents/issue-tracker.md` describes.

## Reading and writing tags safely

ADO stores tags as a single semicolon-separated string, and
`wit_work_item_write` / `update` **replaces** the whole `System.Tags` value.
Always read the current tags, merge, then write back. Blind writes drop
whatever else was on the item.

To filter by tag in WIQL, use `CONTAINS`, not `=`:

```sql
SELECT [System.Id], [System.Title]
FROM WorkItems
WHERE [System.TeamProject] = 'MMM'
  AND [System.Tags] CONTAINS 'needs-triage'
  AND [System.State] <> 'Closed'
```

ADO creates tags on first use, so no setup step is needed — but it also means a
typo silently creates a new tag rather than failing. Tag matching is
case-insensitive on write, and ADO keeps whichever casing the tag was first
created with.

Edit the middle column if you later adopt different strings.
