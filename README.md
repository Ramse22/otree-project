# Tragedy of the Commons – River Restoration (oTree)

An experimental economics game built with oTree where players cooperate to restore a shared river resource. This game implements a common pool resource dilemma with dynamic contribution thresholds, group voting mechanisms, and wealth inequality analysis.

## Game Overview

Players participate in a 5-round common pool resource game with the following structure:

| Parameter | Value |
|-----------|-------|
| **Rounds** | 5 |
| **Budget per round** | Carried forward from previous contributions and payoffs |
| **Contribution range** | 0–10 UM (capped by available budget) |
| **Efficiency levels** | 5 levels, unlocked via group contribution thresholds |
| **Voting mechanism** | Tax vote in round 4; reoccurs in round 5 if round 4 fails |
| **Currency** | UM (Unité Monétaire) |

*UM = Unité Monétaire (Monetary Unit)*

### Key Mechanics

**Budget Flow**
- `budget_before → contribution/payoff → budget_after` (persists to next round)

**Group Outcomes**
- Total group contributions are mapped to 5 efficiency levels
- Thresholds scale dynamically based on group size
- Each efficiency level grants a per-player bonus

**Taxation System**
- **Vote timing:** Round 4 (mandatory); round 5 (if round 4 fails)
- **Enforcement:** Players contributing below the minimum are fined with a flat penalty equal to `TAX_MIN_CONTRIB`
- **Persistence:** Once enacted, tax persists through subsequent rounds

**Final Analysis**
- Individual final budgets for each player
- River ecological state visualization
- Lorenz curve and Gini coefficient for wealth inequality analysis

## Project Structure

```
otree-project/
├─ Tragedie_des_communs_ecologie/     # Main game app
│  ├─ __init__.py                     # Game logic, constants, models, pages
│  ├─ templates/
│  │  └─ Tragedie_des_communs_ecologie/
│  │     ├─ FinalResults.html         # Lorenz curve, Gini, river state
│  │     ├─ Results.html              # Per-round results & fines
│  │     ├─ Contribute.html           # Contribution input
│  │     ├─ VoteTax.html              # Tax voting form
│  │     └─ VoteWait.html             # Vote aggregation
├─ _static/global/                    # Global static assets
├─ _templates/global/                 # Global templates
├─ settings.py                        # Session & app configuration
├─ manage.py                          # oTree management script
├─ pyproject.toml                     # Project dependencies & metadata
├─ uv.lock                            # Pinned dependency versions
└─ README.md                          # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8+ (see `pyproject.toml` and `uv.lock` for exact versions)
- oTree

### Quick Start (Using `uv`)

If you have `uv` installed and want to match the exact development environment:

```bash
uv sync
uv run otree devserver
```

### Standard Setup (pip)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd otree-project
   ```

2. **Install dependencies:**
   ```bash
   pip install otree
   ```

3. **Launch the development server:**
   ```bash
   otree devserver
   ```

4. **Access the game:**
   - Open the link displayed in your terminal
   - Click "Create Session" to start a demo session
   - For multi-player testing, open multiple browser tabs (oTree manages split-screen simulation)

### Number of Demo Participants

The demo participant count is set in `settings.py` in the `SESSION_CONFIGS` list:

```python
SESSION_CONFIGS = [
    {
        'name': 'tragedie_des_communs_ecologie',
        'display_name': 'Tragedy of the Commons – River Restoration',
        'num_demo_participants': 3,  # Change this value
        'app_sequence': ['Tragedie_des_communs_ecologie'],
    },
]
```

When deploying to a server, you can set the number of participants when creating a session.

## Customizing Game Parameters

All game constants (budget, bonuses, tax thresholds, etc.) are defined in `Tragedie_des_communs_ecologie/__init__.py`. You can modify:

- `TAX_MIN_CONTRIB` – Minimum contribution threshold for taxation
- `INITIAL_BUDGET` – Starting budget for each player
- Efficiency level thresholds and bonuses
- Tax penalty amounts
- Round structure

## Testing with Bots

For automated testing without manual participants, oTree supports bot testing. See the [oTree bot documentation](https://otree.readthedocs.io/en/latest/bots.html) for implementation details.

## Deployment

To run this game on a production server:

1. Follow the [oTree deployment guide](https://otree.readthedocs.io/en/latest/server.html)
2. When creating a session on the server, specify the number of participants
3. Players will join via a unique session link

## Dependencies

Exact dependency versions are pinned in `uv.lock`. See `pyproject.toml` for the main dependencies:
- oTree
- Python 3.8+

## Implementation Details

### Server-Side Logic

- **Group-level tax state:** `Group.tax_enacted` (Boolean)
- **Vote display logic:**
  - Round 4: Always shown
  - Round 5: Only if round 4 vote failed
- **Payoff calculation:**
  - Sum group contributions
  - Compute efficiency level from thresholds
  - Apply bonuses and fines
  - Update player budgets
- **Final results:** JSON data exported for Lorenz/Gini visualization

## Learn More

- [oTree documentation](https://otree.readthedocs.io/)
- [oTree bot testing](https://otree.readthedocs.io/en/latest/bots.html)
- [oTree deployment](https://otree.readthedocs.io/en/latest/server.html)
