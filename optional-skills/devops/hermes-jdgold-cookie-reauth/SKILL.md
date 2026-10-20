---
name: hermes-jdgold-cookie-reauth
description: Restore expired JDGold sessions through browser login.
version: 1.0.0
author: "Wu Haoyang (@whyy9527)"
license: MIT
platforms: [macos]
metadata:
  hermes:
    category: devops
    tags: [jdgold, authentication, browser, cron]
---

# Hermes JDGold Cookie-Backed Reauthorization Skill

Restore expired JDGold sessions through the supported browser login flow and
maintain bounded Hermes reauthorization jobs. Session restoration remains separate
from downstream financial decisions and transactions.

## When to Use

- JDGold reports an expired login after several hours and the user asks Hermes to
  restore it automatically.
- The installed JDGold client has no durable refresh credential, but its supported
  same-machine login entrypoint can open the user's normal browser.
- A prior diagnosis equated "no refresh endpoint" with "browser login cannot be
  automated" without testing the real page and callback.

## Prerequisites

- The installed `jdgold` skill and its supported status/login entrypoints.
- The intended Hermes profile, with its own `$HERMES_HOME`.
- A same-machine browser session accessible from the execution environment.
- macOS for the LaunchAgent workflow verified by this skill.

## How to Run

Use `read_file` to load the installed `jdgold` instructions. Use `terminal` for
its supported status/login entrypoints and Hermes cron commands, following the
procedure and authorization boundaries below.

## Quick Reference

Backend token refresh and browser reauthorization are different mechanisms. A client
may lack a refresh token while the authorization page immediately succeeds from an
existing browser session, returning the normal callback and issuing a new short-lived
credential. Declaring automation impossible from source inspection alone misses this
path. Declaring it fully verified after one terminal run also overstates evidence: a
Hermes LaunchAgent may have different GUI and browser access.

## Procedure

1. Load the installed `jdgold` skill and obey its version check and credential-output
   rules. Never inspect or print the stored credential, browser cookies, authorization
   URL, callback parameters, or account data.
2. Check login state through JDGold's supported status command. Use only its exit code
   and non-secret remaining-duration fields.
3. If the user has not explicitly authorized unattended use of the existing browser
   session, stop before scheduled reauthorization. This permission is separate from a
   request for a reminder or health check.
4. Test the supported same-machine login entrypoint once with output redirected to a
   private temporary directory. Do not use a hand-built OAuth request or direct token
   exchange. Verify that the normal callback changes state from expired to valid
   without account input, QR scan, MFA, or a manual approval click.
5. For an authorized Hermes job, use a `no_agent` script inside
   `$HERMES_HOME/scripts`. The script should:
   - exit silently when login is already valid;
   - call only JDGold's supported login entrypoint when expired;
   - suppress all login output because it may contain authorization material;
   - poll only the supported login-status command for a bounded interval;
   - exit silently on success and return a short business-facing error on failure.
6. Create or update the job through the supported Hermes cron command, never by
   editing `jobs.json`. Back up the job store before mutation. Choose a time that gives
   the short-lived authorization enough coverage for its actual consumer workflow.
7. Keep downstream FundLog ownership unchanged. The Gold adapter reads private facts
   only after the external session is valid; it must not read, exchange, copy, or store
   credentials.

## Pitfalls

- Do not delete the current credential or use a force-login flag merely to manufacture
  an expired-path test.
- Do not automate QR, MFA, CAPTCHA, password entry, or a newly presented consent grant.
- Do not store browser cookies, passwords, or authorization URLs in Hermes config,
  prompts, scripts, or logs.
- Do not let login automation trigger holdings capture, Gold decisions, simulated
  trades, or real financial transactions.
- Do not call this backend refresh. Describe it accurately as browser-cookie-backed
  reauthorization, and preserve the residual dependency on the browser session.

## Verification

- Terminal expired path: expired state became valid through the normal login callback
  without user input, and the reported remaining duration was plausible.
- Hermes current-valid path: a manual job run completed with empty output and no
  delivery.
- Hermes expired path: do not claim end-to-end completion until a scheduled or manual
  expired-state run completes through the LaunchAgent environment. Treat the first
  such run as a monitored canary.
- Failure path: if the browser is logged out, the Mac is locked, MFA or QR appears, the
  callback times out, or GUI access is unavailable, the job must fail visibly rather
  than loop, retry authorization repeatedly, or report success.
- Confirm persisted logs and output documents contain no credential, authorization
  URL, callback query, account identifier, or private holdings.
