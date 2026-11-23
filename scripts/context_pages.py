"""Render private client navigation and reference pages from approved answers."""

from collections import defaultdict
from pathlib import PurePosixPath


# Stable CLI topic IDs and the phrases a client is likely to use.
ROUTES = {
    "business-sops": ("Business SOPs", "company/operations.md"),
    "company-onboarding": ("Company onboarding", "company/operations.md"),
    "staff-delegation": ("Staff responsibilities", "company/operations.md"),
    "clients-profiles": ("Existing clients", "company/operations.md"),
    "web-social-links": ("Official accounts", "company/operations.md"),
    "sales-conversions": ("Sales and conversions", "performance/measurement.md"),
    "brand-system": ("Brand rules and decisions", "brand/CONTEXT.md"),
    "target-audience": ("Who are we writing for?", "brand/strategy/positioning.md"),
    "message-framework": ("Which messages can we use?", "brand/identity/message.md"),
    "platform-strategy": ("Channel scope and reviewers", "channels/strategy.md"),
    "demo-calls": ("Demo calls", "customer-evidence/proof.md"),
    "newsletter-data": ("Prepare a newsletter or find newsletter data", "channels/newsletter.md"),
    "blog-data": ("Write a blog or find blog data", "channels/blog.md"),
    "youtube-data": ("Plan a YouTube video or find video data", "channels/youtube.md"),
    "linkedin-data": ("Create a LinkedIn post or carousel, or find LinkedIn data", "channels/linkedin.md"),
    "case-studies": ("Case studies", "customer-evidence/proof.md"),
    "testimonials": ("Testimonials", "customer-evidence/proof.md"),
    "one-line-praise": ("Short quotes", "customer-evidence/proof.md"),
    "offer-updates": ("Communicate an offer or product change", "records/updates/CONTEXT.md"),
    "weekly-report": ("Prepare the weekly report", "performance/reporting.md"),
    "meeting-brief": ("Prepare a private meeting brief", "performance/reporting.md"),
    "research-libraries": ("What do customers value?", "customer-evidence/research-libraries.md"),
    "cross-channel-study": ("Compare channel results", "performance/cross-channel-studies.md"),
    "backlinks-pr": ("Backlinks and press mentions", "customer-evidence/earned-media.md"),
    "api-help-docs": ("Product facts, API docs and help center", "offers/catalog.md"),
    "competitor-positioning": ("Competitors and positioning", "brand/strategy/positioning.md"),
    "website-traffic": ("Website traffic", "performance/measurement.md"),
    "search-console": ("Search Console", "performance/measurement.md"),
    "keyword-bank": ("Keywords", "performance/search-and-ai.md"),
    "ai-answer-bank": ("AI answers", "performance/search-and-ai.md"),
    "source-freshness": ("Is our data current?", "monitoring/sources.json"),
}

# Keep the area contract with its subject. References and source data stay in
# the files reached from the contract.
AREA_JOBS = {
    "company": (
        "Keep the engagement, delegation and official accounts findable.",
        "Read the engagement for scope and the operations page for responsibilities.",
        "Match a request to the agreed deliverable and named owner.",
        "Keep working notes in `outputs/company/` or the bound company record.",
        "Confirm scope and delegation against the client agreement or decision.",
        "Take changes to the person's recorded engagement contact.",
    ),
    "brand": (
        "Find the current audience, voice, message and visual or lifecycle choices.",
        "Read the relevant block below and its source. Review changed wording in [Brand decisions](decisions.md).",
        "Use the recorded choice for the intended audience. Keep proposed wording labeled.",
        "Record a change in its interview answer and bring the revised brief to the named approver.",
        "Check the block's status, exact wording, decision maker and source.",
        "Carry the approved choice to the selected channel worker.",
    ),
    "customer-evidence": (
        "Find customer language, research, quotes and outcomes that the team may use.",
        "Read the selected proof or research page and the source owner's permission.",
        "Separate prospect statements from customer results and identify the evidence window.",
        "Keep permitted extracts in the named owner home or `outputs/customer-evidence/`.",
        "Check the source, consent, attribution and limits for this intended use.",
        "Give the channel worker the approved excerpt and its source.",
    ),
    "offers": (
        "Establish which product or service facts the client can support.",
        "Read the catalog and the fact owner's current product or service documentation.",
        "Identify the released change and the surfaces it affects.",
        "Record coverage in `records/updates/<id>/record.json` through `record-update`.",
        "Check the fact owner's evidence and a separate readback for each selected surface.",
        "Open [Update coverage](../records/updates/CONTEXT.md) for the receiving owner and gate.",
    ),
    "channels": (
        "Find the working brief for each selected marketing channel.",
        "Read the worker below and the relevant campaign or source material.",
        "Use its audience, reviewer, offer facts and permitted proof to prepare the local draft.",
        "Use the bound production home or `outputs/channels/` for local drafts.",
        "Resolve audience and reviewer gaps before the dependent action. Follow the channel's review decision.",
        "Hand the draft to its named reviewer.",
    ),
    "performance": (
        "Prepare reports from comparable evidence and distinguish traffic from business outcomes.",
        "Read the report requirements or metrics dictionary, then the specified source for the period.",
        "Use the agreed dates, units, denominator and attribution limits.",
        "Use the reporting owner's output or `outputs/performance/` for a local report.",
        "Reconcile the numbers to the source and check the intended recipient and privacy.",
        "Deliver the local draft to the designated report reviewer.",
    ),
    "monitoring": (
        "Assess whether a specific source is current enough for the intended use.",
        "Read [the live source register](sources.json) and the selected owner's receipt.",
        "Run `python3 scripts/workbook.py check --require-current` from the client root.",
        "Use `review-source` with the owner's observed evidence to record a receipt.",
        "Match the source hash, owner and validity rule. Report unresolved sources by name.",
        "Return the dated finding to the requester or the missing check to the source owner.",
    ),
}

