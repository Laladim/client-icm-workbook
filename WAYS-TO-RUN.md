# Ways to use the workbook

Claude Code and Codex share AGENTS.md; CLAUDE.md imports it. Open the repository folder in your chosen assistant and paste the kickoff in START-HERE.md. After installation, open the private client workspace and follow its own entry files. No user-specific paths, symlinks, global hooks or settings are installed.

Before introducing real data on a shared machine, try a routing question in a fictional client. Inspect the files the assistant actually opens. Expect the client map, the matching destination and any deliberately bound external owner. A personal startup profile can point an assistant into a different project even when the current folder is correct. If that happens, use a client-scoped session profile and repeat the question with fictional data.

You can obtain the public source using GitHub's template/copy option, Git clone, or Download ZIP. On Windows, extract the ZIP and use the available Python 3 launcher, often `py -3`; on macOS/Linux, use the available `python3`. Check the local help before copying a command. Shell quoting differs, so the agent should construct arguments for the user's actual shell.

The automated smoke tests exercise Python on Ubuntu, macOS and Windows in GitHub Actions when those runs complete. Local release verification states which environments were actually exercised. File/command tests are not a live end-to-end test of every Claude Code or Codex version. Manual Markdown onboarding remains possible when the user has no terminal access, but command-verification claims require an actual run.

Every client stays outside the public template. GitHub visibility, cloud sync and model/tool access for the private workspace are separate choices. A template download does not grant access to the client's accounts or authorize publishing.
