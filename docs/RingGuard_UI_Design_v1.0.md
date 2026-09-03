# RINGGUARD AI

UI / UX DESIGN DOCUMENT — v1.0

Based on the Juice Lab Cybersecurity Analytics Dashboard reference

# 1. Reference Design Analysis

The selected Dribbble reference is a modern cybersecurity dashboard concept by Juice Lab. The source describes it as a Security Operations Center workspace built around monitoring, investigation, prioritization and resolution. Its stated design highlights include AI-powered investigation, network topology visualization, incident management, threat intelligence analytics, real-time monitoring, data visualization, an enterprise dark UI and a modern SaaS dashboard. citeturn0search0

This makes the reference a strong visual foundation for RingGuard because RingGuard also needs an investigation-oriented workspace rather than a generic banking dashboard. The reference should be treated as visual inspiration, not copied screen-for-screen.

## Reference Palette

These colors are the palette published on the Dribbble reference. citeturn0search0

# 2. RingGuard Design Direction

RingGuard should combine the reference's cybersecurity/SOC visual language with the information architecture of a financial risk-operations product.

## Design Character

Dark, premium, enterprise-grade interface.

High information density without visual clutter.

Teal/cyan as the main intelligence accent.

Warm red/orange reserved for risk and action-required states.

Subtle borders rather than heavy card shadows.

Data visualization should communicate evidence, not merely decorate the dashboard.

The graph and investigation case should be the visual center of the product.

## What RingGuard Should Avoid

Generic AI-chatbot appearance.

Neon cyberpunk styling.

Excessive glassmorphism.

Large decorative illustrations that consume investigation space.

Too many competing accent colors.

Making the graph look like a decorative network animation.

Presenting risk probability as a guaranteed fraud verdict.

# 3. Information Architecture

RingGuard AI
│
├── Overview
│ ├── Risk Overview
│ ├── Active Cases
│ ├── Detected Networks
│ └── Business Impact
│
├── Cases
│ ├── Case Queue
│ ├── Case Detail
│ ├── Evidence
│ ├── Timeline
│ └── Decision
│
├── Networks
│ ├── Network Explorer
│ ├── Ring Clusters
│ └── Entity Relationships
│
├── Analytics
│ ├── Model Performance
│ ├── Baseline vs Graph
│ ├── False-Positive Economics
│ └── Investigation Efficiency
│
└── Audit
 ├── Tool Calls
 ├── Model Actions
 └── Human Decisions

# 4. Global Layout

┌──────────────────────────────────────────────────────────────────────┐
│ RingGuard AI Search... Notifications Analyst ▼ │
├──────────────┬───────────────────────────────────────────────────────┤
│ │ │
│ Overview │ MAIN WORKSPACE │
│ │ │
│ Cases │ │
│ Networks │ │
│ Analytics │ │
│ Audit │ │
│ │ │
│ Settings │ │
│ │ │
└──────────────┴───────────────────────────────────────────────────────┘

Recommended desktop-first canvas: 1440 × 900. The product is an analyst workstation, so desktop information density should be prioritized over mobile-first layouts.

# 5. Screen 01 — Risk Operations Overview

Purpose: Give the analyst an immediate understanding of current risk workload and business impact.

## Top KPI Row

## Main Content

Risk activity trend

Detected network clusters

Priority investigation queue

Risk distribution

Recent investigation activity

The overview should feel closer to a SOC command center than a conventional banking dashboard, while keeping the numbers financially meaningful.

# 6. Screen 02 — Case Queue

Purpose: Prioritize investigations.

## Filters

Risk level

Ring probability

Case status

Network size

Evidence type

Date range

Use compact rows, strong status indicators and fast scanning. Avoid oversized cards for each case.

# 7. Screen 03 — Hero Case Investigation

This is the most important screen in the product. It should communicate the entire RingGuard value proposition in one view.

