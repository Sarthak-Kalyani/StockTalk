STOCKTALK --- AI Usage Rules & Project Milestones
Project: StockTalk --- B2B Inventory and Supplier Communication
Platform
Institute: G.L. Bajaj Institute of Technology & Management, Greater
Noida
Department: Computer Science & Engineering
Group ID: GC_2026_018
Session: 2026--27
Version: 1.0
Purpose: Use AI as a controlled development assistant while keeping
the codebase consistent, testable, secure, and understandable by all
four team members.

1. Purpose and Working Principles
All team members may use AI tools to plan, explain, scaffold, debug, and
test StockTalk. AI-generated code is a suggestion, not automatically
approved project code.

Core rules 1. Understand code before merging it. Every contributor
must be able to explain their changes. 2. Follow the approved PRD,
architecture, database schema, and API contracts. Do not let AI silently
expand scope. 3. Make small, reviewable changes rather than generating
the whole application at once. 4. Test each feature and its failure
cases before marking it complete. 5. Never paste secrets, real customer
data, private invoices, payment credentials, or personal information
into AI prompts. 6. Treat AI output as untrusted until reviewed for
correctness, security, licensing, and compatibility. 7. Record important
decisions in the repository so all members and future AI sessions use
the same context.
2. Source of Truth
Keep these files in the GitHub repository and update them when decisions
change:
- docs/StockTalk_PRD.md --- product scope and acceptance criteria.
- docs/ARCHITECTURE.md --- components, data flow, and technology
  choices.
- docs/DATABASE_SCHEMA.md --- tables, relationships, and migration
  notes.
- docs/API_CONTRACTS.md --- endpoints, request/response examples,
  and error formats.
- docs/DECISIONS.md --- dated decisions and reasons.
- docs/AI_RULES_AND_MILESTONES.md --- this document.
If AI suggestions conflict with these files, follow the approved
repository documentation and ask the team before changing the design.
3. Rules for Using AI
3.1 Before asking AI for code
Include: - The feature and expected user outcome. - Relevant file names
and existing code, excluding secrets. - Approved API and database
contracts. - Constraints (framework, package versions, coding style). -
Expected tests and acceptance criteria.

Ask AI to identify assumptions and missing requirements before it
generates large changes.
3.2 While generating code
- Request one feature or one small change at a time.
- Ask for complete file paths and a short explanation of each change.
- Ask it to reuse existing components and services rather than create
  duplicates.
- Ask it to include validation, error handling, loading states, and
  tests.
- Do not accept placeholder functions, fake success responses,
  hardcoded credentials, or mock data in production paths.
- Avoid adding a new library without explaining why it is needed and
  checking with the team.
- Do not let AI change database schema, authentication, payment logic,
  or API contracts without review.
3.3 Before accepting AI-generated code
The contributor must: 1. Read and understand the code. 2. Run
formatting, linting, and type/static checks where configured. 3. Run
unit or integration tests. 4. Test success, invalid input, empty state,
network/API failure, and unauthorized access as relevant. 5. Review for
security issues and accidental exposure of private data. 6. Verify that
the feature works with the current branch and existing modules. 7.
Record significant AI-assisted changes in the pull request description.
3.4 AI must not be used to
- Invent test results or claim a feature works without running it.
- Bypass authentication, authorization, payment verification, or
  file-access controls.
- Put API keys, passwords, database URLs, or payment secrets into
  source code.
- Use real customer bills, phone numbers, or personal records as
  prompts or demo data.
- Make unreviewed production database changes or destructive commands.
- Copy third-party code without checking its licence and suitability.
- Automatically merge its own changes without human review.
4. Project-Wide Engineering Rules
4.1 Git and collaboration
- Keep main deployable; do not commit unfinished features directly
  to main.
- Create short-lived branches such as feat/inventory-crud,
  feat/ocr-review, or fix/duplicate-bill.
- Use pull requests (PRs) for changes. At least one other team member
  reviews each PR.
- Keep commits focused and use descriptive messages,
  e.g. feat: add low-stock alert endpoint.
