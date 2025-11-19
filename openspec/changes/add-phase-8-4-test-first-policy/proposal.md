## Why
Make test execution visibility mandatory for /apply and review flows.

## What Changes
- Ensure /apply always records whether tests ran and their status in ExecutionResult.
- Have CLI output and /changes-review surface test status explicitly along error paths.
- Provide clear messages for failed applies or tests.

## Impact
- Users always see whether tests ran and passed.
- Failures are explicit and actionable.
