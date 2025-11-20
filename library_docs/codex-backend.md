# Codex Executor Backend

Codex is the default executor backend for ai-clean. Instead of running local
shell commands, the backend prints explicit instructions after each
`ai-clean apply` so you can apply the generated OpenSpec change inside Codex.

## Daily Workflow

1. Run `ai-clean apply <PLAN_ID>` locally to generate the OpenSpec change.
2. After the spec is written, the CLI prints a line such as:
   `Backend instructions: In Codex, run '/openspec-apply my-plan-id'.`
3. Copy the command into a Codex tab (or trigger the helper slash command
   described below). Codex handles `/openspec-apply` (or `/prompts:openspec-apply`).
4. Continue reviewing/test-running in Codex as you normally would.

The CLI also saves the backend metadata alongside the execution result so
`ai-clean changes-review` can remind reviewers how the change was applied.

## Customising Commands

The backend can be tweaked via config or env vars:

| Setting | Description | Default |
| --- | --- | --- |
| `executor_backend.type` | Backend implementation (`codex` only today). | `codex` |
| `executor_backend.command_prefix` | First command printed (e.g., `/openspec-apply`). | `/openspec-apply` |
| `executor_backend.prompt_hint` | Optional fallback command (e.g., `/prompts:openspec-apply`). | `/prompts:openspec-apply` |
| `AI_CLEAN_EXECUTOR_BACKEND` | Env override for backend type. |  |
| `AI_CLEAN_EXECUTOR_COMMAND_PREFIX` | Env override for the prefix string. |  |
| `AI_CLEAN_EXECUTOR_PROMPT_HINT` | Env override for the prompt hint string. |  |

Set the env vars before running `ai-clean apply` to experiment with custom Codex
commands or to disable the `/prompts:` hint entirely.

## Codex Slash Command Helper

See `library_docs/codex-slash-command-example.yaml` for a starter
`/code-butler-apply` definition. The template runs `ai-clean apply PLAN_ID` and
then invokes `/openspec-apply PLAN_ID`. Update the placeholders (repo path,
plan id prompt, etc.) to fit your Codex setup.
