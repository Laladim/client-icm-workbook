# Record a source check that can actually pass

A working path is not current evidence. The workbook includes both a source-readback template and commands to register a source and record its actual owner review. Inspect each subcommand help before use.

1. Use register-source to name a stable ID, actual file/URL locator, owner, cadence, sensitivity and permitted public use. Registration stays unreviewed. Re-registering resets its old reviewed state and preserves prior JSON history.
2. The source owner runs the actual refresh or opens the current source. Keep its real readback output in the private workspace or authorized owner home. The workbook does not run a connector, install a scheduler or guess that the job succeeded.
3. The agent fills monitoring/source-readback.template.json into a separate evidence file from the observed result. It names the exact source ID/locator/owner, pass result, timezone-aware checked-at date, supported use/limits and current source hash. Time-sensitive data needs an owner-defined unexpired valid-until. Decision-controlled context needs the actual decision_source and decision_sha256; brand choices do not expire arbitrarily, but a changed decision reopens the check.
4. Run review-source with that evidence path and the registered owner. The tool reads/hash-binds the evidence, checks source identity and validity, writes an immutable receipt and updates only that source's review pointer.
5. Run check --require-current to expose missing, unavailable, changed or expired evidence. A readback proves only its stated source/window/use, not all factual claims or public permission.

URL evidence additionally needs an actual successful HTTP response and content hash. A URL string is not a check. Credential-like files and access-bearing URLs are refused. Never place passwords, keys or tokens in source notes.

For studies, agree the metrics dictionary first. Use study-pack to index selected owner outputs with exact files/ranges, metric definitions, units, time windows and limits. The resulting private STUDY.md and manifest make evidence easy to inspect without moving its canonical home or silently adding unlike metrics.