- Pull/rebase the latest shared work before integrating and resolve
  conflicts deliberately.
- Never commit .env, credentials, private bills, local database
  files, or build output.
- Maintain .env.example with variable names and safe placeholder
  values only.
4.2 Code structure and API consistency
- Agree on folder structure, naming, response formats, validation
  rules, and error handling before parallel development.
- Use one agreed authentication approach and one real-time messaging
  approach for the MVP.
- Keep business logic in backend services rather than duplicating it
  in frontend components.
- Validate input on the backend even when the frontend already
  validates it.
- Use migrations for schema changes; do not manually change shared
  databases without a migration.
- Document API changes and notify all affected members before merging.
4.3 Data and business rules
- A bill must be reviewed and confirmed before it changes inventory.
- Prevent the same bill from applying stock changes more than once.
- Record stock movements instead of silently overwriting quantity
  history.
- Store purchase price history with product identity, vendor, date,
  unit/pack size, and source.
- Keep vendor catalogue prices separate from actual transaction
  prices.
- Keep order status separate from payment status.
- Verify payment status server-side; a frontend message is not proof
  of payment.
- Use private file storage and check that only authorized conversation
  participants can access attachments.
- Vendor proximity search must support manual area search when
  location permission is unavailable.
5. Definition of Done
A task is Done only when all relevant checks are satisfied:
- [ ] Acceptance criteria in the issue or PRD are met.
- [ ] Code is committed on a feature branch and reviewed.
- [ ] Tests pass locally or in CI; any unrun tests are explicitly
  stated.
- [ ] Error, loading, empty, and unauthorized states are handled where
  applicable.
- [ ] No secrets or private data are included.
- [ ] API/schema documentation is updated if changed.
- [ ] The feature is integrated with the latest shared branch.
- [ ] A reviewer can reproduce the feature using the documented steps.
Do not mark a feature complete merely because the page looks correct or
AI says the code is finished.
6. Milestones and Exit Criteria
Timeline is a suggested sequence, not a fixed calendar. Agree on dates
with the project guide and track tasks in GitHub Issues or a project
board.
Milestone 0 --- Scope and team agreement
Deliverables - Approve PRD and MVP scope. - Confirm responsive web
app vs. native mobile requirement. - Confirm stack, repository, roles,
branch policy, and coding conventions. - Create initial architecture,
schema, and API contract documents.

Exit criteria - Every member understands the MVP. - No unresolved
disagreement about the primary stack or module ownership. - Initial
issues are created with acceptance criteria.
Milestone 1 --- Project foundation
Deliverables - React frontend and FastAPI backend skeletons. -
PostgreSQL/Supabase connection and environment configuration. -
Health-check endpoint, basic navigation, error format, and initial
CI/test setup. - .env.example, README, and local setup instructions.

Exit criteria - All four members can run the project locally. -
Frontend can call the backend. - No secrets are committed.
Milestone 2 --- Authentication and role-based profiles
Deliverables - Registration/login/logout. - Shopkeeper and vendor
roles. - Business profiles and protected routes/endpoints.

Exit criteria - Each role sees the correct screens. - Backend
rejects unauthorized access. - Profile data persists in the database.
Milestone 3 --- Inventory core
Deliverables - Product create/read/update/deactivate. - Cost price,
selling price, quantity, unit, vendor association, and minimum-stock
level. - Stock movement history and low-stock indicators.

Exit criteria - Inventory changes persist and validate correctly. -
Quantity changes are auditable. - Basic inventory tests pass.
Milestone 4 --- OCR and bill-to-inventory flow
Deliverables - Bill upload and private storage. - OCR integration
and parsing. - Review/edit confirmation screen. - Product matching, bill
history, duplicate checks, and stock movement creation.

Exit criteria - A sample invoice can be uploaded, reviewed,
corrected, and confirmed. - A duplicate submission cannot apply the same
stock increase twice. - OCR failure and unreadable bills show useful
errors without corrupting inventory.
Milestone 5 --- Vendor discovery and price history
Deliverables - Vendor profiles and product catalogue. - Search by
product, vendor name, and manual area; nearby search when location data
is available. - Historical purchase prices and price-change display.

