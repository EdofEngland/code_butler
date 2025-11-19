## Why
Persist spec payloads as readable YAML files with stable naming under .ai-clean/specs/.

## What Changes
- Implement write_spec(spec, directory) to create files named {spec.id}.openspec.yaml or similar stable pattern.
- Serialize SpecChange payload to YAML under .ai-clean/specs/.
- Ensure each spec file covers a single small change without merging multiple topics.

## Impact
- Spec files become inspectable artifacts before execution.
- Naming is predictable for later retrieval.
