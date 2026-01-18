from negotiationarena.alternating_game import AlternatingGameEndsOnTag
from negotiationarena.game_objects.goal import BuyerGoal
from negotiationarena.game_objects.resource import Resources
from negotiationarena.constants import (
    REASONING_TAG,
    PLAYER_ANSWER_TAG,
    MESSAGE_TAG,
    PROPOSAL_COUNT_TAG,
    PROPOSED_TRADE_TAG,
    RESOURCES_TAG,
    GOALS_TAG,
    ACCEPTING_TAG,
)

from negotiationarena.utils import extract_multiple_tags
from games.buy_sell_game.prompt import buy_sell_prompt
from negotiationarena.parser import ExchangeGameDefaultParser
from negotiationarena.agent_message import AgentMessage

BUYER_ALIGN_PROMPT = """
YYou are Player BLUE, the BUYER.

Player RED is selling exactly one object: X.
You give ZUP to buy X.

You MUST strictly follow the response format, tag names, ordering,
and rules exactly as specified by the game.
Any deviation will result in failure.

Your objective is to acquire X for the LOWEST possible ZUP
while maximizing buyer surplus and avoiding premature commitment.

----------------------------------------------------------------
MANDATORY ALIGN-STYLE DECOMPOSED NEGOTIATION PROCESS (BUYER)
----------------------------------------------------------------

At EVERY turn, you MUST internally follow these stages:

1) PLANNER (buyer strategy)
2) SELLER OUTPUT PARSER
3) LATENT BELIEF INFERENCE (Θ)
4) CONFIDENCE & UNCERTAINTY ESTIMATION (C)
5) PREFERENCE ALIGNMENT ASSESSMENT
6) SELLER-BELOW-TARGET LOCK (SB-TL)
7) DIALOGUE GENERATION
8) EVALUATOR
9) MEMORY

Only the final decision appears in <player answer>.

----------------------------------------------------------------
1) PLANNER — BUYER STRATEGY
----------------------------------------------------------------

Internally determine:

- MAX_WILLINGNESS_TO_PAY (private)
- TARGET_PRICE (ideal buyer outcome)
- WALK_AWAY_PRICE (absolute upper bound)
- MAX_CONCESSION_STEP
- Remaining proposal budget (max = 4)

Planner rules:
- NEVER propose above WALK_AWAY_PRICE
- Buyer offers must increase monotonically
- NEVER concede more than MAX_CONCESSION_STEP
- Commitment decisions must be justified by belief confidence
  or proposal budget pressure

----------------------------------------------------------------
2) SELLER OUTPUT PARSER
----------------------------------------------------------------

From Player RED’s last response, extract:

- Seller action: PROPOSAL / ACCEPT / REJECT
- If PROPOSAL: seller_price_last (ZUP)
- Direction and size of seller concessions
- Behavioral signals (firmness, urgency, consistency)
- Remaining negotiation risk

If seller ACCEPTED → ACCEPT immediately  
If seller REJECTED → STOP (game ends)

----------------------------------------------------------------
3) LATENT BELIEF INFERENCE — Θ (DISTRIBUTIONAL)
----------------------------------------------------------------

Maintain a latent belief state Θ representing a DISTRIBUTION
(or bounded interval) over the seller’s hidden heuristics.

Θ MUST be updated every turn and MUST be written explicitly
inside <reason>.

Θ includes belief ranges, not point values:

- Θ_cost ∈ [low, high] : plausible seller production cost
- Θ_min_price ∈ [low, high] : plausible seller walk-away price
- Θ_concession_rate ∈ {low, medium, high}
- Θ_urgency ∈ {low, medium, high}
- Θ_rationality ∈ {consistent, noisy}

Θ is updated using observed behavioral signals:
- Concessions narrow Θ_min_price downward
- Repeated firmness shifts Θ_min_price upward
- Consistency narrows uncertainty bands

Θ is PRIVATE and must never be revealed.

----------------------------------------------------------------
4) CONFIDENCE & UNCERTAINTY ESTIMATION — C
----------------------------------------------------------------

Maintain confidence values C ∈ [0,1] describing how tight
the belief intervals in Θ have become.

Track at minimum:
- C_min_price : confidence in Θ_min_price bounds
- C_cost : confidence in Θ_cost bounds

Interpretation:
- Low C → high uncertainty → prefer information-gathering
- High C → low uncertainty → allow commitment

There is NO hard confidence threshold.
Confidence should SOFTLY influence decisions.

----------------------------------------------------------------
5) PREFERENCE ALIGNMENT ASSESSMENT (ALIGN CORE)
----------------------------------------------------------------

At every turn, assess inferred preference alignment between
buyer and seller.

Estimate qualitatively:
- Expected buyer utility over Θ
- Expected seller acceptability over Θ
- Preference misalignment trend:
    {diverging, stable, converging}

Prefer actions that:
- Increase expected buyer surplus (BSE)
- Reduce misalignment when confidence is high
- Gather information when misalignment is unclear

This assessment MUST be mentioned in <reason>.

----------------------------------------------------------------
6) SELLER-BELOW-TARGET LOCK (SB-TL) — HARD CONSTRAINT
----------------------------------------------------------------

Define:
- seller_price_last = last ZUP proposed by Player RED

HARD RULE:
- Buyer MUST NEVER propose a price higher than seller_price_last.

Formally:
- buyer_proposed_price_t ≤ seller_price_last

This constraint OVERRIDES:
- urgency
- confidence
- proposal budget pressure

If no feasible proposal exists under SB-TL:
- Buyer may only ACCEPT or REJECT.

SB-TL status MUST be logged in <reason>.

----------------------------------------------------------------
7) DIALOGUE GENERATION
----------------------------------------------------------------

Generate exactly ONE of:

A) PROPOSAL — a counter-offer respecting SB-TL
B) ACCEPT — commitment justified by belief + alignment
C) REJECT — only if no feasible agreement remains

Dialogue rules:
- NEVER reveal Θ, C, or WALK_AWAY_PRICE
- Low confidence → exploratory, patient tone
- High confidence + alignment → firm, decisive tone

----------------------------------------------------------------
8) EVALUATOR — BUYER SAFETY CHECK
----------------------------------------------------------------

Before finalizing response, verify:

- Proposed ZUP ≤ WALK_AWAY_PRICE
- Proposed ZUP ≤ seller_price_last (SB-TL)
- ZUP increase ≤ MAX_CONCESSION_STEP
- Proposal is not dominated by earlier buyer offers
- Action is consistent with belief, confidence, and alignment

If checks fail:
- Regenerate proposal
- Or REJECT if negotiation space is exhausted

----------------------------------------------------------------
9) MEMORY — WITHIN-GAME ADAPTATION
----------------------------------------------------------------

Track:
- Seller price trajectory
- Θ interval tightening over time
- Confidence evolution
- Preference alignment trend
- Remaining proposals

Use memory to:
- Delay commitment under uncertainty
- Converge efficiently when beliefs stabilize
- Avoid regretful overbidding

----------------------------------------------------------------
OUTPUT FORMAT (ABSOLUTE — MUST MATCH SELLER)
----------------------------------------------------------------

ALL responses MUST include the following tags
IN THIS EXACT ORDER:

<proposal count> [integer, inclusive of current] </proposal count>
<my resources> [current buyer resources] </my resources>
<my goals> Buy X for minimum ZUP </my goals>
<reason>
You MUST explicitly include:

1) Planner thresholds
2) Parsed seller price
3) Θ belief intervals
4) Confidence values C
5) Preference alignment trend
6) Seller-Below-Target Lock status
7) How Θ, C, and alignment influenced the action
8) Evaluator checks

This text is PRIVATE and not shared with the seller.
</reason>
<player answer>
[ONE OF: PROPOSAL | ACCEPT | REJECT]
</player answer>
<newly proposed trade>
[If PROPOSAL:
 Player RED Gives X: 1 | Player BLUE Gives ZUP: integer_amount
If ACCEPT or REJECT: NONE]
</newly proposed trade>
<message>
[Human-readable buyer message to seller]
</message>

DO NOT omit tags.
DO NOT reorder tags.
DO NOT change tag names.
DO NOT use decimals.

----------------------------------------------------------------
BUYER WINNING HEURISTICS (ALIGN-CONSISTENT)
----------------------------------------------------------------

- Never bid against the seller’s last move
- Exploit uncertainty early
- Prefer information-gathering under low confidence
- Commit only when beliefs converge
- Optimize buyer surplus, not just agreement rate

----------------------------------------------------------------
END OF BUYER PROMPT
----------------------------------------------------------------
"""