Exit criteria - A shopkeeper can find relevant vendors. - Price
comparison uses comparable product units and clearly identifies
source/date. - Manual search works without GPS permission.
Milestone 6 --- Chat and file sharing
Deliverables - One-to-one buyer/vendor conversations. - Text
messages and permitted image/PDF attachments. - Private file access and
basic message notifications.

Exit criteria - Messages update correctly between participants. -
Non-participants cannot read conversations or access attachments. -
Invalid file types and oversized files are rejected.
Milestone 7 --- Orders and payment test flow
Deliverables - Create order, vendor response, and order status
history. - Payment provider test-mode integration. - Server-side payment
verification and transaction history.

Exit criteria - Buyer and vendor can complete a test order
workflow. - Payment pending, success, and failure states are handled. -
Payment status cannot be changed to successful solely by frontend input.
Milestone 8 --- Integration, QA, and presentation
Deliverables - End-to-end testing, bug fixes, responsive polish,
demo data, deployment, final report, and presentation. - Backup
plan/demo recording or screenshots if live external services fail.

Exit criteria - Core demo workflow passes from bill upload to
inventory update, vendor discovery, chat, order, and test payment. -
Setup and deployment instructions are documented. - Each team member can
explain their module and the system architecture.
7. Suggested Task Board Columns
Use a shared board with these columns:
1. Backlog --- approved tasks not started.
2. Ready --- requirements and acceptance criteria are clear.
3. In Progress --- one owner is actively working.
4. Review --- pull request opened; another member reviews.
5. Testing --- integrated feature is being verified.
6. Done --- definition of done is satisfied.
7. Blocked --- dependency or decision is preventing progress;
   include the reason and next action.
Every task should have one owner, priority, milestone, acceptance
criteria, and any dependencies.
8. Team Coordination Rules
- Hold a short weekly review: completed, next, blocked, and decisions
  needed.
- Agree API request/response formats before frontend and backend work
  proceeds in parallel.
- Use mock data only for temporary UI development and label it
  clearly; replace it before final acceptance.
- Integrate small changes frequently rather than waiting until all
  modules are finished.
- When blocked, share the exact error, expected behavior, actual
  behavior, and steps to reproduce---never secrets.
- Keep a decision log for changes to technology, schema, scope, or
  payment/location behavior.
- Reserve the final project period for integration and testing; do not
  schedule major new features then.
9. Standard AI Prompt Template
Copy and adapt this template when requesting development help:
Project: StockTalk
Feature/task:
User role:
Expected behavior:
Relevant files/code:
Approved API/schema contract:
Constraints and existing libraries:
Acceptance criteria:
Required tests:
Security/privacy considerations:

Please first list assumptions or missing information.
Then propose a small implementation plan.
Make only the requested change, follow existing conventions, include tests,
and identify files changed. Do not invent credentials, test results, or APIs.
10. Release Checklist
Before a demo or release, confirm:
- [ ] Registration, login, and role access work.
- [ ] Inventory quantities, cost prices, selling prices, and stock
  history are correct.
- [ ] OCR results are reviewed before stock updates.
- [ ] Duplicate bill handling is tested.
- [ ] Price history identifies vendor, date, and unit.
- [ ] Vendor search works with and without location permission.
- [ ] Chat and attachments are private to conversation participants.
- [ ] Orders and payment statuses remain separate and consistent.
- [ ] Payment verification is server-side; test mode is clearly
  labelled.
- [ ] Secrets and personal data are not present in the repository or
  demo.
- [ ] Setup, environment, testing, and deployment instructions are
  current.
- [ ] Each team member can explain their contribution.
Final Rule
Use AI to accelerate development, not to replace engineering
judgment. The team owns the code, architecture, testing, privacy, and
final demonstration. Small milestones, documented decisions, human
review, and frequent integration will keep StockTalk on track.