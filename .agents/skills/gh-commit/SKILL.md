---
name: gh-commit
description: "Stage, review, commit, rebase, and push with Conventional Commits and user approval gates"
license: MIT
compatibility: opencode
---

## What I do

Walk through the complete commit pipeline: show the diff, analyse and classify changes, propose a Conventional Commits message, get user approval, commit, rebase, and push.

## When to use me

Use this when the user asks to commit changes, stage files, or push a branch. Can also be used as a sub-skill invoked by broader workflows (e.g. github-issues) for the commit phase.

## Procedure

### 1. Load project context

Before analysing the diff, load the project's conventions:

1. Read `AGENTS.md` — it lists every `.ai/` instruction file.
2. Read **all** `.ai/` files referenced there.

Do **not** skip this step.

### 2. Show and analyse the diff

```
git diff HEAD --stat
```

Present a summary of changed files to the user. Then show the full diff:

```
git diff HEAD
```

Analyse the changes and classify the commit type:

- **`feat`** — a new feature for the user (not a new feature for build script)
- **`fix`** — a bug fix
- **`chore`** — maintenance, refactoring, tooling, dependencies, docs

Determine a scope if the changes are focused on a single module or area.

### 3. Propose a commit message

Draft a commit message in the **imperative mood** with Conventional Commits format:

```
<type>(<scope>): <short description>

<optional body>

Closes #<N>
```

- Use the **type** determined from the diff analysis
- Use the **branch prefix** as a hint for the type if available (`fix/`, `feat/`, `chore/`)
- Include `Closes #<N>` if an issue number is known
- If the changes are trivial or no issue is linked, omit the `Closes` trailer

### 4. Get user approval

Ask the user:

*"Shall I commit these changes with the following message? [y/n / edit]"*

```
<commit-message>
```

- **`y`** → proceed to step 5
- **`edit`** → prompt the user for their message and use that
- **`n`** → stop and report back

Do **not** proceed past this point without explicit approval.

### 5. Commit

```bash
git add -A
git commit -m "<message>"
```

### 6. Fetch and rebase

Detect the correct upstream remote. If `upstream` exists, rebase against the canonical repo (fork workflow). Otherwise fall back to `origin` (direct contributor):

```bash
DEFAULT_BRANCH="develop"

if git remote get-url upstream > /dev/null 2>&1; then
  TARGET_REMOTE="upstream"
else
  TARGET_REMOTE="origin"
fi

git fetch "$TARGET_REMOTE" "$DEFAULT_BRANCH"
git rebase "$TARGET_REMOTE/$DEFAULT_BRANCH"
```

If there are conflicts, **stop and alert the user**. Do not attempt to resolve conflicts automatically. If the user resolves them manually, re-run tests to re-verify.

### 7. Get push approval

Ask the user:

*"Branch `<branch-name>` is rebased and ready. Shall I push to `origin`? [y/n]"*

- **`y`** → proceed to step 8
- **`n`** → stop and report back

### 8. Push

```bash
git push origin <branch-name>
```

Notify the user the branch is pushed and ready.
