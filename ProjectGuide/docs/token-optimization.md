# Token Optimization

## Context levels

```text
Level 0: Issue + exact files
Level 1: Repo tree + relevant files
Level 2: Full module
Level 3: Compressed repo
Level 4: Full repo
```

## Repomix

```bash
npx repomix@latest --compress
npx repomix@latest --token-count-tree 100
npx repomix@latest --include-diffs
```

## Gitingest

```bash
pipx install gitingest
gitingest /path/to/repo
```