┌─────────────────────────────────────────────────────────────────────┐
│ ← Cases CASE RG-10482 HIGH RISK 91% │
├──────────────────────────────────┬──────────────────────────────────┤
│ │ │
│ EVIDENCE GRAPH │ TOP EVIDENCE │
│ │ │
│ Account A123 │ ● Shared Device │
│ / \ │ ● Common Beneficiary │
│ Device Account B │ ● Rapid Fund Splitting │
│ \ / │ ● Coordinated Timing │
│ Beneficiary Z │ │
│ │ Evidence Strength ████████░ │
├──────────────────────────────────┴──────────────────────────────────┤
│ TIMELINE │
│ 10:02 Created → 10:17 ₹4.8L → 10:21 Split → 10:25 Device Link │
├─────────────────────────────────────────────────────────────────────┤
│ COUNTERFACTUAL RISK │
│ Transaction LOW → Behavioral MEDIUM → Network HIGH → Fund Flow HIGH │
├─────────────────────────────────────────────────────────────────────┤
│ INVESTIGATION COPILOT │
│ ✓ Account ✓ Transactions ✓ Related Accounts ✓ Fund Flow │
│ │
│ "Four accounts converge on Beneficiary Z and share Device D17." │
├─────────────────────────────────────────────────────────────────────┤
│ CLEAR CASE REQUEST MORE EVIDENCE ESCALATE │
└─────────────────────────────────────────────────────────────────────┘

## Design Rule

The analyst should understand why the case is suspicious without opening five separate screens.

# 8. Screen 04 — Evidence Graph

The graph is a functional investigation tool, not decorative visualization.

## Node Types

Account

Customer

Transaction

Device

IP

Beneficiary

Merchant

## Visual Encoding

## Graph Interactions

Click node → inspect entity

Click edge → show supporting evidence

Expand network → reveal next-hop relationships

Filter → device/IP/beneficiary/fund-flow

Focus case → hide unrelated entities

# 9. Screen 05 — Timeline

Purpose: Make the investigation understandable chronologically.

ACCOUNT CREATED
 │
 ▼
LARGE PAYMENT RECEIVED
 │
 ▼
RAPID TRANSFER TO B
 │
 ▼
RAPID TRANSFER TO C
 │
 ▼
SHARED DEVICE DISCOVERED
 │
 ▼
COMMON BENEFICIARY DISCOVERED
 │
 ▼
HUMAN REVIEW

Each event should expose the underlying record when clicked.

# 10. Screen 06 — Counterfactual Risk

This screen should visually demonstrate the core RingGuard hypothesis: network evidence can add information that is unavailable from a transaction viewed in isolation.

RISK EVOLUTION

Transaction-only
 │
 ▼
 LOW
 31%
 │
 │ + behavioral evidence
 ▼
 MEDIUM
 57%
 │
 │ + network evidence
 ▼
 HIGH
 84%
 │
 │ + coordinated fund flow
 ▼
 HIGH CONFIDENCE
 91%

The numbers above are placeholders for UI design. They must be replaced by actual model results in the final product.

# 11. Screen 07 — Investigation Copilot

The AI should not look like a general-purpose chat interface. It should look like a controlled investigation assistant.

┌────────────────────────────────────────────┐
│ INVESTIGATION COPILOT │
│ │
│ ✓ Account retrieved │
│ ✓ 12 transactions analyzed │
│ ✓ 4 related accounts found │
│ ✓ Shared device identified │
│ ✓ Common beneficiary identified │
│ ✓ Fund flow reconstructed │
│ │
│ KEY FINDING │
│ 4 accounts connect through Device D17 │
│ and converge on Beneficiary Z. │
│ │
│ [View Evidence] [View Graph] │
└────────────────────────────────────────────┘

The UI should make tool execution visible and auditable. Do not hide all agent actions behind a single AI response.

# 12. Screen 08 — Model Analytics

Purpose: Prove the technical hypothesis rather than merely displaying AI branding.

The strongest chart should visually compare baseline versus graph-enhanced performance. This is a core RingGuard differentiator.

# 13. Screen 09 — Business Impact

Purpose: Connect model performance to business value.

FRAUD LOSS AVOIDED
 ₹18.7L

FALSE-POSITIVE COST
 ₹2.4L

INVESTIGATION COST
 ₹1.1L

────────────────────

NET BUSINESS VALUE
 ₹15.2L

Every number must show or link to its underlying assumption. Do not use illustrative values in the final demo.

# 14. Screen 10 — Audit Trail

Purpose: Demonstrate that the AI investigation is controlled and reviewable.

The audit screen should reinforce trust rather than simply provide administrative logging.

