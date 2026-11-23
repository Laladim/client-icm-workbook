# Guided new-client setup

Kickoff: `Read SETUP.md and guide me through installing and onboarding a private client ICM workspace.`

## Start with the person and available context

Explain that the public repository is the template and the installed client folder is private. Ask for the client name, short ID and an intended empty destination outside this repository. Inspect the current folder and its entry instructions before installing. Do not overwrite an existing folder, copy another client's records, create a sibling in a managed workspace, modify global settings or request credentials.

Ask whether the person already has a brief, SOPs, onboarding documents, brand guide, content inventory, analytics exports or an established workflow. Read authorized material first. Extract answers with their exact source location and label them as supplied fact, evidence, interpretation or human decision. Ask only for missing choices, stale facts or contradictions. A document's existence is not proof of freshness, consent or correctness.

Use `python3 scripts/workbook.py --help`, then `init --help` before constructing a command. On Windows use the available Python 3 launcher (`py -3` when installed). No package install, connector, model API or global configuration is needed.

## Phase 1: install and discover

Initialize the explicit private destination. Continue work from the installed folder; it contains its own portable tool and entry files. Run `interview` to get the next small group, with no more than three questions. Record responses using `answer` and the canonical question IDs. The agent handles command/JSON formatting; never make the person maintain JSON by hand.

Preserve human answers. Each record has a basis, who supplied it, source reference when available, and date. Unknown needs a reason/next source; not-applicable needs a reason. Do not convert guesses into customer insights or approvals. Ask the human to resolve actual decisions; an unknown decision can remain provisional only if its downstream action is explicitly blocked. Selected channel IDs turn on their required channel question branches. Use `interview --include-optional` for deeper discovery after core answers.

Source references can be private local files, authorized documents or public pages. Do not copy restricted material into the public repository. Do not fetch paid data, contact the client's staff, connect an account or send anything as an interview side effect. Request secure account invitations, never secrets in chat.

## Phase 2: produce a reviewable client brief

After core questions are answered, run `brief`. It creates `onboarding/03_brief/output/client-brief.md` and displays its SHA-256. Review scope, outcomes, audience, offer/claim limits, selected channels, sources and gaps, desired authority, privacy, owners, measurement and maintenance with the person. Explicitly distinguish confirmed choices from provisional unknowns.

Stop here. Ask the named human to approve or revise this exact brief. A genuine response such as 'I approve this brief' applies to the displayed exact version; record the approver, statement and displayed digest with `approve-brief`. Never invent the response or infer it from silence. If answers or brief bytes change, old approval fails. Fix disagreements before generating the workspace.

## Phase 3: build and walk the seven folders

Only after the approved-brief check passes, run `build`. Answers populate company, brand, customer-evidence, offers, channels, performance and monitoring. Every question has an answer-to-file destination. Missing optional information stays labeled; tools and audience research are never invented. Only selected channel pages are generated. Brand strategy, identity and before/during/after marketing remain distinct.

Use docs/OWNER-BINDINGS.md when recording an existing workflow in the interview answers. Record the source, output and review gate. The selected channel worker displays the approved audience and reviewer, or the missing decision and next action. Each brand page shows its source status. The dated history of explicit brand decisions is in brand/decisions.md.

Run `check`, then walk three realistic jobs: find the audience and approved message, prepare one local content brief using permitted evidence, and route a product/service change to affected online surfaces. Check an unavailable source and an unapproved publication attempt as refusals. Use actual output paths and readbacks. Do not start a real campaign just to test setup.

## Phase 4: human acceptance and handoff

Run `status` to show the generated workspace digest. Present the folder routes, source gaps, local-only authority, operational-owner bindings, maintenance method and pilot limits. Stop for explicit human acceptance of this exact workspace, then use `accept-workspace` with the displayed digest, approver and genuine statement. `check --accepted` must pass before calling onboarding accepted.

Give the person one next action and the active entry. The installed agent follows the existing owner for real work. The workbook itself never sends, posts, spends or changes production. Platform integration requires the separate scoped pilot in deploy/HANDOFF.md. Do not describe a documented cadence as installed automation or a local draft as published.