class BuySellGameDefaultParser(ExchangeGameDefaultParser):
    def __init__(self):
        super().__init__()

    def instantiate_prompt(
        self,
        resources_available_in_game,
        starting_initial_resources,
        player_goal,
        maximum_number_of_proposals,
        player_social_behaviour,
    ):
        if isinstance(player_goal, BuyerGoal):
          return BUYER_ALIGN_PROMPT
        return buy_sell_prompt(
            resources_available_in_game,
            starting_initial_resources,
            player_goal,
            maximum_number_of_proposals,
            player_social_behaviour,
        )

    def parse(self, response):
        """
        Parse the response from the player. We are going to extract multiple lines of text from
        different tags.

        For example, we extrac <REASONING_TAG> reasoning from the model. </REASONING_TAG>

        :param response:
        :return:
        """
        (
            resources,
            goal,
            reasoning,
            answer,
            message,
            proposal_count,
            trade,
        ) = extract_multiple_tags(
            response,
            [
                RESOURCES_TAG,
                GOALS_TAG,
                REASONING_TAG,
                PLAYER_ANSWER_TAG,
                MESSAGE_TAG,
                PROPOSAL_COUNT_TAG,
                PROPOSED_TRADE_TAG,
            ],
        )
        resources = Resources.from_string(resources)
        trade = self.parse_trade(response, PROPOSED_TRADE_TAG)

        # create the message, we are going to split between public messages and secret messages.

        ms = AgentMessage()

        for tag, content in zip(
            [MESSAGE_TAG, PLAYER_ANSWER_TAG, PROPOSED_TRADE_TAG],
            [message, answer, trade],
        ):
            ms.add_public(tag, content)

        for tag, content in zip(
            [RESOURCES_TAG, GOALS_TAG, REASONING_TAG, PROPOSAL_COUNT_TAG],
            [resources, goal, reasoning, proposal_count],
        ):
            ms.add_secret(tag, content)

        return ms


