---
name: pencil
description: "Create, edit, and export .pen design files via the CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    category: creative
    tags: [Pencil, Design, UI, Figma, Design-to-Code, Canvas, pencil.dev]
    related_skills: [excalidraw, claude-design, popular-web-designs]
prerequisites:
  commands: [pencil, node]
---

# Pencil Skill

Optional skill — **not active until installed**:

```bash
hermes skills install official/creative/pencil
```

After install, scripts live under `~/.hermes/skills/creative/pencil/`. In prose
below, `{SKILL_DIR}` means that directory (or the repo path
`optional-skills/creative/pencil/` before install).

Drive [Pencil](https://pencil.dev) — an IDE-first design canvas that stores
designs as version-controlled `.pen` files — from Hermes through its CLI. You
can call Pencil's design tools directly (deterministic, no extra API key) or
hand Pencil a natural-language prompt and let its built-in agent generate a
design. This skill does **not** add a dependency to Hermes: the `pencil` binary
is a lazy runtime dependency you install only if you use this skill.

> Why the CLI and not an MCP server: Pencil's MCP server is embedded in its
> closed-source desktop app / IDE extension and auto-injected into specific
> hosts (Claude Code, Cursor, …). It exposes no public stdio command for a
> generic MCP host, so a true MCP wiring would require a bridge. The `pencil`
> CLI gives the same tool surface with zero bridge — Pencil's own CLI help even
> says *"Agents should use this mode to design with Pencil."*

## When to Use

- The user wants to create or edit a `.pen` design (screens, components,
  design systems) that lives in their repo.
- The user wants a design rendered to an image (PNG/JPEG/WEBP/PDF).
- The user wants to read an existing `.pen` file's structure, variables, or
  components to keep design and code in sync.

## When NOT to Use

- Quick throwaway diagrams (arch/flow/sequence) → use the `excalidraw` skill.
- Pure HTML/CSS mockups with no design file → use `popular-web-designs` /
  `claude-design`.
- The user is editing a Figma `.fig` file → that's a different product
  (OpenPencil); this skill targets `pencil.dev` `.pen` files.

## Prerequisites

- **Node.js** and the Pencil CLI: `npm install -g @pencil.dev/cli`. Docs say
  Node 18+, but newer CLI builds need **Node 22+** — upgrade if you hit
  `ERR_REQUIRE_ESM`. No sudo? `npm install --prefix ~/.local`.
- **Auth is required for BOTH modes.** `pencil login` (stores
  `~/.pencil/session-cli.json`) or set `PENCIL_CLI_KEY`. Pencil has no offline
  mode — even headless `pencil interactive` refuses to start unauthenticated.
  Verify with `pencil status`.
- **Agent mode (Mode B)** additionally needs an agent key, e.g.
  `ANTHROPIC_API_KEY` (or `PENCIL_AGENT_API_KEY`).
- Run the preflight check first via the `terminal` tool:
  `python {SKILL_DIR}/scripts/pencil_doctor.py`

## How to Run

Two modes. Prefer **Mode A** when Hermes is doing the thinking; use **Mode B**
to delegate generation to Pencil's own agent.

### Mode A — Direct tool control (recommended, no agent key)

Hermes decides the design and calls Pencil's MCP tools through the
`pencil interactive` REPL, driven non-interactively by `scripts/pencil_repl.py`
via the `terminal` tool. Always read the live schema first:

```bash
python {SKILL_DIR}/scripts/pencil_repl.py --out design.pen \
  --cmd 'get_editor_state({ include_schema: true })'
```

Then issue tool calls (`batch_get`, `batch_design`, `get_screenshot`, …). The
wrapper appends `save()` (headless) and `exit()` automatically:

```bash
python {SKILL_DIR}/scripts/pencil_repl.py --out design.pen \
  --cmd 'batch_design({ operations: "hero=I(document,{type:\"frame\",name:\"Hero\",x:0,y:0,width:1440,height:900,fill:\"#0A0A0A\"})" })' \
  --cmd 'get_screenshot({ nodeId: "hero" })'
```

Connect to a running Pencil desktop app instead (changes apply live):

```bash
python {SKILL_DIR}/scripts/pencil_repl.py --app desktop --in design.pen \
  --cmd 'batch_get({ patterns: [{ reusable: true }] })'
```

See `references/mcp-tools.md` for the tool list and the `batch_design` DSL.

### Mode B — Prompt-driven generation (delegates to Pencil's agent)

```bash
# New design from a prompt
pencil --out landing.pen --prompt "Create a SaaS landing page with hero, features, pricing" --agent claude

# Modify an existing design
pencil --in landing.pen --out landing-v2.pen --prompt "Add a dark footer with social links"

# Attach reference images (repeatable)
pencil --out ui.pen --prompt "Match this style" -f ./ref.png

# Export to an image
pencil --in landing.pen --export landing.png --export-scale 2 --export-type png
```

## Quick Reference

| Goal | Command |
| --- | --- |
| Preflight check | `python .../scripts/pencil_doctor.py` |
| Read document schema + DSL | REPL: `get_editor_state({ include_schema: true })` |
| List design-system components | REPL: `batch_get({ patterns: [{ reusable: true }] })` |
| Mutate the design | REPL: `batch_design({ operations: "..." })` |
| Screenshot a node | REPL: `get_screenshot({ nodeId: "..." })` |
| Generate from a prompt | `pencil --out x.pen --prompt "..." --agent claude` |
| Export an image | `pencil --in x.pen --export x.png --export-type png` |
| List models | `pencil --list-models` |

## Procedure

1. **Preflight.** Run `pencil_doctor.py`. If `pencil` is missing, tell the user
   to `npm install -g @pencil.dev/cli`; if unauthenticated, `pencil login`.
2. **Pick the file.** New design → choose an output path ending in `.pen`.
   Editing → pass the existing file as `--in`.
3. **Inspect first (Mode A).** Call `get_editor_state({ include_schema: true })`
   and, when editing, `batch_get` to learn the current node tree and the exact
   `batch_design` DSL for this Pencil version.
4. **Make changes.** Issue `batch_design` operations (Mode A) or a prompt
   (Mode B). Keep `batch_get` `readDepth` ≤ 3 to avoid flooding context.
5. **Verify** (see below), then **commit** the `.pen` file with the related
   code change so design and implementation move together in Git.

## Pitfalls

- **Auth is mandatory.** There is no offline path; both modes refuse to run
  without a `pencil login` session or `PENCIL_CLI_KEY`.
- **`batch_design` binding names are per-call.** A name you bind (e.g.
  `hero=I(...)`) only exists within that single `batch_design` call. To touch
  the node in a later call, reference it by its real node id (from the call's
  output or `batch_get`) — do **not** reuse the binding name across calls.
  Combine related inserts/edits into one `batch_design` where possible.
- **Pencil must be running for `--app` mode.** App mode connects over a local
  socket to the desktop app / extension. If it isn't running, use headless
  mode (`--out`, no `--app`).
- **Don't guess the `batch_design` DSL.** Operation letters/args can change
  between versions — read them from `get_editor_state`, not from memory.
- **Multi-line stdin: use `--cmds-file`, not inline escaping.** `batch_design`
  operations are strings of JS-object literals; piping them through a shell
  `printf`/`--cmd '...'` with escaped quotes is fragile. For anything
  non-trivial, write the REPL calls to a file and pass `--cmds-file`.
- **Mode B costs tokens and needs an agent key.** It runs Pencil's own LLM
  agent. For precise, free, deterministic edits prefer Mode A.
- **`.pen` is the source of truth, in your repo.** Treat it like code: review
  the diff, commit it alongside the implementation.

## Verification

- After a mutation, run `get_screenshot({ nodeId })`, save the PNG, and read it
  back with Hermes's `vision_analyze` / `read_file` to confirm the result.
- Re-run `batch_get` / `snapshot_layout` to confirm the node tree and bounds.
- Confirm the `.pen` file was written (headless `save()` succeeded) before
  committing.
