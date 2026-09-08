# Telegram Coach Runtime and Maintenance

Codex is the PM, engineering and release owner. Brian discusses coaching changes
in the training project conversation; Notion is the internal project record.

## Implementation status — 2026-09-08

Source branch: `codex/telegram-coach`, [PR #66](https://github.com/bribergey/brian-training/pull/66).
The replacement Mac service is running and owns the existing Telegram bot.
Runtime release: `59d2524ef94e3ab40ea6304c149406f583664ac1`.
Launch agent: `com.briqtraining.coach`; its independent caffeinate parent is active.
OpenClaw's coach account is disabled and explicitly stopped. The migration test
was delivered to Brian's existing chat. His reply and the completed coaching
response were verified; cutover acceptance is complete.
Brian chose this Mac and the existing Telegram bot. Coach permanently uses
`Asia/Shanghai` (China time), including while Brian travels; do not ask again. Existing bot: `@coach_trainerhub_bot`.

Verified: the app-bundled CLI at
`/Applications/ChatGPT.app/Contents/Resources/codex` is version 0.153.4 and accepts
managed ChatGPT sign-in in an isolated coach home. GPT-6 Astra is available on
the account. The unrelated `/usr/local/bin/codex` wrapper is broken; do not use it.

## Verified implementation results

- 18 local regression tests pass, including per-set completeness, numeric UI
  compatibility, scheme drift, block/week rollover, recipient restrictions,
  expired/unpresented/tampered approvals, receipt replay and Unicode delivery.
- Live synthetic staging rehearsal passed monthly creation, weekly creation,
  one-row adjustment, three idempotent replays and stale-snapshot rejection.
  Brian's production fingerprint stayed unchanged.
- The staging app showed the synthetic Week 1 / September 14 session, with
  all three working presets populated as 40 kg × 5. No workout was logged.
  QA signed out; the synthetic fixture was restored afterward.
- GPT-6 Astra passed four supplied coaching scenarios and a real dynamic-tool
  rehearsal: it read context/catalog/blueprint/history and prepared a valid
  synthetic monthly proposal without applying it. These are bounded checks,
  not a guarantee of perfect coaching; ongoing real-use feedback still matters.
- Managed ChatGPT authentication works. No paid API fallback is configured.

Cutover checks passed: confirmed bot identity and no webhook/pending updates;
seeded the durable inbox offset from the current OpenClaw SQLite boundary;
exclusive Telegram long-poll completed without a competing consumer; service
started and restarted; migration message delivery succeeded. Brian's production
fingerprint remained unchanged. No real program proposal or write occurred.

Restart testing caught the app-server's empty-thread behavior: a thread with no
first turn has no saved rollout. The service now recreates only an unused missing
startup thread; it refuses to discard one that has started a turn. A separate live
Codex rehearsal verified that a completed conversation resumes with its earlier
context and dynamic tools. The recovery path has a regression test.

OpenClaw's all-account channel-status RPC has an existing failure resolving a
disabled Cleo SecretRef. Its Telegram hot reload aborted after stopping accounts;
we issued an explicit coach stop and restarted default/Ian/PJ/PM individually.
Their provider-start logs were verified; Coach did not restart. The status error
occurs after the targeted lifecycle operation, as confirmed in the installed
OpenClaw source. Runtime health claims rely on the lifecycle evidence and exclusive
Telegram poll, not the broken aggregated RPC. Historical coach files are retained
with `MIGRATED_TO_CODEX.md` pointing to this project.

The active scheduler has a PM job and legacy Ian/Dex configuration remains, so
this work does not authorize uninstalling all of OpenClaw. Acceptance completed:
Brian replied to the migration test and Coach returned the expected updated
coaching approach. The inbound update finished successfully, the conversation
was persisted, no proposal was created and production data stayed unchanged.
No new actual training block is implied by successful migration.

## Telegram progress during long requests

After the first monthly-planning request, Brian reported silence while Codex was
actively reading history and generating commentary. The bridge had discarded
commentary and sent only the final answer. `coach/progress.py` now acknowledges
processing, refreshes typing every four seconds, forwards completed user-facing
commentary, and sends a still-working notice after 90 seconds without a visible
update. Reasoning and tool payloads are never forwarded. Notices stop before the
final result; progress transport failures do not abort the coaching request.

Regression coverage includes event/turn filtering, commentary versus final output,
reasoning exclusion, notifier shutdown and nonfatal transport failures. A live
synthetic Codex turn confirmed separate commentary and final delivery. Deploy
only when the current inbox is idle; do not interrupt a real plan to update UI
feedback. See the roadmap bug record for the final release and current-request
verification.

## Sources of truth

- `coach/instructions/COACH.md`: coaching judgment and operating rules.
- `coach/instructions/DATA_CONTRACT.md`: complete monthly/weekly/adjustment format.
- `coach/planning.py`: date/week assignment and prescription validation.
- `coach/tools.py`: the complete model-facing read/draft/memory tool surface.
- `coach/data.py`: trusted scoped database operations and transactional read-back.
- `coach/state.py`: durable proposals, approvals, inbox, receipts and coaching memory.
- `coach/service.py`, `coach/telegram.py`, `coach/codex_client.py`: transport/runtime.

Private runtime root: `~/.local/share/briq-coach/`. Its directories use mode 0700;
credentials and state use mode 0600. It contains `config.json`, `secrets.json`,
`codex/`, `workspace/`, `state/`, and `backups/`. Never put these in Git or Notion.

The isolated Codex home uses managed ChatGPT OAuth, with API login disabled. Its
initial auth was transferred locally from Brian's existing Codex auth store.
It manages refresh independently. No OpenRouter or API billing fallback is
automatic. On auth expiry or subscription exhaustion, report unavailable and
restore managed sign-in; review an OpenRouter alternative explicitly if needed.

The model has no execution environment, shell or generic Supabase connector.
It receives scoped data via dynamic tools and may prepare proposals. Hosted web
search supports coaching research. No model tool can apply a database write.

## Database boundary

The trusted Python service currently uses the existing Supabase management
credential previously used by the coach's OpenClaw integration. It holds this
credential privately and does not pass it to Codex. This credential is broad:
protect the host/service and consider a dedicated restricted backend credential
in a later hardening change. This implementation does not alter RLS or grants.

The fixed database adapter pins `training.*` and `user_id='brian'` for production,
or `_staging` and `user_id='codex_qa'` for staging. SQL comes only from trusted code,
with quoted literals and fixed column/table allowlists; models cannot provide SQL.
The service reads profile/measurements/history and the shared exercise catalog.
It writes only program/monthly_program. No logged workout, profile, measurement
or shared catalog writes are provided.

Monthly contracts preserve exact rep/set structure in `internal_notes`, because
the existing monthly table has no reps or per-set columns. Weekly writes populate
every working set. Trigger-owned `session_key` is never supplied.

Approval buttons identify immutable, integrity-checked proposals. New drafts
supersede unapproved ones; unapproved proposals expire after 48 hours. Source
fingerprints detect changed data before application. Fixed proposal UUIDs,
transactions, a per-user advisory lock and exact read-back prevent partial or
duplicate writes. An approved request with a lost response can retry the same
proposal and recognize an already-committed result. Never retry by creating new IDs.

## Validation and staging

Run `python3 -m unittest discover -s coach/tests -v` and
`python3 -m py_compile coach/*.py`. Regression cases include incomplete sets,
anchor scheme drift, block rollover, deload structure, duplicate inbox delivery,
stale/superseded approvals and quoted text in SQL.

Before interactive staging checks, refresh the `codex_qa` fixture using
`scripts/qa/README.md`. Exercise monthly creation, weekly creation, adjustment,
replay after lost response, stale proposal rejection and exact read-back. Check
the queue and per-set presets at https://briqtraining.com/staging/app/ while signed
in as `dev@lostplate.com`. Do not use Brian's app login for browser QA. Refresh
the fixture again to remove synthetic program changes when finished.

Run representative model scenarios: repeated underchallenging successes, one
late missed rep, repeated early misses, maintenance/travel breaks, equipment
increments and consistent anchor schemes. Verify reasoning uses the actual
evidence, gives a recommendation and identifies what would change it.

## Release preparation

After committing the source, run `python3 coach/stage_release.py`. It copies
that committed coach directory into the private runtime's `releases/<commit>/`,
and prepares `com.briqtraining.coach.plist`; it does not start a consumer.
The definition uses an independent `caffeinate -i` parent, so the new coach's
sleep prevention will not depend on OpenClaw. Record the full source commit.

Private `config.json` follows `coach/config.example.json`. Use the confirmed
`Asia/Shanghai` timezone and verified private Telegram user/chat IDs. Start with both
switches false. The credential file has `telegram_token` and
`supabase_access_token`; never copy those values into public examples.

Only after old consumer shutdown and offset reconciliation: enable the two
switches, copy the prepared plist to `~/Library/LaunchAgents/`, then bootstrap
`gui/<uid>` with that exact plist. Confirm the service log and Telegram reply.
For upgrades, boot out the old agent before loading the new committed release.

## Controlled cutover and rollback

1. Verify the runtime, managed auth, tests and private context. Preserve China time.
2. Back up the old coach config/binding and relevant private instructions/history.
3. Inspect active OpenClaw routing and current Telegram update offset. Current
   offsets are in OpenClaw SQLite `plugin_state_entries`, plugin `telegram`,
   namespace `telegram.update-offsets`, key `coach`; migrated JSON is historical. Stop only
   the old coach Telegram consumer; retain unrelated bots and shared services.
4. Seed the replacement offset so historical pending messages do not execute.
   Retain an audit of the boundary. Never drop pending messages silently.
5. Enable the new consumer and install a dedicated launchd agent. Verify only one
   consumer owns the bot and restart recovery works. The Mac must remain awake
   and online; the dedicated launch agent uses its own caffeinate parent.
6. Send Brian a clearly identified migration test, verify a reply in the same
   Telegram chat, and check `/status`. Initial actual workout changes still need
   approval of their exact proposals. Do not create a return week automatically.
7. Record the release commit, service label, model, instruction version, QA and
   remaining dependencies here and in Notion. Archive the old coach only after
   stable operation. Do not uninstall the shared OpenClaw installation.

Rollback: stop the new launchd agent before restoring the old coach consumer.
Reconcile Telegram offsets and any approved proposal receipts first. Preserve
private state for diagnosis. A rollback never automatically reverts workouts.

## Future coach updates

Capture the requested behavior and representative failure case; inspect current
logs and instructions; edit the source instructions/implementation in a focused
PR; run the relevant regression and model checks; rehearse staging; deploy a
versioned local release; restart/resume with the new instructions; verify the
same Telegram bot; update this runbook and the roadmap. Prompt-only changes also
need a behavior check. Keep the athlete's private context separate from generic
instruction changes, and explain consequential coaching decisions in chat.

Roadmap card: https://app.notion.com/p/3d5e5cb920a581d28433ce0ccad38641
