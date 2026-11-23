# Verification scope

verify-template.py checks public-source hygiene, portable shared entries, canonical question IDs and answer-to-file coverage, local documentation links and required template anatomy. It detects selected secret/private-path patterns; manual staged-file review remains necessary.

The question bank owns both the discovery guide and the CSV. Run `python3 scripts/verify-template.py --write-views` after changing a question. The default audit compares both rendered files in full. In an installed client, `check --accepted` checks the generated workspace and approval record. Run `check --require-current` to inspect source review findings separately.

smoke-test.py runs actual command-line onboarding in disposable private storage and reads the resulting files. It exercises distinct fictional client scopes, explicit brief/workspace gates, selected channel behavior, direct audience/brand consumption, client isolation, source registration and review, evidence expiry/source changes, update records and false-publication refusal, and study-pack output. No real approval, campaign, customer record, platform integration or publication is created by the fixtures.

For a release that changes agent instructions, open independent fresh sessions of Claude Code and Codex in an installed fictional client. Try a new blog, a weekly report, a customer-research question, a LinkedIn carousel and a source freshness question. Starting from the project entry, use the map and one destination file. Compare the visible answer to the client's recorded owner, input, output, next action and review gate. For freshness, compare it to the actual registered receipt or missing review. Record the versions and the files each tool read.

A passing result establishes the tested local installation, routing and evidence gates. It does not prove audience validity, content quality, every AI model's instruction following, current external data or full production reliability. WAYS-TO-RUN.md and the actual CI results identify environments. The reusable source is intentionally separate from private client instances.
