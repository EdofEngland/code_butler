## Why
Construct the configured SpecBackend from ai-clean.toml with clear errors on unsupported types.

## What Changes
- Read ai-clean.toml to determine spec_backend type (the config must explicitly declare a supported backend value such as "openspec").
- Instantiate the appropriate SpecBackend implementation or error clearly when unsupported.
- Validate configuration so mis-typed backend names surface early.

## Impact
- Spec backend selection is deterministic and configurable.
- Users get clear feedback for unsupported backends.
