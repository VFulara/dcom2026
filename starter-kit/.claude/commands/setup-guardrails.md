Add a PreToolUse hook to `.claude/settings.json` that blocks writes to credential files, then create the security-reviewer subagent.

**Hook requirements:**
- Fires on Write and Edit tool calls
- Parses the file path from the tool input JSON (stdin)
- Blocks with exit code 2 if the filename matches: `*.env*`, `*.pem`, `*.key`, `credentials*`
- Prints exactly this message to stderr: `BLOCKED: Credential file modification requires explicit human approval`
- Implemented as an inline `python3 -c` script in the `command` field (no separate file needed)
- Add it to the existing `"hooks"` object in `.claude/settings.json` — do not remove any existing permissions

**Subagent requirements:**
- File: `.claude/agents/security-reviewer.md`
- Frontmatter: `name: security-reviewer`, `model: claude-sonnet-4-6`, `description: Reviews code for security vulnerabilities against CLAUDE.md rules. Use before every merge.`
- Tools: Read, Glob, Bash (read-only — no Edit or Write)
- System prompt checks for: hardcoded secrets or tokens, string concatenation in CQL/SQL/OData URLs, missing input validation on service boundaries, unauthenticated write endpoints, PII or request bodies in logs, `eval()` or `Function()` calls
- For each check category, report either `PASS` (no issues) or list findings with: file path, line number, rule violated, suggested fix
- Model must be restricted to read-only Bash (grep, cat, ls — no npm, no git write operations)

After creating both, print a confirmation that lists the two files created and what each does.
