# AGENTS.md

## Chat

- Answer in the language of the user's current prompt unless instructed otherwise.
- Never use the em dash ('—'). Use a hyphen ('-') instead.
- Be concise. Do not expand explanations more than necessary.
- Prefer straight apostrophes (') over typographic apostrophes (’) in contractions and possessives (e.g. I'm, we're, user's).

Shortcuts (always respond using a Writing Block with `variant="standard"`):

- `wr:` or `wr` - Provide feedback on whether the following text is well written. Keep the response in the same language, improve naturalness and clarity, and preserve the original meaning.
- `tr:` or `tr` - Translate the following text into English if it is in Spanish, or into Spanish otherwise. Include brief examples or usage context when helpful.
- `def:` or `def` - Explain the meaning of the following word or expression in the same language, ideally with examples.
- `re:` or `re` - Provide multiple natural ways to express the given word, phrase, or idea. First, show alternatives in the original language, then provide equivalent expressions in the other language. Include brief notes on nuance, tone, or common usage when helpful.

## Work

- Write commit messages using Conventional Commits (e.g. `feat: ...`). Keep them short and never add your agent name as a co-author unless explicitly requested.
- When creating new branches, use conventional branch names (e.g. `feat/calendar`, `fix/button`, `chore/tooling...`).
- When fixing a bug, first reproduce it in an end-to-end scenario that closely matches how an end user experiences it. Base the fix on the reproduced behavior.
- Point out incorrect assumptions, mistakes, or misunderstandings when they affect the solution. Do not validate incorrect conclusions.
- When making technical decisions, prioritize correctness, simplicity, robustness, scalability, and long-term maintainability over implementation effort, unless the user explicitly asks for the quickest or lowest-cost solution.
- Preserve the user's existing coding style unless there is a clear reason to change it.
- Keep changes focused. Avoid unrelated refactors or drive-by improvements unless they are necessary to implement the requested change.
- Avoid duplicating logic, component structure, or styles. Extract shared code when duplication is intentional and likely to be maintained together, but do not introduce unnecessary abstractions for one-off cases.
