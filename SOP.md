# Digital Picture Frame Program - Sprint Sequence (Standard Operating Procedure)

This sequence governs the state machine interactions between the crew members to ensure disciplined Integration & Test (I&T) lifecycles.

## Phase 1: Requirements & Design (Dev Handoff)
1. Lead receives intent from Director.
2. Lead tasks Developer to generate a "Proposed Change Set" (Lua/Ansible/Config).
3. Developer returns code. Lead reviews for basic alignment with requirements.

## Phase 2: Pre-Integration Review (Governance Gate)
1. Lead checks the Audit Tool for the current FS state (RO/RW).
2. If Read-Write is required, Lead pauses and triggers `request_director_approval`.
3. Lead only proceeds once the Director authorizes the "Maintenance Window."

## Phase 3: Deployment (I&T Execution)
1. Lead hands the "Approved Change Set" to the I&T Engineer.
2. I&T Engineer executes `run_ansible_task`.
3. I&T Engineer reports the raw logs back to the Lead.

## Phase 4: Verification & Validation (QA Audit)
1. Lead tasks the QA Auditor to verify the deployment.
2. QA Auditor runs `get_pi_telemetry` and independently confirms the "Golden State."
3. If QA reports a "Non-Conformance" (NCR), Lead loops back to Phase 1.

## Phase 5: Release & Closeout
1. Lead tasks I&T Engineer to re-enable Overlay FS (Read-Only) to "Freeze" the build.
2. Lead provides the final "Status-Risk-Path" report to the Director.

## Final Project Checklist: "Digital Picture Frame Program"
- **Human-in-the-Loop:** Kyle Mercer (Director)
- **Orchestration:** Hierarchical (Lead -> Dev/I&T/QA)
- **Safety:** Read-Only Overlay FS / Kasa Smart Plug FDIR
- **Verification:** Independent QA Telemetry
