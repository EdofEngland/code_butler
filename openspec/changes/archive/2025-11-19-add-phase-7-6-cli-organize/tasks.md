## 1. Implementation
- [x] 1.1 List organize_candidate findings from the analyzer.
  - [x] 1.1.1 Extend the CLI with `ai-clean organize [PATH]` that runs the organizer analyzer and prints destination suggestions, file counts, and line ranges.
  - [x] 1.1.2 Allow `--max-files` to filter overly large candidates per config.
- [x] 1.2 Support selection of candidates and build move plans for each.
  - [x] 1.2.1 Provide selection options (interactive or `--ids`), then call `plan_file_moves` via orchestrator to produce plans with constrained file sets.
  - [x] 1.2.2 Persist each plan and show the destination plus list of files to move, reminding users no content edits occur.
- [x] 1.3 Offer immediate apply or storing while keeping moves small and content untouched.
  - [x] 1.3.1 Prompt per plan whether to run `/apply` immediately; if yes, call the shared helper, otherwise exit after printing the plan file path.
  - [x] 1.3.2 Add tests ensuring the command enforces file limits and never modifies files unless apply is triggered.
