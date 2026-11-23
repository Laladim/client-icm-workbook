# Client ICM Workbook

Give a new digital-marketing client a clear home for its business context, brand, customer evidence, offers, channels, performance and source monitoring. Decisions and source references live in files so Claude Code, Codex or another team member can find the right context without the original chat.

## Start with your assistant

Open this repository and paste:

```text
Read SETUP.md and guide me through installing and onboarding a private client ICM workspace.
```

The agent installs a private client folder outside this public repository, reads the material you already have, and asks up to three missing questions at a time. You review the exact client brief before folder generation, then review the exact workspace before acceptance. The default is local drafts only.

## What is included

- A 97-question guided onboarding workbook covering business scope, SOPs, company onboarding, staff/delegation, existing customers, official website/social accounts, brand strategy/identity/marketing, audience, messages, platform strategy, demo calls, newsletter/blog/video/LinkedIn data, case studies, testimonials and one-line praise.
- Additional questions for commercial outcomes, budgets, deliverables, approvals, offers and limitations, SEO/AI visibility, paid media, website conversion, accessibility, privacy, source freshness, sales feedback, maintenance and handover.
- Seven organized client areas, with an ordered onboarding record and one answer-to-file map.
- Product/service change coverage that distinguishes internal updates, local assets and actual online evidence.
- A portable Python standard-library installer/checker, explicit human approval hashes, meaningful refusal tests and fictional setup examples.
- Shared Claude Code/Codex entries. No company-specific accounts, decisions, private data, global settings, connectors or publication authority are inherited.

## Read next

- [Start here](START-HERE.md) or [guided setup](SETUP.md).
- [Complete discovery questions](NEW-CLIENT-DISCOVERY.md).
- [What goes in each folder](docs/FOLDER-GUIDE.md) and [answer-to-file map](FILE-BUILD-MAP.csv).
- [Existing workflow bindings](docs/OWNER-BINDINGS.md), [updates and monitoring](docs/UPDATES-AND-MONITORING.md), and [handoff/pilot](deploy/HANDOFF.md).
- [Ways to run](WAYS-TO-RUN.md) and [privacy](docs/SECURITY-AND-PRIVACY.md), [recordable source checks](docs/SOURCE-RECEIPTS.md) and [verification scope](docs/VERIFICATION.md).

A client is an umbrella, not one giant content pipeline. Existing production owners stay canonical. This workbook organizes context and local work; live sending, posting, spending, account changes and background integrations require their own owner-authorized pilot and production contracts.

## Verification

Inspect `python3 scripts/workbook.py --help` first. Run `python3 scripts/verify-template.py` and `python3 scripts/smoke-test.py` for the public source and isolated fictional-client setup. Release evidence records the tested scope; an install or a green folder check does not certify client strategy, current data or production results.

## License

Copyright 2026 Laladim. Code uses the MIT License in LICENSE-CODE. Workbook text and templates use Creative Commons Attribution 4.0 in LICENSE-CONTENT. Credit Laladim when reusing the content. This repository contains no real client example.