SOURCE_MARK = "<!-- Generated from the approved onboarding answers. Edit the answer and rebuild. -->"
ROUTER_MARK = "<!-- Generated from the workbook routes and approved channel selection. -->"


def channel_entry(entry, channels):
    path = PurePosixPath(entry)
    if path.parent.as_posix() == "channels" and path.stem != "strategy" and path.stem not in channels:
        return "channels/strategy.md"
    return entry


def routes_for(channels):
    routes = {}
    for topic, (_, entry) in ROUTES.items():
        destination = channel_entry(entry, channels)
        area = "offers" if topic == "offer-updates" else destination.split("/")[0]
        routes[topic] = (area, destination)
    return routes


def client_map(name, channels):
    grouped = defaultdict(list)
    for topic, (_, destination) in routes_for(channels).items():
        label, requested = ROUTES[topic]
        if destination == requested:
            grouped[destination].append(label)
    for channel in channels:
        destination = f"channels/{channel}.md"
        if destination not in grouped:
            grouped[destination].append(f"Work on {channel}")
    lines = [f"# {name} client map", ROUTER_MARK, "",
             "| Request | Read |", "|---|---|"]
    for destination, labels in grouped.items():
        lines.append(f"| {' / '.join(labels)} | [{destination}]({destination}) |")
    lines.extend(["", "For an unlisted channel, check [channel scope](channels/strategy.md). "
                  "For an unassigned task, check [delegation](company/operations.md) and ask the engagement contact.",
                  "Run `python3 scripts/workbook.py status` for onboarding progress or "
                  "`python3 scripts/workbook.py check --require-current` to check dated source receipts.",
                  "Use the actual workflow owner for production and publication.", ""])
    return "\n".join(lines)


def area_page(area, destinations):
    lines = [f"# {area.replace('-', ' ').capitalize()}", ROUTER_MARK, ""]
    verbs = ("Purpose", "Read", "Do", "Write", "Check", "Next")
    for verb, detail in zip(verbs, AREA_JOBS[area]):
        lines.append(f"- **{verb}** {detail}")
    lines.append("")
    for dest in sorted(destinations):
        path = PurePosixPath(dest)
        if path.parts[0] == area:
            label = path.stem.replace("-", " ").capitalize()
            lines.append(f"- [{label}]({path.relative_to(area)})")
    return "\n".join(lines) + "\n"


def brand_status(questions, answers):
    counts = defaultdict(int)
    for question in questions:
        counts[answers.get(question["id"], {}).get("basis", "unanswered")] += 1
    unresolved = counts["unknown"] + counts["unanswered"] + counts["interpretation"]
    if counts["not-applicable"] == len(questions):
        status = "Not applicable for this engagement"
    elif unresolved == len(questions):
        status = "Open"
    elif unresolved:
        status = "Partially documented"
    else:
        status = "Documented"
    return (f"**Status** {status}. {counts['human-decision']} explicit human decisions. "
            f"{unresolved} open, unanswered or provisional items.")


def worker_brief(channel, answers):
    lines = ["## Local drafting brief", ""]
    for key, label, path in [
        ("audience.primary", "Audience", "../brand/strategy/positioning.md"),
        ("channels.reviewers", "Reviewer", "strategy.md"),
    ]:
        answer = answers.get(key, {})
        value = str(answer.get("value", "")).strip()
        if answer.get("basis") != "human-decision" or not value:
            value = "Unresolved. Hold the dependent work. " + (answer.get("reason") or "Ask the engagement contact.")
        lines.extend([f"**{label}** {value} [Decision source]({path}).", ""])
    lines.extend([
        "Read [voice](../brand/identity/character.md), [message](../brand/identity/message.md) "
        "and the permitted source evidence for this piece.",
        f"Prepare a local {channel} draft in `outputs/channels/` or the bound workflow's output. "
        "Follow the recorded audience-specific review and publication gates.", "",
    ])
    return "\n".join(lines)


PAGE_JOBS = {
    "performance/reporting.md": "Use the named reporting owner, primary evidence, period and recipient below. "
        "Write the local report in its designated output or `outputs/performance/`. Obtain its required review before sharing.",
    "customer-evidence/research-libraries.md": "Start with the named customer-research owner and its accepted findings below. "
        "Write a sourced theme summary in its output or `outputs/customer-evidence/`. Check permission for every quoted or identifying detail.",
    "performance/cross-channel-studies.md": "Read [metric definitions](metrics-dictionary.md). Run `study-pack` on the selected owner outputs. "
        "Read back `outputs/studies/<id>/STUDY.md` and its evidence window before comparing results.",
    "channels/strategy.md": "Use the channel selection and reviewer decisions below. If a channel is absent from the selection, "
        "ask the engagement contact before starting work in it.",
}
