"""
Common good game applied to river restoration using oTree.

Players contribute each round (0-10 UM). Group contribution determines
ecological efficiency level (thresholds scale by number of player n). Before round 4, players vote
on a minimum contribution tax (4 UM); if passed, it applies to round 4 onwards. If not, playerscan vote again on
round 5. Budgets carry across rounds. Final page shows the player's final budget, the river state,
 and a Lorenz curve with Gini coefficient.
"""

from otree.api import *
import json


# ---------------------------- Constants ----------------------------


class C(BaseConstants):
    """Game constants and UI limits."""

    NAME_IN_URL = "tragedie_des_communs_ecologie"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5

    START_BUDGET = cu(50)  # initial budget at round 1

    CONTRIB_MIN = cu(0)
    CONTRIB_MAX = cu(10)

    THRESHOLD_RATIOS = (0.3, 0.5, 0.7, 0.9)  # ratios for S1..S4 thresholds
    # Thresholds are based on n:
    # S1: 0 < T < 3n
    # S2: 3n+1 < T < 5n
    # S3: 5n+1 < T < 7n
    # S4: 7n+1 < T < 9n
    # S5: 9n < T

    BONUS_BY_LEVEL = (cu(-7), cu(-4), cu(0), cu(5), cu(7))  # per-player bonus
    TAX_MIN_CONTRIB = cu(4)  # minimum contribution when tax is enacted


# ---------------------------- Subsession ----------------------------


class Subsession(BaseSubsession):
    """Round-level state (tax is tracked per group, see Group.tax_enacted)."""

    pass


def creating_session(subsession: BaseSubsession):
    """Initialize per-round state and carry forward `budget_before`."""

    for p in subsession.get_players():
        if subsession.round_number == 1:
            p.budget_before = C.START_BUDGET
        else:
            prev_player = p.in_round(subsession.round_number - 1)
            if prev_player.budget_after is not None:
                p.budget_before = prev_player.budget_after
            else:
                # Fallback keeps play going if a prior payoff/budget is missing in tests.
                p.budget_before = (
                    prev_player.budget_before + prev_player.payoff
                    if prev_player.payoff
                    else prev_player.budget_before
                )


# ---------------------------- Group and players ----------------------------


def apply_vote(group: BaseGroup):
    """Apply simple-majority vote to set the group's tax flag for THIS round and seed next round."""
    players = group.get_players()
    yes = sum(1 for p in players if p.vote_tax)
    enacted = yes >= len(players) / 2
    group.tax_enacted = enacted

    # Persist to next round so round-5 knows the outcome immediately
    if group.round_number < C.NUM_ROUNDS:
        next_group = group.in_round(group.round_number + 1)
        next_group.tax_enacted = enacted


class Group(BaseGroup):
    """Group-level state and methods to compute efficiency levels and payoffs."""

    tax_enacted = models.BooleanField(
        initial=False
    )  # persists across rounds via creating_session
    total_contribution = models.CurrencyField()
    bonus_per_player = models.CurrencyField()
    n_players = models.IntegerField()
    efficiency_level = models.IntegerField()
    S1 = models.CurrencyField()
    S2 = models.CurrencyField()
    S3 = models.CurrencyField()
    S4 = models.CurrencyField()

    def compute_thresholds(self):
        """Compute thresholds S1..S4 based on number of players and THRESHOLD_RATIOS."""
        n = len(self.get_players())
        self.n_players = n

        # max total contribution if everyone gives CONTRIB_MAX
        max_total = float(C.CONTRIB_MAX) * n

        r1, r2, r3, r4 = C.THRESHOLD_RATIOS
        # integers (UM) for thresholds; adjust rounding policy if you prefer floor/ceil
        self.S1 = cu(int(round(r1 * max_total)))
        self.S2 = cu(int(round(r2 * max_total)))
        self.S3 = cu(int(round(r3 * max_total)))
        self.S4 = cu(int(round(r4 * max_total)))

    def classify_level(self):
        """Classify efficiency level based on total contribution and thresholds."""
        x = float(self.total_contribution)
        s1 = float(self.S1)
        s2 = float(self.S2)
        s3 = float(self.S3)
        s4 = float(self.S4)

        if x < s1:
            lvl = 0  # ecological collapse: -7
        elif x < s2:
            lvl = 1  # sustained degradation: -4
        elif x < s3:
            lvl = 2  # stability: 0
        elif x < s4:
            lvl = 3  # improvement: +5
        else:
            lvl = 4  # strong improvement: +7

        self.efficiency_level = lvl
        self.bonus_per_player = C.BONUS_BY_LEVEL[lvl]


def set_payoffs(group: BaseGroup):
    """Compute total contribution, classify efficiency level, apply fines/bonuses,
    but never let any player's budget_after go below 0."""
    players = group.get_players()

    # total contributions for the round
    group.total_contribution = sum((p.contribution or cu(0)) for p in players)

    group.compute_thresholds()
    group.classify_level()

    tax_active = bool(getattr(group.subsession, "tax_enacted", False))

    for p in players:
        contrib = p.contribution or cu(0)
        budget_before = p.budget_before or cu(0)

        # determine fine (only if tax active AND player could have paid the minimum)
        fine = cu(0)
        if (
            tax_active
            and contrib < C.TAX_MIN_CONTRIB
            and budget_before >= C.TAX_MIN_CONTRIB
        ):
            fine = C.TAX_MIN_CONTRIB

        # raw budget after applying contribution, ecological bonus/penalty and fine
        raw_budget_after = budget_before - contrib + group.bonus_per_player - fine

        # CAP: budgets may not go below zero
        budget_after_capped = max(cu(0), raw_budget_after)

        # set payoff to reflect the actual change in budget this round
        # (keep it as a Currency value)
        p.payoff = budget_after_capped - budget_before

        # persist capped budget
        p.budget_after = budget_after_capped

