# GitHub Features Reference

## Pull Requests

Pull requests are the core collaboration mechanism on GitHub. A pull request proposes changes from one branch to another and facilitates code review, discussion, and approval before merging.

### Pull request features
- **Draft PRs:** Mark a PR as draft to signal it's not ready for review. Useful for work-in-progress visibility.
- **Review requests:** Request specific team members or teams to review a PR. Reviewers receive notifications.
- **Required reviews:** Branch protection rules can require a minimum number of approvals before merging.
- **Suggested changes:** Reviewers can suggest specific code changes that authors can apply with one click.
- **PR templates:** `.github/pull_request_template.md` provides a consistent structure for all PRs in a repo.
- **Merge strategies:** Supports merge commit, squash merge, and rebase merge — configurable per repository.
- **Auto-merge:** PRs can be configured to merge automatically when all required checks pass.

### Copilot for Pull Requests
- Automatically generates PR descriptions from the diff
- Summarizes changes in plain language for non-technical reviewers
- Suggests labels, reviewers, and related issues based on PR content

---

## GitHub Discussions

GitHub Discussions is a collaborative communication forum built into GitHub repositories. Unlike issues (which are task-oriented), Discussions are conversation-oriented.

### Use cases
- Community Q&A for open source projects
- RFC (Request for Comments) processes for architectural decisions
- Project announcements to a community of contributors
- Maintainer office hours and AMA sessions

### Categories
Maintainers define custom categories. Common: Announcements, Q&A, Show and Tell, Ideas, General.

---

## GitHub Projects

GitHub Projects is a flexible project management tool built into GitHub. It supports both table (spreadsheet-like) and board (kanban) views with custom fields and automation.

### Key features
- Custom fields: text, number, date, single select, iteration, labels, milestone
- Automation: automatically move items based on PR or issue status changes
- Cross-repository: a single project can track issues and PRs from multiple repositories
- Insights: built-in charts for tracking progress, velocity, and burndown

---

## GitHub Packages

GitHub Packages is a package registry integrated directly into GitHub. It supports npm, Maven, NuGet, RubyGems, Gradle, Docker, and Conda packages.

### Key capabilities
- Publish packages directly from GitHub Actions workflows
- Fine-grained access control using GitHub repository permissions
- Package versioning linked to GitHub releases and tags
- Free for public packages; storage and bandwidth limits for private packages

---

## GitHub Pages

GitHub Pages hosts static websites directly from a GitHub repository. It supports Jekyll, Hugo, and any static site generator, as well as plain HTML/CSS/JS.

### Use cases
- Project documentation sites
- Personal portfolio sites for developers
- Open source project landing pages
- Technical blogs

### Configuration
- Enable via repository Settings > Pages
- Supports custom domains with HTTPS
- Builds triggered automatically on push to the configured branch

---

## GitHub Releases

GitHub Releases formalizes the concept of a software release on GitHub. A release bundles a specific commit (via a tag) with release notes and binary assets.

### Features
- Release notes: manually written or auto-generated from merged PRs and commits
- Assets: attach binary files (executables, archives, installers) to any release
- Pre-releases: mark releases as pre-release to signal they're not production-ready
- Latest release API: consumers can always fetch the latest stable release via API

---

## GitHub CLI (gh)

The GitHub CLI (`gh`) brings GitHub features to the terminal. It supports the full GitHub workflow without leaving the command line.

### Key commands
- `gh pr create` / `gh pr review` / `gh pr merge` — full PR lifecycle
- `gh issue create` / `gh issue list` — issue management
- `gh run watch` — watch a GitHub Actions workflow run in real time
- `gh repo clone` / `gh repo fork` — repository operations
- `gh secret set` — manage repository secrets
- `gh extension install` — install community-built CLI extensions

---

## GitHub API

GitHub provides two APIs for programmatic access: REST API (v3) and GraphQL API (v4).

### REST API
- Comprehensive coverage of GitHub resources: repos, issues, PRs, users, orgs, teams
- Rate limit: 5,000 requests/hour for authenticated requests
- Webhooks: configure HTTP callbacks for any GitHub event

### GraphQL API
- Fetch exactly the data you need in a single request
- Strongly typed schema with introspection
- Supports GitHub's newer features faster than REST API
- Rate limit based on complexity points, not request count

### GitHub Apps
- Recommended for integrations: fine-grained permissions, installable per org or repo
- OAuth Apps: user-delegated permissions, simpler but broader access scope
