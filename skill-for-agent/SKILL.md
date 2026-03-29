---
name: skill-for-agent
description: Run the local rule-based PRD reviewer against a Markdown or DOCX file path and return a Markdown or JSON report. Use when the user wants an Agent-accessible local review instead of the Web app flow.
---

# Skill For Agent

Use this skill when the user wants a local, deterministic PRD review from a file path.

## Input contract

- Accept only a local file path to a `.md` or `.docx` PRD
- If the path is already available in the conversation, reuse it directly
- Do not ask the user to paste the full PRD text unless the file is unavailable

## Command

Install dependencies first:

```bash
pip install -r /Users/ann/skill-for-agent/requirements.txt
```

Run:

```bash
python3 /Users/ann/skill-for-agent/scripts/run_review.py <prd_file> --preset normal --format markdown
```

Optional:

- `--preset normal|p0_critical|innovation`
- `--format markdown|json`
- `--output <file>`

## Response pattern

1. Validate the path and extension
2. Run the script
3. Summarize the key recommendation and top issues
4. If `--output` was used, mention the generated file path
