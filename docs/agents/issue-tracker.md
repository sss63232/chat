# Issue tracker: Azure DevOps (MMM)

Issues, tickets and specs for this repo live as **Azure DevOps work items**, not GitHub issues.

- **Organization**: `s63232`
- **Project**: `MMM`
- **Web URL**: https://s63232.visualstudio.com/MMM (equivalently https://dev.azure.com/s63232/MMM)
- **Process template**: Agile — features are `User Story`, defects are `Bug`, subtasks are `Task`

> **Do not run `gh issue ...` in this repo.** The git remote is GitHub
> (`git@github.com:sss63232/chat.git`) but work tracking is in Azure DevOps.
> Code review happens on GitHub; tickets live in ADO. An agent that infers the
> tracker from `git remote -v` will get this wrong.

## Access: the Azure DevOps MCP server

All work item operations go through Microsoft's official MCP server,
[`microsoft/azure-devops-mcp`](https://github.com/microsoft/azure-devops-mcp).

Server config (organization is passed as the sole argument):

```json
{
  "mcpServers": {
    "ado": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "s63232"]
    }
  }
}
```

Authentication is interactive on first use: sign in with a Microsoft account
that has access to the `s63232` organization. Passing
`"--authentication", "azcli"` in `args` delegates to an `az login` session
instead; that requires the Azure CLI, which is **not currently installed** on
this machine.

If the `ado` MCP tools are not available in a session, stop and say so rather
than falling back to `gh issue` or guessing. There is no CLI fallback
configured for this repo.

## Conventions

The MCP tools take an `operation` parameter, so each row below is a
tool + operation pair.

- **Create a ticket**: `wit_work_item_write` / `create` — type `User Story` for
  features, `Bug` for defects, in project `MMM`.
- **Create a subtask under a parent**: `wit_work_item_write` / `add_child`.
- **Read a ticket**: `wit_work_item` / `get` by ID. For several at once,
  `wit_work_item` / `get_batch`.
- **Read the discussion**: `wit_work_item` / `list_comments`. History is
  `wit_work_item` / `list_revisions`.
- **List / query tickets**: `wit_query` / `wiql` with an ad-hoc WIQL query, e.g.
  filtering on `[System.Tags] CONTAINS 'needs-triage'` and
  `[System.State] <> 'Closed'`. Saved queries are `wit_query` / `get_results`.
- **Comment**: `wit_work_item_comment_write` / `add`.
- **Apply / remove triage tags**: `wit_work_item_write` / `update` on the
  `System.Tags` field. Tags are semicolon-separated in ADO, and an update
  **replaces** the whole field — read the current tags first and write back the
  merged set, or you will silently drop existing tags.
- **Close**: `wit_work_item_write` / `update` setting `System.State` to
  `Closed` (Agile template), plus a comment explaining why.
- **Work item type metadata** (valid states, required fields):
  `wit_work_item` / `get_type`.

## When a skill says "publish to the issue tracker"

Create an ADO work item with `wit_work_item_write` / `create`.

## When a skill says "fetch the relevant ticket"

`wit_work_item` / `get` for the fields, then `wit_work_item` / `list_comments`
for the discussion. Both are usually needed; the body alone often omits the
decisions.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if external PRs should enter
the triage queue; `/triage` reads this flag.)_

Note the split if you ever turn this on: PRs arrive on **GitHub**
(`sss63232/chat`, via `gh pr ...`) while tickets live in **ADO**. There is no
automatic link between the two. `wit_work_item_link_write` /
`link_to_pull_request` can attach an ADO-hosted PR to a work item, but it does
not understand GitHub PRs, so the association has to be a URL in the work item
body or a comment.

## Wayfinding operations

Used by `/wayfinder`. The **map** is one work item with **child** work items as
tickets.

- **Map**: a `Feature` work item tagged `wayfinder:map`, holding the Notes /
  Decisions-so-far / Fog body.
- **Child ticket**: a `User Story` (or `Bug`) created with
  `wit_work_item_write` / `add_child` against the map, which establishes the
  native `System.LinkTypes.Hierarchy-Forward` parent/child link. Tag with
  `wayfinder:<type>` (`research` / `prototype` / `grilling` / `task`). Once
  claimed, set `System.AssignedTo` to the driving dev.
- **Blocking**: use ADO's native dependency link, not a body convention.
  `wit_work_item_link_write` / `link` with link type
  `System.LinkTypes.Dependency-Reverse` on the blocked item pointing at its
  blocker (equivalently `Dependency-Forward` from blocker to blocked). A ticket
  is unblocked when every predecessor's `System.State` is `Closed` (or
  `Removed`).
- **Frontier query**: `wit_query` / `wiql` for the map's open children — a
  `WorkItemLinks` query from the map over `Hierarchy-Forward`, keeping children
  whose `System.State` is not `Closed`/`Removed`. Then drop any with an
  unclosed predecessor or a non-empty `System.AssignedTo`; first in map order
  wins.
- **Claim**: `wit_work_item_write` / `update` setting `System.AssignedTo` to
  yourself, and `System.State` to `Active`. This is the session's first write.
- **Resolve**: `wit_work_item_comment_write` / `add` with the answer, then
  `wit_work_item_write` / `update` to `State = Closed`, then append a context
  pointer to the map's Decisions-so-far.