# 15. Design System

## 15.1 Color System

The first six reference colors above are taken from the published Juice Lab palette. Risk-state colors should be adapted carefully for RingGuard semantics rather than copied blindly. citeturn0search0

## 15.2 Typography

Use a clean modern sans-serif.

Strong hierarchy between page title, section title, KPI, label and metadata.

Use tabular numerals for financial metrics where available.

Avoid excessively large marketing-style headings inside the application.

## 15.3 Cards

Subtle 1px borders

Low/no shadow

Compact padding

Consistent radius

Clear hierarchy between title, value and metadata

## 15.4 Icons

Use simple line icons. Icons should communicate entity type or action and should never replace textual labels for critical risk decisions.

# 16. Interaction Design

## Evidence Linking Principle

Graph → Evidence → Transaction → Timeline should be navigable in both directions.

# 17. Responsive Strategy

Primary target: desktop analyst workstation.

1440×900: primary design target

1280×800: supported

1024px+: functional tablet/compact desktop adaptation

Mobile: not an MVP priority

# 18. Accessibility & Trust

Do not rely on color alone to communicate risk.

Pair risk colors with labels/icons.

Maintain readable contrast.

Allow keyboard navigation for important controls.

Use explicit status text such as HIGH, MEDIUM, LOW.

Show evidence availability clearly.

Never hide uncertainty behind polished AI language.

# 19. Animation & Motion

Use restrained motion inspired by security-monitoring products.

Subtle graph node transitions.

Case status transitions.

Timeline reveal.

Investigation tool-call progress.

Risk-state transition for counterfactual view.

Avoid constant animated particles, excessive glowing nodes, or decorative motion. The reference's enterprise security positioning should translate into purposeful motion, not cyberpunk effects.

# 20. Recommended Navigation

Sidebar
────────────
◉ Overview
◉ Cases
◉ Networks
◉ Analytics
◉ Audit
────────────
⚙ Settings

Keep the sidebar persistent on desktop. The active section should use the teal intelligence accent.

# 21. Component Priority

# 22. Judge-Focused Visual Story

The UI should make the product story visible without requiring a long verbal explanation.

1. Transaction looks normal
 ↓
2. Network context appears
 ↓
3. Ring probability increases
 ↓
4. Evidence graph explains why
 ↓
5. Timeline reconstructs what happened
 ↓
6. AI investigates using bounded tools
 ↓
7. Analyst sees evidence-grounded explanation
 ↓
8. Human makes final decision
 ↓
9. Business impact is quantified

# 23. Recommended Reference Usage

Use the Juice Lab reference primarily for the visual language: dark enterprise UI, security-operations density, network visualization, AI investigation and structured analytics. The source itself describes the design as a focused SOC workspace for monitoring, investigating, prioritizing and resolving incidents. citeturn0search0

For RingGuard, the information architecture should be changed substantially: the primary case object is a payment-abuse/ring investigation, the graph represents financial entities and relationships, the timeline represents payment activity, and the final action is a human risk decision.

# 24. Final Design Recommendation

Recommended direction: adopt the reference's dark enterprise cybersecurity aesthetic, but build RingGuard around a financial-risk investigation workflow.

This direction is also consistent with other current Dribbble cybersecurity work, where dark enterprise dashboards emphasize risk monitoring, network visualization, threat analytics and security operations. citeturn0search4turn0search6

# 25. Figma Build Order

Create color and typography variables.

Build App Shell + Sidebar.

Build reusable KPI/Card/Table components.

Build Overview Dashboard.

Build Case Queue.

Build Case Investigation page.

Build Evidence Graph component.

Build Timeline component.

Build Counterfactual Risk component.

Build Investigation Copilot.

Build Analytics page.

Build Business Impact panel.

Build Audit Trail.

Add responsive behavior.

Add final motion and micro-interactions.

# 26. Final UI Principle

RingGuard should visually communicate one central idea:

“The AI does not simply tell the analyst that something is risky. It connects the entities, retrieves the evidence, reconstructs what happened, explains the network context, quantifies the impact, and lets the human make the final decision.”

That should be the organizing principle for every screen in the product.


