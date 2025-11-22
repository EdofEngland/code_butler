## 1. Deliverables

- [ ] Implement `write_spec(spec: ButlerSpec, directory: Path) -> Path`:

  - [ ] File name: `{spec.id}.butler.yaml`.
  - [ ] Directory: `.ai-clean/specs/` by default.
  - [ ] Content: YAML serialization of the `ButlerSpec`.

- [ ] Guardrails:

  - [ ] Each spec file corresponds to a **single, small change** in a single file.
  - [ ] No multi-topic specs.
