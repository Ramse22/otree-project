from otree.api import *
import json

class C(BaseConstants):
    NAME_IN_URL = 'tragedie_des_communs_ecologie'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 5

    ENDOWMENT = cu(100)
    START_BUDGET = cu(50)
    PER_ROUND_ENDOWMENT = cu(0)

    CONTRIB_MIN = cu(0)
    CONTRIB_MAX = cu(10)

    THRESHOLD_RATIOS = (0.3, 0.5, 0.7, 0.9)
    BONUS_BY_LEVEL = (cu(-7), cu(-4), cu(0), cu(5), cu(7))
    TAX_MIN_CONTRIB = cu(4)


class Subsession(BaseSubsession):
    tax_enacted = models.BooleanField(initial=False)


def creating_session(subsession: BaseSubsession):
    if subsession.round_number == 1:
        subsession.tax_enacted = False
    else:
        prev = subsession.in_round(subsession.round_number - 1)
        subsession.tax_enacted = bool(getattr(prev, 'tax_enacted', False))

    for p in subsession.get_players():
        if subsession.round_number == 1:
            p.budget_before = C.START_BUDGET
        else:
            prev_player = p.in_round(subsession.round_number - 1)
            if prev_player.budget_after is not None:
                p.budget_before = prev_player.budget_after
            else:
                p.budget_before = prev_player.budget_before + prev_player.payoff if prev_player.payoff else prev_player.budget_before



def apply_vote(group: BaseGroup):
    """Calculate vote result and update tax_enacted."""
    players = group.get_players()
    yes = sum(1 for p in players if p.vote_tax)
    group.subsession.tax_enacted = (yes >= len(players) / 2)


class Group(BaseGroup):
    total_contribution = models.CurrencyField()
    bonus_per_player = models.CurrencyField()
    n_players = models.IntegerField()
    efficiency_level = models.IntegerField()
    S1 = models.CurrencyField()
    S2 = models.CurrencyField()
    S3 = models.CurrencyField()
    S4 = models.CurrencyField()

    def compute_thresholds(self):
        """Calcule S1..S4 selon le nombre de joueurs présents."""
        n = len(self.get_players())
        self.n_players = n
        # Thresholds are based on n:
        # S1: 0 < T < 3n
        # S2: 3n+1 < T < 5n
        # S3: 5n+1 < T < 7n
        # S4: 7n+1 < T < 9n
        # S5: 9n < T
        self.S1 = cu(3 * n)
        self.S2 = cu(5 * n)
        self.S3 = cu(7 * n)
        self.S4 = cu(9 * n)

    def classify_level(self):
        """Fixe efficiency_level (0..4) et bonus_per_player à partir de total_contribution."""
        x = float(self.total_contribution)
        s1 = float(self.S1)
        s2 = float(self.S2)
        s3 = float(self.S3)
        s4 = float(self.S4)
        
        if x < s1:
            lvl = 0  # Effondrement écologique: -7
        elif x < s2:
            lvl = 1  # Dégradation continue: -4
        elif x < s3:
            lvl = 2  # Stabilité: 0
        elif x < s4:
            lvl = 3  # Amélioration: +5
        else:
            lvl = 4  # Amélioration avancée: +7
        
        self.efficiency_level = lvl
        self.bonus_per_player = C.BONUS_BY_LEVEL[lvl]


def set_payoffs(group: BaseGroup):
    players = group.get_players()
    group.total_contribution = sum(p.contribution for p in players)
    group.compute_thresholds()
    group.classify_level()
    for p in players:
        fine = cu(0)
        if p.subsession.tax_enacted and p.contribution < C.TAX_MIN_CONTRIB:
            fine = C.TAX_MIN_CONTRIB
        p.payoff = group.bonus_per_player - fine
        p.budget_after = p.budget_before - p.contribution + group.bonus_per_player - fine


class Player(BasePlayer):
    contribution = models.CurrencyField(
        label="Combien souhaitez-vous investir dans la restauration du cours d'eau ?",
        min=0,
        max=10,
    )
    vote_tax = models.BooleanField(label="Souhaitez-vous voter pour l'instauration de la taxe ?",choices=[
        [False, 'Non'],
        [True, 'Oui'],
    ])
    budget_before = models.CurrencyField()
    budget_after = models.CurrencyField()

    def contribution_min(self):
        # No minimum enforced by form
        return C.CONTRIB_MIN

    def contribution_max(self):
        budget = self.field_maybe_none('budget_before')
        if budget is None:
            if self.round_number == 1:
                budget = C.START_BUDGET
            else:
                prev = self.in_round(self.round_number - 1)
                budget = prev.budget_after if prev.budget_after else C.START_BUDGET
        return min(C.CONTRIB_MAX, budget)
    
# -------------------- Pages --------------------

class VoteTax(Page):
    form_model = 'player'
    form_fields = ['vote_tax']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 4

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            note=f"Le vote à la majorité simple détermine si une taxe minimale de "
                 f"{C.TAX_MIN_CONTRIB} UM s'applique à partir du prochain tour."
        )


class VoteWait(WaitPage):
    after_all_players_arrive = 'apply_vote'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 4


class Discussion(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3


class Contribute(Page):
    form_model = 'player'
    form_fields = ['contribution']

    @staticmethod
    def vars_for_template(player: Player):
        budget = player.field_maybe_none('budget_before') or C.START_BUDGET
        # show warning only when the tax is active THIS round (i.e. was set earlier and copied)
        return dict(
            current_budget=int(budget),
            show_tax_warning=bool(player.subsession.tax_enacted),
        )


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'set_payoffs'

class Results(Page):
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Set budget_before for NEXT round (if not last round)
        if player.round_number < C.NUM_ROUNDS:
            next_player = player.in_round(player.round_number + 1)
            next_player.budget_before = player.budget_after


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        # Get all players in session and their final budgets
        all_players = player.session.get_participants()
        final_budgets = [float(p.payoff_plus_participation_fee()) for p in all_players]
        
        return dict(
            final_budget=player.budget_after,
            final_budgets_json=json.dumps(final_budgets),
        )

page_sequence = [
    VoteTax,
    VoteWait,
    Discussion,
    Contribute,
    ResultsWaitPage,
    Results,
    FinalResults,
]