# Skill Registry - MarketIntelligenceAgent

> Generated: 2026-05-08 | Mode: hybrid (engram + openspec)

## Project Context

- **Stack**: Python 3.11+, Streamlit, LangChain, ChromaDB, Polars
- **Architecture**: Clean Architecture
- **Testing**: pytest (18 test files), no integration/e2e
- **Quality**: pylint, mypy, black

## User-Level Skills

### SDD Workflow (Spec-Driven Development)

| Skill | Location | Description |
|-------|----------|-------------|
| sdd-init | `~/.config/opencode/skills/` | Initialize SDD context (THIS SKILL) |
| sdd-propose | `~/.config/opencode/skills/` | Create change proposals |
| sdd-spec | `~/.config/opencode/skills/` | Write specifications |
| sdd-design | `~/.config/opencode/skills/` | Create technical designs |
| sdd-tasks | `~/.config/opencode/skills/` | Break down into tasks |
| sdd-apply | `~/.config/opencode/skills/` | Implement changes |
| sdd-verify | `~/.config/opencode/skills/` | Verify implementation |
| sdd-archive | `~/.config/opencode/skills/` | Archive completed changes |
| sdd-explore | `~/.config/opencode/skills/` | Explore/investigate ideas |
| sdd-onboard | `~/.config/opencode/skills/` | Guided SDD walkthrough |

### Code Quality & Review

| Skill | Location | Description |
|-------|----------|-------------|
| judgment-day | `~/.config/opencode/skills/` | Parallel adversarial review |
| branch-pr | `~/.config/opencode/skills/` | PR creation workflow |
| issue-creation | `~/.config/opencode/skills/` | Issue creation workflow |

### Tool Creation

| Skill | Location | Description |
|-------|----------|-------------|
| skill-creator | `~/.config/opencode/skills/` | Create new AI skills |
| skill-registry | `~/.config/opencode/skills/` | Update skill registry |

## Project-Level Skills

**None detected** - Project has no `.claude/skills/`, `.agent/skills/`, or `skills/` directories.

## Project Conventions

**None detected** - Project has no AGENTS.md, CLAUDE.md, .cursorrules, or GEMINI.md.

## Relevant Skills for This Project

Based on detected stack (Python/Streamlit):

1. **sdd-*** (all phases) - Core SDD workflow
2. **judgment-day** - For complex reviews
3. **skill-creator** - If extending agent capabilities

> Note: `go-testing` skill is not relevant - this is a Python project, not Go.

## Sync Status

- ✅ `.atl/skill-registry.md` created
- ✅ Saved to engram: `skill-registry` topic