| Field | Value |
| --- | --- |
| Product | RingGuard AI |
| Design Goal | Enterprise-grade AI risk investigation workspace |
| Primary User | Merchant Risk / Risk Operations Analyst |
| Visual Direction | Dark enterprise security analytics + fintech risk operations |
| Primary UX Principle | Evidence first, action second |
| Reference | Juice Lab — Cybersecurity Analytics Dashboard on Dribbble |


| Source token | Hex |
| --- | --- |
| Deep background | #02090B |
| Dark teal | #123B42 |
| Primary light | #FCFCFC |
| Muted gray | #616562 |
| Secondary gray | #9EA2A2 |
| Accent teal | #18CDBB |
| Warm alert accent | #D05322 |


| KPI | Example | Purpose |
| --- | --- | --- |
| Active Cases | 142 | Current investigation workload |
| Detected Rings | 27 | Network-level cases |
| High Risk | 18 | Priority workload |
| Fraud ₹ Prevented | ₹18.4L | Business impact |
| FP Cost | ₹2.4L | Friction/economic cost |


| Column | Content |
| --- | --- |
| Case | RG-10482 |
| Entity | Account A123 |
| Ring Risk | 91% |
| Risk Level | HIGH |
| Evidence | 7 verified |
| Network | 5 accounts |
| Status | Investigating |
| Updated | 2 min ago |


| Entity | Suggested treatment |
| --- | --- |
| Account | Primary node; highest visual prominence |
| Device | Small infrastructure node |
| IP | Small infrastructure node |
| Beneficiary | Financial destination node |
| Transaction | Event/flow marker |
| Suspicious relationship | Highlighted relationship |
| Verified evidence | Strong relationship line |
| Unavailable evidence | Do not render as confirmed |


| Metric | Transaction-only | Graph-enhanced |
| --- | --- | --- |
| PR-AUC | Actual result | Actual result |
| Precision | Actual result | Actual result |
| Recall | Actual result | Actual result |
| FP Cost | Actual result | Actual result |
| Fraud ₹ Prevented | Actual result | Actual result |


| Time | Action | Actor | Result |
| --- | --- | --- | --- |
| 10:25 | find_shared_devices() | Investigation AI | 2 accounts linked |
| 10:27 | trace_fund_flow() | Investigation AI | 3 transfers found |
| 10:29 | get_risk_features() | Investigation AI | Features retrieved |
| 10:35 | Case decision | Human analyst | Escalate |


| Token | Recommended value | Usage |
| --- | --- | --- |
| Background | Reference deep green-black / #02090B | App background |
| Surface | #0B1417 / similar | Cards and panels |
| Surface elevated | #123B42 / similar | Selected/active areas |
| Primary text | #FCFCFC | Headings |
| Secondary text | #9EA2A2 | Supporting information |
| Primary accent | #18CDBB | AI/intelligence/positive action |
| High risk | #D05322 or restrained red | Risk/action-required |
| Medium risk | Amber | Warning |
| Low / clear | Green | Legitimate/cleared |


| Interaction | Behavior |
| --- | --- |
| Hover KPI | Show definition/source |
| Click case | Open investigation workspace |
| Click graph node | Open entity drawer |
| Click graph edge | Show relationship evidence |
| Click evidence | Highlight supporting graph/timeline records |
| Click timeline event | Open source transaction/event |
| Run investigation tool | Show tool action and result |
| LLM explanation | Allow evidence drill-down |
| Decision button | Require clear confirmation |


| Priority | Components |
| --- | --- |
| P0 | App shell, sidebar, KPI cards, case table, case detail, evidence graph, timeline, risk score, decision controls |
| P1 | Investigation Copilot, counterfactual risk, analytics comparison, business-value panel, audit trail |
| P2 | Advanced network filters, historical case similarity, retrieval, richer animations |


| Element | RingGuard Decision |
| --- | --- |
| Overall aesthetic | Dark enterprise security analytics |
| Main accent | Teal/cyan intelligence accent |
| Risk accent | Restrained orange/red |
| Hero screen | Case Investigation |
| Hero visualization | Evidence Graph |
| Supporting visualization | Timeline |
| AI surface | Investigation Copilot, not chatbot |
| Proof surface | Baseline vs Graph-enhanced analytics |
| Trust surface | Evidence + Audit Trail |
| Final action | Human decision controls |
