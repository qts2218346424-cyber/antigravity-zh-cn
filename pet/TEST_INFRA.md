# E2E Test Infra: Antigravity Desktop Pet

## Test Philosophy
- Opaque-box and requirement-driven, derived strictly from user requirements (R1-R4) in `ORIGINAL_REQUEST.md`.
- Headless execution with zero external UI or network dependencies: tests run cleanly in any CI/CD environment or local terminal via standard `python test_account_switcher.py`.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Scenarios.
- Zero-corruption safety: All tests execute against sandboxed temporary directories via `tempfile.TemporaryDirectory()`, never mutating user's live `~/.gemini` or `%APPDATA%` files.

## Feature Inventory Coverage
| # | Feature | Requirement Source | Tier 1 | Tier 2 | Tier 3 |
|---|---------|-------------------|:------:|:------:|:------:|
| 1 | Window Management & Transparency | R1 & AC 34-35 | 5 | 5 | ✓ |
| 2 | Mascot Animation States | R1 & AC 34 | 5 | 5 | ✓ |
| 3 | Custom Avatar Engine & Magic-bytes | R1 & AC 36 | 5 | 5 | ✓ |
| 4 | Quota Monitoring & Status Engine | R2 & AC 39 | 5 | 5 | ✓ |
| 5 | Desktop Toast Alert & Rate-Limiting | R2 & AC 40 | 5 | 5 | ✓ |
| 6 | Profile Vault Storage & Listing | R3 & AC 43 | 5 | 5 | ✓ |
| 7 | Atomic Hot-Swapping & Backup Retention | R3 & AC 44-45 | 5 | 5 | ✓ |
| 8 | Standalone CLI & Runner Integration | R4 & AC 48 | 5 | 5 | ✓ |

## Test Architecture
- Test Runner: `test_account_switcher.py` runnable directly via `python test_account_switcher.py` or `pytest test_account_switcher.py`.
- Pass/Fail Semantics: Exit code 0 if all tests pass; non-zero exit code if any assertion fails.
- Sandboxing: Each test case creates a hermetic sandbox mimicking `~/.gemini/` and `AppData/Roaming/Antigravity/User/globalStorage/state.vscdb`.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | First-Time User Onboarding & Multi-Profile Setup | F3.1, F3.2, F2.1, F1.6 | Medium |
| 2 | High-Frequency Multi-Account Development Workflow | F3.3, F3.4, F3.5, F2.1 | High |
| 3 | Task Completion Notification & Quota Deduction | F2.4, F2.1, F1.8, F1.6 | Medium |
| 4 | Proactive Low-Quota Warning & Rescue Switch | F2.5, F3.4, F2.2, F1.8 | High |
| 5 | Fault Injection & Crash Resilience Recovery | F3.3, F3.4, F3.5 | High |
| 6 | Avatar Customization & Cross-Session Persistence | F1.7, F1.8, F1.1 | Medium |

## Coverage Thresholds
- Tier 1 (Feature Coverage): 40 test cases (5 per feature area across 8 areas)
- Tier 2 (Boundary & Corner Cases): 40 test cases (5 per feature area covering limits, zero, negative, corrupt, locked, and timeout conditions)
- Tier 3 (Cross-Feature Combinations): 12 pairwise interaction test cases
- Tier 4 (Real-World Application Scenarios): 6 end-to-end user journeys
- **Total Test Matrix: 98 rigorous automated test cases**