class BuySellGame(AlternatingGameEndsOnTag):
    def __init__(
        self,
        player_goals,
        player_starting_resources,
        player_social_behaviour,
        player_conversation_roles,
        game_interface=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # we compute the set of resources available in game.
        # this is done just to "inform" the agents of the resources available in the game.
        resources_support_set = {}

        if len(player_starting_resources[0].resource_dict) > 1:
            raise ValueError(
                "Only one resource is supported due to rendering in the prompt. Update the prompt to support more resources"
            )

        for resource in player_starting_resources[0].resource_dict:
            resources_support_set[resource] = 0

        resources_support_set = Resources(resources_support_set)

        self.game_state = [
            {
                "current_iteration": "START",
                "turn": "None",
                "settings": dict(
                    resources_support_set=resources_support_set,
                    player_goals=player_goals,
                    player_initial_resources=player_starting_resources,
                    player_social_behaviour=player_social_behaviour,
                    player_roles=player_conversation_roles,
                    player_valuation=[g.get_valuation() for g in player_goals],
                ),
            }
        ]

        # we are going to set all the parameter we might need later
        self.resources_support_set = resources_support_set
        self.player_goals = player_goals
        self.player_starting_resources = player_starting_resources
        self.player_social_behaviour = player_social_behaviour
        self.player_conversation_roles = player_conversation_roles

        self.game_interface = (
            BuySellGameDefaultParser()
            if game_interface is None
            else game_interface
        )

        # init players
        self.init_players()

    def init_players(self):
        settings = self.game_state[0]["settings"]
        for idx, player in enumerate(self.players):
            game_prompt = self.game_interface.instantiate_prompt(
                resources_available_in_game=settings[
                    "resources_support_set"
                ].only_keys(),
                starting_initial_resources=settings[
                    "player_initial_resources"
                ][idx],
                player_goal=settings["player_goals"][idx],
                maximum_number_of_proposals=self.iterations // 2 - 1,
                player_social_behaviour=settings["player_social_behaviour"][
                    idx
                ],
            )

            player.init_agent(game_prompt, settings["player_roles"][idx])

    def after_game_ends(self):
        """
        This method is called after the game ends. For example
        the agent has accepted.

        This method can be much simpler if you don't want to compute the outcome of the game.

        :return:
        """
        end_state = self.game_state[-1]

        # if there is only one iteration, we are going to set the game state to END
        if int(end_state["current_iteration"]) <= 1:
            datum = dict(
                current_iteration="END",
                turn="None",
            )
            self.game_state.append(datum)
        else:
            # we compute the outcome of the game

            player_response = end_state["player_public_info_dict"][
                PLAYER_ANSWER_TAG
            ]
            initial_resources = self.game_state[0]["settings"][
                "player_initial_resources"
            ]
            player_valuation = self.game_state[0]["settings"][
                "player_valuation"
            ]
            player_goals = self.game_state[0]["settings"]["player_goals"]
            proposed_trade = self.game_state[-2]["player_public_info_dict"][
                PROPOSED_TRADE_TAG
            ]

            if player_response == ACCEPTING_TAG:
                # get proposed trade
                print(self.game_state)
                final_resources = [
                    proposed_trade.execute_trade(res, idx)
                    for idx, res in enumerate(initial_resources)
                ]
            else:
                final_resources = initial_resources

            outcome = [
                v.value(final - initial)
                for v, initial, final in zip(
                    player_valuation, initial_resources, final_resources
                )
            ]

            datum = dict(
                current_iteration="END",
                turn="None",
                summary=dict(
                    player_goals=player_goals,
                    player_initial_resources=initial_resources,
                    proposed_trade=proposed_trade,
                    player_valuation=player_valuation,
                    final_response=player_response,  # ACCEPT / REJECT / NONE
                    final_resources=final_resources,
                    player_outcome=outcome,
                ),
            )

            self.game_state.append(datum)
