# Tragedy of the Commons – River Restoration (oTree)

**Note:** The game interface is in French. The code and documentation are in English.

This experimental economics serious game project is an application of the Tragedy of the commons to the ecological restorations of a river. This game implement a shared resource dilemna in which players are taxpayers with the same starting wealth and the same common goal: to restore the river, for the good of the community. The implementation comprises dynamic contribution thresholds, group voting mechanisms, and wealth inequality analysis (gini index and Lorenz curve). 

## Game Overview

Players participate in a 5-round common pool resource game with the following structure:

| Parameter | Value |
|-----------|-------|
| **Rounds** | 5 (information which is purposefully omitted in the player interface to not influence contribution)|
| **Budget per round** | Carried forward from previous contributions and payoffs |
| **Contribution range** | 0–10 UM (capped by available budget) |
| **Efficiency levels** | 5 levels of ecological restoration efficiency, unlocked via group contribution thresholds |
| **Voting mechanism** | Tax vote (minimal contribution of `TAX_MIN_CONTRIB` for all player) in round 4; reoccurs in round 5 if round 4 fails |
| **Currency** | UM |

*UM = Unité Monétaire (Monetary Unit)*

### Key Mechanics

**Budget Flow**
- `budget_before → contribution/payoff → budget_after` (persists to next round)

**Group Outcomes**
- Total group contributions are mapped to 5 efficiency levels
- Thresholds scale dynamically based on group size
- Each efficiency level grants a per-player bonus or malus depending on the efficiency level (maluses are capped by the player's budget, so that a player cannot have a negative net worth)

**Taxation System**
- **Vote timing:** Round 4 (mandatory); round 5 (if round 4 fails)
- **Enforcement:** Players contributing below the minimum are fined with a flat penalty equal to `TAX_MIN_CONTRIB` (the fine is not applied if the player's net worth is lower than `TAX_MIN_CONTRIB`)
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
│  │     └─ VoteWait.html             # Wait for all players to vote page
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

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ramse22/otree-project.git
   cd otree-project
   ```

2. **Install dependencies:**

#### Using `uv`

If you have `uv` installed and want to match the exact development environment:

```bash
uv sync
uv run otree devserver
```
#### Without `uv` (pip)

Add the dependencies from the `pyproject.toml`

   ```bash
   pip install -e .
   ```

3. **Launch the development server:**
   ```bash
   otree devserver
   ```
This starts a local development server. You can create demo sessions with a pre-set number of participants (configured in `settings.py`).

4. **Access the game:**

#### Actual game

   - Open the link displayed in your terminal
   - Click "Create new session" in the **Session** tab or directly in your room in the **Room** tab (room configuration is done in `settings.py`)
   - Share the room URL to your game participants. You can use **Room-wide URL** (one URL for all players) or **Single-use links** (specific link for each players).

#### Demo

   - Open the link displayed in your terminal
   - Click on the demo room (name can be changed in `settings.py`, currently set to `test_1`)
   - For multi-player testing, open multiple browser tabs (oTree manages split-screen simulation)

### Number of Demo Participants

The demo participant count is set in `settings.py` in the `SESSION_CONFIGS` list:

```python
SESSION_CONFIGS = [
    dict(
        name="test_1",
        num_demo_participants=3,   # change this value (up to 20)
        app_sequence=["Tragedie_des_communs_ecologie"],
    )
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
3. Players will join via a unique session URL or through individual single-use links

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

## Resources

- [oTree documentation](https://otree.readthedocs.io/)
- [oTree bot testing](https://otree.readthedocs.io/en/latest/bots.html)
- [oTree deployment](https://otree.readthedocs.io/en/latest/server.html)

## Credits & Acknowledgments

This project was carried out as part of the M2 final project presentation within the **PhDTrack - Transition Environnemental** program at the **ENS de Rennes**.

- **Game Design & Rules:** Klervia Gallois
- **Implementation & Development:** Marion Rosec
- **Code Assistance:** Javascript code was written with assistance from Copilot
