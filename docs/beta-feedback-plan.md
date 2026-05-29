# Quill Beta Feedback Plan

This document exists to answer one practical beta question: how should people report bugs, rough edges, missing features, and usability problems if they do not use GitHub?

## Current Position

Quill is ready for meaningful beta use, but it does not yet ship a general-purpose in-app diagnostics export or a no-login report flow.

Today we have:

- a diagnostics bundle specification in the engineering documentation
- recovery and notification infrastructure
- extraction-quality review
- bad-extraction package export for extraction-specific issues
- a repository that can accept GitHub issues from users who already use GitHub

Today we do not have:

- a public support mailbox defined in this repository
- a BITS-hosted HTTPS feedback form
- an in-app `Save Diagnostics...` command for general bug reports
- an in-app `Report a Bug...` command that prepares a safe report package

One strong path now exists elsewhere in the Community Access ecosystem: GLOW's feedback service can route support entries into `Community-Access/support`, and it now exposes a shared authenticated API for app-to-app intake. Quill can build on that instead of inventing a separate support silo.

## Launch Recommendation

Do not treat GitHub login as the only feedback path for a broad public beta.

For the public beta, Quill should offer one primary feedback path that does not require GitHub login and one secondary path for technical users who already prefer GitHub.

### Recommended primary path

Use a BITS-controlled HTTPS feedback form or shared support-hub surface.

The form should:

- work without GitHub sign-in
- work well with screen readers and keyboard-only users
- support short feedback, structured bug reports, and feature suggestions
- allow optional upload of a user-reviewed diagnostics bundle
- show a clear privacy statement before upload
- return a human-readable confirmation number after submission

The most practical near-term implementation is a Quill bug-report flow that submits to the Community Access support hub rather than directly to GitHub from the client.

### Recommended secondary path

Offer GitHub issues as an optional route for users who already use GitHub and want a public issue tracker.

## Ideal User Flow

1. User chooses `Help -> Report a Bug...` or visits the beta feedback link from the website.
2. Quill explains what information will be included and what will never be included.
3. User chooses whether to create a diagnostics bundle.
4. Quill writes a redacted zip file locally for the user to review.
5. User either attaches that bundle to the secure web form or submits feedback without an attachment.
6. The system returns a confirmation number and plain-language next steps.

If Quill uses the shared Community Access support hub, the confirmation can also include the support issue URL when server-side sync is enabled.

## Privacy and Security Requirements

Any beta feedback system should follow these rules:

- never auto-send diagnostics
- never include document body text by default
- never include secrets, provider keys, or tokens
- strip URL query strings unless the user explicitly opts in
- hash file paths by default unless the user explicitly opts in to plain paths
- describe the upload destination before any submission
- support cancellation before upload begins

## Minimum Viable Fields

The secure form should ask for:

- name or nickname
- email address only if follow-up is desired
- Quill version
- Windows version
- short summary
- what happened
- what the user expected to happen
- exact steps to reproduce if known
- whether the issue blocks work
- optional diagnostics upload

## Launch-Blocking Gap

Before the broadest beta push, one of these needs to exist:

- a secure BITS-hosted feedback form
- a BITS support mailbox that is published clearly in the application and docs
- a comparable no-login support intake channel with attachment support

The new Community Access support-hub path now satisfies the shape of that requirement if Quill is wired into it with careful diagnostics controls.

Without one of those, the beta can still proceed for invited testers, but the public story is weaker and less inclusive than it should be.

## v1.1 Roadmap Tie-In

The v1.1 roadmap should include:

- `Help -> Save Diagnostics...`
- `Help -> Report a Bug...`
- redacted diagnostics bundle generation
- no-login secure beta feedback intake, preferably through the shared Community Access support hub
- user-facing documentation for how to report bugs and how diagnostics are handled
