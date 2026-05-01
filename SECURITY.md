# Security Policy

## Supported Versions

Security fixes are applied to the **current latest release** on the `1.x` line only. Previous 1.x minor releases are not patched separately.

| Version | Supported |
|---------|-----------|
| 1.x (current latest only) | Yes |
| < 1.0 | No |

## Scope

PlotStyle is a data-formatting library. It reads TOML spec files, applies Matplotlib rcParams, and delegates file I/O to Matplotlib, fontTools, and Pillow. There are no network calls, no eval or exec, and no subprocess invocations in PlotStyle's own code. When LaTeX rendering is enabled, Matplotlib invokes an external LaTeX process; see "Not in scope" below.

**In scope: please report these.**

- **Path traversal or unintended file writes:** a bug in export path construction that allows writing outside the intended output directory
- **Dependency vulnerabilities with direct user impact:** a CVE in Matplotlib, fontTools, Pillow, or tomli (Python 3.10 only; Python 3.11+ uses the stdlib tomllib) that is exploitable specifically through PlotStyle's public API
- **TOML schema bypass:** a way to trigger arbitrary code execution by crafting a malicious `.toml` spec or overlay file

**Not in scope:**

- LaTeX rendering executing figure content. When LaTeX rendering is enabled, all text in the figure is passed to your local LaTeX installation. This is expected behavior. If you are building a tool that passes untrusted content (for example, user-submitted labels) into PlotStyle figures with LaTeX enabled, you are responsible for sanitizing that content before it reaches PlotStyle.
- Informational error messages that include file paths; these are not exploitable.
- Vulnerabilities that require the attacker to already control the machine or the Python environment.
- CVEs in PlotStyle's dependencies that only affect direct consumers of those libraries and are not reachable through PlotStyle's API; please report those upstream.

## Reporting

**Do not open a public GitHub issue for security vulnerabilities.**

Use GitHub's private vulnerability reporting: [Report a vulnerability](https://github.com/rahulkaushal04/plotstyle/security/advisories/new).

Include the following in your report:

- A description of the vulnerability and its potential impact
- Steps to reproduce, with a minimal example if possible
- Any mitigations or fixes you have already identified

## Disclosure Timeline

| Step | Target |
|------|--------|
| Acknowledgement | Within 48 hours |
| Initial assessment | Within 7 days |
| Fix or decision communicated | Within 30 days |

If the 30-day target cannot be met, we will contact you before it passes to explain the delay and agree on a revised timeline.

Once a fix is released, the vulnerability will be disclosed in the GitHub release notes and you will be credited by name unless you request otherwise. We ask that you withhold public disclosure until the fix is available or until the agreed timeline has passed.
