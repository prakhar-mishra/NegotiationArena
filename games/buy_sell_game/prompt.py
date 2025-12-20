from negotiationarena.constants import *

BUYER_ALIGN_PROMPT = """
You are Player BLUE, the BUYER.

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

- Θ_cost ∈ [low, high]
- Θ_min_price ∈ [low, high]
- Θ_concession_rate ∈ {low, medium, high}
- Θ_urgency ∈ {low, medium, high}
- Θ_rationality ∈ {consistent, noisy}

Θ is PRIVATE and must never be revealed.

----------------------------------------------------------------
4) CONFIDENCE & UNCERTAINTY ESTIMATION — C
----------------------------------------------------------------

Maintain confidence values C ∈ [0,1].

Track at minimum:
- C_min_price
- C_cost

----------------------------------------------------------------
5) PREFERENCE ALIGNMENT ASSESSMENT
----------------------------------------------------------------

Assess inferred alignment:
- Buyer expected utility
- Seller acceptability
- Alignment trend: {diverging, stable, converging}

----------------------------------------------------------------
6) SELLER-BELOW-TARGET LOCK (SB-TL)
----------------------------------------------------------------

HARD RULE:
buyer_proposed_price_t ≤ seller_price_last

If violated → only ACCEPT or REJECT allowed.

----------------------------------------------------------------
7) DIALOGUE GENERATION
----------------------------------------------------------------

Generate exactly ONE:
- PROPOSAL
- ACCEPT
- REJECT

----------------------------------------------------------------
8) EVALUATOR
----------------------------------------------------------------

Verify:
- ZUP ≤ WALK_AWAY_PRICE
- ZUP ≤ seller_price_last
- ΔZUP ≤ MAX_CONCESSION_STEP

----------------------------------------------------------------
9) MEMORY
----------------------------------------------------------------

Track seller trajectory, Θ tightening, confidence, alignment.

----------------------------------------------------------------
OUTPUT FORMAT (ABSOLUTE)
----------------------------------------------------------------

ALL responses MUST include the following tags
IN THIS EXACT ORDER:

<proposal count>
<my resources>
<my goals>
<reason>
<player answer>
<newly proposed trade>
<message>

DO NOT omit or reorder tags.
DO NOT use decimals.
"""

def buy_sell_prompt(
    resources_available_in_game,
    starting_initial_resources,
    player_goal,
    maximum_number_of_proposals,
    player_social_behaviour,
):
    if player_goal == "BUYER":
        return BUYER_ALIGN_PROMPT

    prompt = f"""You are playing game where you are buying or selling an object. There is only one object for sale/purcahse.

{AGENT_ONE} is going to sell one object. {AGENT_TWO} gives {MONEY_TOKEN} to buy resources.

RULES:

```
1. You must always respond with:

    A) Propose a trade with (you can only trade in integer amounts, not decimals):
    <{PLAYER_ANSWER_TAG}> PROPOSAL </{PLAYER_ANSWER_TAG}>
    <{PROPOSED_TRADE_TAG}> {AGENT_ONE} Gives {resources_available_in_game}: amount, ...| {AGENT_TWO} Gives {MONEY_TOKEN}: amount </{PROPOSED_TRADE_TAG}>

    B) Accept the trade by saying:
    <{PLAYER_ANSWER_TAG}> {ACCEPTING_TAG} </{PLAYER_ANSWER_TAG}>
    <{PROPOSED_TRADE_TAG}> NONE </{PROPOSED_TRADE_TAG}>

    C) Reject and end the game:
    <{PLAYER_ANSWER_TAG}> {REJECTION_TAG} </{PLAYER_ANSWER_TAG}>
    <{PROPOSED_TRADE_TAG}> NONE </{PROPOSED_TRADE_TAG}>

    Note: The game will end if one of the players {ACCEPTING_TAG} OR {REJECTION_TAG}. This means that you have to be careful about both accepting, rejecting and proposing a trade.

2. You are allowed at most {maximum_number_of_proposals} proposals of your own to complete the game, after which you can only reply with {ACCEPTING_TAG} or {REJECTION_TAG}.
DO NOT propose a new trade after {maximum_number_of_proposals} proposals. Your limit for proposals is {maximum_number_of_proposals}.

3. You can reason step by step on why you are A) proposing, B) rejecting and C) accepting a trade with:

<{REASONING_TAG}> [add reasoning] </{REASONING_TAG}> add as much text as you want

This information will not be sent to the other player. It is just for you to keep track of your reasoning.

4. At each turn send messages to each other by using the following format:

<{MESSAGE_TAG}>your message here</{MESSAGE_TAG}>

You can decide if you want disclose your resources, goals, cost and willingness to pay in the message.
```

Here is what you have access to:
```
Object that is being bought/sold: {resources_available_in_game}
<{RESOURCES_TAG}> {starting_initial_resources} </{RESOURCES_TAG}>
<{GOALS_TAG}> {player_goal} </{GOALS_TAG}>,
```

All the responses you send should contain the following and in this order:

```
<{PROPOSAL_COUNT_TAG}> [add here (inclusive of current)] </{PROPOSAL_COUNT_TAG}>
<{RESOURCES_TAG}> [add here] </{RESOURCES_TAG}>
<{GOALS_TAG}> [add here] </{GOALS_TAG}>
<{REASONING_TAG}> [add here] </{REASONING_TAG}>
<{PLAYER_ANSWER_TAG}> [add here] </{PLAYER_ANSWER_TAG}>
<{PROPOSED_TRADE_TAG}> [add here] </{PROPOSED_TRADE_TAG}>
<{MESSAGE_TAG}> [add here] </{MESSAGE_TAG}
```

Please be sure to include all.

{player_social_behaviour}
"""

    return prompt
