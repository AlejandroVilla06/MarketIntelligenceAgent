# Proposal: Migrate npm to pnpm Workspaces

## Intent

Migrate from npm to pnpm for strict dependency resolution (eliminates phantom deps by design), 2-3x faster installs via content-addressable store, disk efficiency across projects, and monorepo readiness for future workspace packages.

## Scope

### In Scope
- Root `pnpm-workspace.yaml` pointing to `frontend/`
- Root `package.json` with convenience scripts (`dev`, `build`, `lint`)
- `.npmrc` with `auto-install-peers=true` and `strict-peer-dependencies=false`
- Delete `frontend/package-lock.json` and `frontend/node_modules/`
- Run `pnpm install` to generate `pnpm-lock.yaml`
- Verify dev server and production build work identically

### Out of Scope
- Migrating Python backend to any workspace (it's Python)
- Adding new packages or refactoring existing code
- Creating additional workspace packages (future work)

## Capabilities

### New Capabilities
- `pnpm-monorepo`: pnpm workspace configuration, root scripts, and .npmrc settings

### Modified Capabilities
- None — no spec-level behavior changes for existing capabilities

## Approach

1. Create three root config files (`pnpm-workspace.yaml`, `package.json`, `.npmrc`)
2. Delete npm artifacts (`package-lock.json`, `node_modules/`)
3. Run `pnpm install` to generate lockfile and symlink tree
4. Verify with `pnpm dev` and `pnpm build` — output must be identical

No changes needed to `frontend/package.json` — pnpm reads it as-is.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pnpm-workspace.yaml` | New | Workspace definition pointing to `frontend/` |
| `package.json` (root) | New | Convenience scripts delegating to frontend |
| `.npmrc` | New | Peer dep handling and store config |
| `frontend/package-lock.json` | Removed | Replaced by pnpm-lock.yaml |
| `frontend/node_modules/` | Removed | Re-symlinked by pnpm store |
| `frontend/pnpm-lock.yaml` | New | pnpm lockfile (auto-generated) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| shadcn CLI expects npm | Low | Use `pnpm dlx shadcn` or add `packageManager` field |
| Peer dep warnings block install | Low | `auto-install-peers=true` in `.npmrc` |
| Windows store path issues | Very low | pnpm v10 handles Windows correctly |

## Rollback Plan

1. Delete root `package.json`, `pnpm-workspace.yaml`, `.npmrc`, `pnpm-lock.yaml`
2. Run `npm install` inside `frontend/`
3. Restores `package-lock.json` and `node_modules/`

## Dependencies

- pnpm v10.32.1 already installed globally
- Node v24.14.0

## Success Criteria

- [ ] `pnpm install` completes without errors
- [ ] `pnpm dev` starts the Next.js dev server
- [ ] `pnpm build` produces identical output to previous npm build
- [ ] All imports resolve (no phantom dependency errors)
- [ ] `package-lock.json` removed, `pnpm-lock.yaml` created at root