class Player(BasePlayer):
    """Player-level fields and methods."""

    contribution = models.CurrencyField(
        label="Combien souhaitez-vous investir dans la restauration du cours d'eau ?",
        min=0,
        max=10,
    )
    vote_tax = models.BooleanField(
        label="Souhaitez-vous voter pour l'instauration de la taxe ?",
        choices=[
            [False, "Non"],
            [True, "Oui"],
        ],
    )
    budget_before = models.CurrencyField()
    budget_after = models.CurrencyField()

    def contribution_min(self):
        """Minimum contribution based on no negative budget."""
        return C.CONTRIB_MIN

    def contribution_max(self):
        """Maximum contribution based on current budget; fallback if budget is missing."""
        budget = self.field_maybe_none("budget_before")
        if budget is None:
            if self.round_number == 1:
                budget = C.START_BUDGET
            else:
                prev = self.in_round(self.round_number - 1)
                budget = prev.budget_after if prev.budget_after else C.START_BUDGET
        return max(C.CONTRIB_MIN, min(C.CONTRIB_MAX, budget))


# -------------------- Pages --------------------


def vote_is_displayed(player: Player) -> bool:
    """
    Voting appears:
    - Round 4: always.
    - Round 5: only if tax was NOT enacted for this player's group in round 4.
    """
    if player.round_number == 4:
        return True
    if player.round_number == 5:
        return not bool(player.group.tax_enacted)
    return False


class VoteTax(Page):
    """Page for voting on minimum contribution tax."""

    form_model = "player"
    form_fields = ["vote_tax"]

    @staticmethod
    def is_displayed(player: Player):
        return vote_is_displayed(player)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            note=(
                "Le vote à la majorité simple détermine si une taxe minimale de "
                f"{C.TAX_MIN_CONTRIB} UM s'applique immédiatement et pour les prochains tours."
            )
        )


class VoteWait(WaitPage):
    """Wait for all players to vote and apply the vote result."""

    after_all_players_arrive = "apply_vote"

    @staticmethod
    def is_displayed(player: Player):
        return vote_is_displayed(player)


class Discussion(Page):
    """Discussion page: allows players to communicate before next rounds."""

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3


class Contribute(Page):
    """Page for contribution decision."""

    form_model = "player"
    form_fields = ["contribution"]

    @staticmethod
    def vars_for_template(player: Player):
        budget = player.field_maybe_none("budget_before") or C.START_BUDGET
        # Show warning only when the tax is active in THIS round.
        return dict(
            current_budget=int(budget),
            show_tax_warning=bool(player.group.tax_enacted),
        )

    @staticmethod
    def error_message(player: Player, values):
        """Server-side validation for contribution form."""
        contrib = values.get("contribution")
        if contrib is None:
            return
        budget = player.field_maybe_none("budget_before")
        if budget is None:
            budget = C.START_BUDGET
        # ensure contribution is not larger than available budget
        if contrib > budget:
            return {
                "contribution": (
                    f"Vous ne pouvez pas contribuer plus que votre budget actuel ({int(budget)} UM)."
                )
            }

class ResultsWaitPage(WaitPage):
    """Wait for everyone's contribution to compute playoffs."""

    after_all_players_arrive = "set_payoffs"


class Results(Page):
    """Propagate budget_after to next round's budget_before.
    Done here (not creating_session) to ensure set_payoffs has already computed budget_after."""

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Set budget_before for NEXT round (if not last round)
        if player.round_number < C.NUM_ROUNDS:
            next_player = player.in_round(player.round_number + 1)
            next_player.budget_before = player.budget_after


class FinalResults(Page):
    """Final page: displays player's final budget and Lorenz curve with Gini coefficient."""

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        # final budgets for the final round
        players_final_round = player.subsession.get_players()
        final_budgets = [
            float(p.budget_after) for p in players_final_round if p.budget_after is not None
        ]

        # Compute average contribution for each round
        avg_contribs = []
        for r in range(1, C.NUM_ROUNDS + 1):
            subs = player.in_round(r).subsession
            contribs = [float(p.contribution or 0) for p in subs.get_players()]
            avg = round(sum(contribs) / len(contribs), 2) if contribs else 0.0
            avg_contribs.append(avg)

        # Compute the overall average (NEW)
        avg_contribs_mean = round(sum(avg_contribs) / len(avg_contribs), 2) if avg_contribs else 0.0

        return dict(
            final_budget=player.budget_after,
            final_budgets_json=json.dumps(final_budgets),
            avg_contribs=avg_contribs,
            avg_contribs_mean=avg_contribs_mean,  # NEW
        )


# ---------------------------- Page sequence ----------------------------

page_sequence = [
    VoteTax,
    VoteWait,
    Discussion,
    Contribute,
    ResultsWaitPage,
    Results,
    FinalResults,
]
