# Telegram Coach Runtime and Maintenance

Codex is the PM, engineering and release owner. Brian discusses coaching changes
in the training project conversation; Notion is the internal project record.

## Purposeful exercise notes — 2026-11-02

Instruction version `2026-11-02.1`; bundle SHA256
`97d1719e61d184b114c20434ab839c883954577d7807980bac8a2ce5fe21aa5a`
for `COACH.md`, two newline bytes, then `DATA_CONTRACT.md`.

Brian reported long exercise notes and a confusing Codex approval handoff.
The bridge was prepending the complete evidence field to every working exercise
note, despite the model authoring a separate short instruction. Old instructions
also encouraged the same exhaustive checklist for every exercise.

The bridge now saves only the authored note. Dated evidence and decisions remain
in the private proposal, covered by its integrity digest; they are never added to
the app note or weekly proposal attachment. Later program/history reads expose
the latest applied proposal's reasoning privately to Coach. Unapproved or
superseded reasoning cannot replace saved coaching history.

Each note is one individually chosen useful sentence, normally 15–30 words.
Validation rejects multiline, clearly multiple-sentence, or oversized notes
(240 characters / 40 words); it never truncates them. This is a readability
ceiling, not a content template. Needed exercise-specific ramps stay with that
exercise, while accessory warm-ups, routine warnings and redundant fallbacks are
not mandatory. General warm-up rows contain general preparation only.

Coach owns recommendations about dose, progression, warm-ups and note wording.
Set counts require a reason based on goals, overlapping work, performance,
effort, recovery and time. A template records the agreed design rather than
justifying it. Normal coaching decisions do not require Codex approval; an actual
tool/runtime limitation still needs an engineering handoff. Brian's exact-plan
approval remains necessary before any production workout save.

Validation: 40 regression tests and compilation passed, including exact saved
notes, private evidence integrity and later retrieval, legacy compatibility,
length rejection and preserved approval boundaries. The live synthetic model
rehearsal produced a concise note, explained its three-set dose, and explicitly
said shortening notes did not need Codex approval. It could only read synthetic
data and draft; it had no database-write capability. The live staging rehearsal
verified the exact stored note field, month/week/adjustment writes, three
idempotent replays and stale rejection. Brian's production fingerprint was
unchanged and the synthetic fixture was restored. These are bounded behavior
checks, not a guarantee that every future coaching judgment will be correct.

The current unsaved draft is being reviewed for an editorial replacement with
identical exercises, dates, sets, loads and rests. Existing saved workouts are
outside this correction. Deployment and draft delivery are recorded below after
verification. Notion checkpoint remains blocked: the documented roadmap card
returns `NOT_FOUND`, so its current status is unknown and was not updated.

## Stability hardening — 2026-11-02

Follow-up work is tracked in [PR #68](https://github.com/bribergey/brian-training/pull/68).
The runtime bridge identifies as version `0.2.0`. The coaching instruction bundle
is unchanged: SHA256
`8223a5c2f9b93c897daea93a584af5c9a368e569f1ef8aa3ad7c63af2f813cf5`
for `COACH.md`, two newline bytes, then `DATA_CONTRACT.md`.

- Coach uses a complete private copy of the verified CLI package, including its
  resources and helper binaries. `pin_runtime.py` records every file's SHA256;
  release staging rejects an unpinned or changed package. Updating or moving the
  desktop app no longer changes the deployed Coach executable. CLI upgrades are
  deliberate, rehearsed releases, not automatic desktop upgrades.
- Telegram polling starts independently of model availability. `/status` and
  `/start` use a separate durable queue and do not wait behind a coaching turn.
  Status distinguishes a connected model, unchecked startup, missing runtime,
  and unavailable sign-in, and reports the last fully delivered coaching reply.
- While idle, the worker checks/refreshes managed authentication every 15 minutes,
  retries failed connections after one minute, and reconnects a dead model process
  using the same saved conversation. It never copies credentials automatically,
  changes the model, or falls back to paid API access. A revoked login still
  requires restoring managed sign-in.
- Requests are claimed durably before execution. After a crash, an already
  claimed request becomes interrupted and receives a recovery notice; it is not
  silently replayed. Unstarted requests remain queued. An approved save must be
  retried using the same proposal button and its existing idempotent receipt.
- The main loop detects a dead worker, an idle worker stuck over five minutes,
  or an active request stuck over twenty minutes, then lets launchd restart it.
  Model turns retain their existing ten-minute limit. Ordinary polling errors
  retry after five seconds. Routine service logs rotate at 2 MiB with five backups.
- `health.py` reads operational metadata only and exits nonzero for stale polling,
  a stale worker, an overdue request or an unavailable/unchecked model. It neither
  reads credential files nor calls Telegram or the model. It does not provide an
  external alert when the Mac itself is offline.

Validation: all 34 regression tests passed, along with Python compilation and
the canonical app contract check. A live synthetic test on the pinned CLI passed
inference, a dynamic-tool round trip, process restart and exact conversation
recall. It used an isolated conversation and a no-data dynamic tool; no athlete
data or database write tool was available to it.

Deployed source: `6963f334da1ea80985908b7884baf262c409d771`, at 21:05 China time
on November 2. The private CLI package is version `0.162.0-alpha.17.2`, package
SHA256 prefix `2cca78e7ae38ee10`. Post-restart health was `healthy`, model `ready`,
inbox idle with ten completed updates, fresh Telegram polling and no new service
errors. The saved conversation ID, inbox offset and hash of all proposal/receipt
rows matched the pre-deployment snapshot. The two real Telegram requests after
the initial repair completed before cutover; no active plan was interrupted.
At 21:07 China time, the new release completed and delivered a fresh real Telegram
coaching response. Health recorded both model success and reply delivery, with
eleven completed inbox updates and no pending work. Live `/status` still
awaits Brian's check; its unavailable-model and busy-worker behavior passed the
synthetic regression tests. No production training data was mutated by the
deployment work. The PR remains open for source-history review; the Mac service
is already deployed, and the static app was not republished.

The Mac still must be powered, logged in, awake and connected. This change does
not make it an always-on hosted service, guarantee provider availability, or
renew a revoked login without authorization. The existing independent caffeinate
process prevents idle sleep while the launch agent is active. Hosting elsewhere
would be a separate architecture/cost decision.

Notion checkpoint remains blocked by access to the documented roadmap card;
its current status is unknown and was not changed. Keep this runbook checkpoint
until the connection can access the card again.

### Pinned runtime upgrades and health

Copy a verified installed package without changing the running service:

```sh
python3 coach/pin_runtime.py --source /Applications/ChatGPT.app/Contents/Resources/codex-cli
```

Use the returned `codex_binary` in the private runtime config only after a live
synthetic inference/tool/restart rehearsal. Back up the config and launch
definition first, wait for an idle inbox, stage a committed source release,
and restart the dedicated agent. Preserve the previous runtime directory for
rollback. Never point production at an untested newly copied version.

Read health without interacting with the bot:

```sh
python3 coach/health.py --runtime ~/.local/share/briq-coach
```

Allow one completed Telegram long-poll after startup. Expect `healthy`, model
`ready`, a recent `last_poll_ok`, and `busy: false` when idle. `ready` verifies
authentication and conversation setup, not a new inference; the separate
`last_model_success` and `last_reply_delivered` timestamps show actual completed
work. Send `/status` to https://t.me/coach_trainerhub_bot to check the live command,
including during a long request; expect a prompt status response. A normal text
request should acknowledge processing and deliver its completed response.

Rollback: stop only `com.briqtraining.coach`, restore the previous private config
and launch definition, and bootstrap it again. Do not replace the current SQLite
database with an older backup. Inspect any `processing`, `interrupted` or `control`
inbox rows first: older releases do not understand those states. Do not reset
offsets, replay an interrupted request, or revert programs as part of rollback.

## Startup recovery — 2026-11-02

Brian reported that Coach was not responding. The dedicated launch agent was
crashing before Telegram polling because its configured executable,
`/Applications/ChatGPT.app/Contents/Resources/codex`, no longer existed. The
installed executable is now
`/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`
(verified version `0.162.0-alpha.17.2`). The installed CLI still supports the
service's `app-server --stdio` transport.

After correcting the path, the isolated coach sign-in returned no authenticated
account. A private rollback snapshot preserved the old config, auth, launch
definition and coach SQLite state. The coach's managed sign-in was restored
locally from Brian's existing desktop sign-in; no credentials were printed or
committed. The dedicated launch agent was restarted at 20:41 China time.

Verified: ChatGPT account recognized, existing coach conversation resumed,
GPT-6 Astra completed an isolated no-tool inference check, all 21 regressions
passed, and the service reached its production polling loop. Runtime source
remains `e05cb45e5dd928a46db1c94e713ca8da02796f37`; coaching instructions and
approval rules are unchanged. No production data operations were performed by
the repair. The SQLite inbox contained no pending messages, and Telegram reported
zero pending updates for `@coach_trainerhub_bot`. Delivery of Brian's reported
message is therefore unverified; a new message to that exact bot is needed for
end-to-end acceptance.

Notion checkpoint is blocked: the documented roadmap card returned `NOT_FOUND`
through the connected workspace, and a search for `coach` returned no results.
Its current status could not be read or updated. This dated entry preserves the
checkpoint until access is restored.

### Diagnosing startup silence

Check the dedicated launch agent and private service log before consuming or
replaying Telegram updates. A running launchd definition does not establish
health: check the process state, restart count and successful service-start log.
Never paste raw private logs or authentication files into Git or Notion.

For a missing executable, locate and verify the installed app-bundled CLI; do not
use the unrelated `/usr/local/bin/codex` wrapper. Stop only this coach agent,
preserve a private rollback snapshot, and update its private `codex_binary`.
Before restarting, check managed authentication, resume the saved conversation,
and complete a no-tool model check in a separate test conversation. A successful
`login status` alone is insufficient: during this incident it succeeded while
`account/read` returned no account. If restoring credentials from an existing
authorized desktop sign-in, keep all transfers local and files mode 0600.

Preserve inbox offsets, proposal receipts and conversation history. Do not
replay completed requests or approve proposals as a recovery test. After restart,
send `/status` and a short text message to https://t.me/coach_trainerhub_bot; expect
the status reply, a processing acknowledgment and then a completed response.
This initial path-only repair remained tied to the installed app layout; the
subsequent stability hardening above removes that dependency.

## Original cutover — 2026-09-08

Source branch: `codex/telegram-coach`, [PR #66](https://github.com/bribergey/brian-training/pull/66).
The replacement Mac service is running and owns the existing Telegram bot.
Runtime release: `e05cb45e5dd928a46db1c94e713ca8da02796f37` ([progress fix PR #67](https://github.com/bribergey/brian-training/pull/67)).
Launch agent: `com.briqtraining.coach`; its independent caffeinate parent is active.
OpenClaw's coach account is disabled and explicitly stopped. The migration test
was delivered to Brian's existing chat. His reply and the completed coaching
response were verified; cutover acceptance is complete.
Brian chose this Mac and the existing Telegram bot. Coach permanently uses
`Asia/Shanghai` (China time), including while Brian travels; do not ask again. Existing bot: `@coach_trainerhub_bot`.

At cutover, the app-bundled CLI at
`/Applications/ChatGPT.app/Contents/Resources/codex` was version 0.153.4 and accepted
managed ChatGPT sign-in in an isolated coach home. GPT-6 Astra is available on
the account. The unrelated `/usr/local/bin/codex` wrapper is broken; do not use it.

## Verified implementation results

- 21 local regression tests pass, including per-set completeness, numeric UI
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
feedback. The real monthly request finished successfully in roughly nine minutes,
and its validated proposal was delivered with an approval button before restart.
The new release resumed the same conversation and retained that proposal. No
production program was written by the fix. Roadmap record:
https://app.notion.com/p/3d5e5cb920a581aaa48fd909b55908b1.

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

Pin and rehearse the CLI package first, then set the private config's
`codex_binary` to the returned immutable path. After committing the source, run
`python3 coach/stage_release.py`. It verifies the pinned package and copies
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
