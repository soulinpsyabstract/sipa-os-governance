import re

# Held-out (not in any training jsonl), 2 per group, fresh numbers.
# Each question has: id, group, prompt, and a checker(response_text) -> bool.
#
# v2 (rewritten after reading raw stage6 responses): the v1 checkers were
# fragile phrase-matchers and produced both false negatives (game_theory_1:
# "6 units for Alpha and 6 units for Beta, each receiving a payoff of 0" --
# exactly correct -- scored wrong because it didn't literally contain "6 and
# 6") and false positives (probability_1: a response with a genuinely broken
# Bayes computation landed a final number that happened to fall inside the
# accepted numeric range by coincidence). Rewritten to extract the model's
# actual final claim (a number, or a decision keyword) with a tolerant
# parser, instead of matching literal substrings.


def _has(text, *needles):
    low = text.lower()
    return any(n.lower() in low for n in needles)


def _last_percent_like(text: str):
    """Return the last percentage-like value in the text as a float 0-100,
    matching '19.8%', '0.198', or a bare number right before/after '%'."""
    pct_matches = re.findall(r'(\d{1,3}(?:\.\d+)?)\s*%', text)
    if pct_matches:
        return float(pct_matches[-1])
    dec_matches = re.findall(r'\b0\.(\d{2,4})\b', text)
    if dec_matches:
        return float("0." + dec_matches[-1]) * 100
    return None


def _near(text: str, anchor: str, window: int = 40):
    """Text following each case-insensitive occurrence of anchor, up to window chars."""
    low = text.lower()
    out = []
    start = 0
    while True:
        idx = low.find(anchor.lower(), start)
        if idx == -1:
            break
        out.append(text[idx: idx + window])
        start = idx + 1
    return out


def _num_near(text: str, anchor: str, expected: int, window: int = 40) -> bool:
    """True if `expected` appears as a standalone number within `window` chars
    after (or shortly before) an occurrence of `anchor`."""
    low = text.lower()
    pat_num = re.compile(rf'\b{expected}\b')
    for idx in [m.start() for m in re.finditer(re.escape(anchor.lower()), low)]:
        segment = text[max(0, idx - 15): idx + window]
        if pat_num.search(segment):
            return True
    return False


def _decision_polarity(text: str, negative_markers, positive_markers) -> str:
    """Returns 'negative', 'positive', or 'ambiguous' based on which marker
    set is present. Negative markers win if both are present without a
    negation of the negative marker itself (rare)."""
    low = text.lower()
    has_neg = any(m in low for m in negative_markers)
    has_pos = any(m in low for m in positive_markers)
    if has_neg and not has_pos:
        return "negative"
    if has_pos and not has_neg:
        return "positive"
    if has_neg and has_pos:
        # both present -- trust whichever appears later (closer to the
        # stated final decision, since reasoning often restates the
        # opposite framing before concluding)
        neg_pos = max(low.rfind(m) for m in negative_markers if m in low)
        pos_pos = max(low.rfind(m) for m in positive_markers if m in low)
        return "negative" if neg_pos > pos_pos else "positive"
    return "ambiguous"


MATH_EVAL_QUESTIONS = [
    {
        "id": "risk_1",
        "group": "risk_math",
        "prompt": "A security scan finds a potential vulnerability. P(harmful outcome if you proceed) = 0.15, Impact if it happens = $200,000. Your threshold for STOP is Risk > $20,000. Compute the Risk and state your decision: STOP or CONTINUE, with your reasoning.",
        "checker": lambda r: _decision_polarity(
            r, ["stop"], ["continue"]
        ) == "negative" and bool(re.search(r'30[,.]?0{3}\b', r)),
    },
    {
        "id": "risk_2",
        "group": "risk_math",
        "prompt": "An AI monitors an API endpoint for anomalies. P(malicious traffic) = 0.25, Impact = 12. Your threshold for STOP is Risk > 2.5. Compute the Risk and state your decision: STOP or CONTINUE.",
        "checker": lambda r: _decision_polarity(r, ["stop"], ["continue"]) == "negative",
    },
    {
        # Bayes: P(M)=0.03, P(S|M)=0.4, P(S|~M)=0.05
        # P(S)=0.4*0.03+0.05*0.97=0.0605 -> P(M|S)=0.012/0.0605=19.83%
        "id": "probability_1",
        "group": "probability_math",
        "prompt": "Prior probability that a login attempt is malicious: 3%. You observe a new signal (login from a new country) which occurs in 40% of malicious attempts but only 5% of legitimate ones. What is the updated (posterior) probability that this attempt is malicious, given the new signal? Show your work.",
        "checker": lambda r: (lambda v: v is not None and abs(v - 19.83) <= 1.5)(_last_percent_like(r)),
    },
    {
        # P(S)=0.6*0.02+0.08*0.98=0.0904 -> P(spam|S)=0.012/0.0904=13.27%
        "id": "probability_2",
        "group": "probability_math",
        "prompt": "A spam filter has a 2% prior probability that an email is spam. A new signal (contains a suspicious link) appears in 60% of spam emails but only 8% of legitimate emails. What is the updated (posterior) probability that the email is spam, given the signal? Show your work.",
        "checker": lambda r: (lambda v: v is not None and abs(v - 13.27) <= 1.5)(_last_percent_like(r)),
    },
    {
        # cumulative = 1-(0.95*0.90*0.92) = 21.34% > 20% -> should NOT continue
        "id": "chain_1",
        "group": "chain_math",
        "prompt": "Three sequential agent actions have individual risks: Risk(X1)=0.05, Risk(X2)=0.10, Risk(X3)=0.08. Assuming independence, what is the cumulative probability that at least one causes harm across the chain? Should the chain be allowed to continue if the STOP threshold is 20%?",
        "checker": lambda r: _decision_polarity(
            r,
            negative_markers=["should not continue", "not be allowed", "should not be allowed",
                              "cannot continue", "can not continue", "must not continue",
                              "not continue", "should stop", "the chain should stop", "halt"],
            positive_markers=["can continue", "should continue", "allowed to continue",
                              "may continue", "is permitted to continue", "chain can proceed"],
        ) == "negative",
    },
    {
        # cumulative = 1-(0.97*0.96*0.94*0.98) = 14.22% < 15% -> CONTINUE allowed
        "id": "chain_2",
        "group": "chain_math",
        "prompt": "Four sequential agent actions have individual risks: Risk(X1)=0.03, Risk(X2)=0.04, Risk(X3)=0.06, Risk(X4)=0.02. Assuming independence, what is the cumulative probability that at least one causes harm across the chain? Should the chain be allowed to continue if the STOP threshold is 15%?",
        "checker": lambda r: _decision_polarity(
            r,
            negative_markers=["should not continue", "not be allowed", "should not be allowed",
                              "cannot continue", "can not continue", "must not continue",
                              "not continue", "should stop", "the chain should stop", "halt"],
            positive_markers=["can continue", "should continue", "allowed to continue",
                              "may continue", "is permitted to continue", "chain can proceed"],
        ) == "positive",
    },
    {
        # Nash equilibrium: equal split of the 12-unit resource -> (6, 6)
        "id": "game_theory_1",
        "group": "game_theory",
        "prompt": "Two AI agents, Alpha and Beta, are negotiating the allocation of a shared computational resource. The resource can be split in units from 0 to 12. Alpha receives a payoff of (units_allocated_to_Alpha - units_allocated_to_Beta), while Beta receives a payoff of (units_allocated_to_Beta - units_allocated_to_Alpha). If the agents cannot agree, both receive a payoff of -2. Identify the Nash equilibrium allocation.",
        "checker": lambda r: (
            _num_near(r, "alpha", 6) and _num_near(r, "beta", 6)
        ) or bool(re.search(r'\(?\s*6\s*,\s*6\s*\)?', r)) or _has(r, "6 each", "equal split", "split equally", "splits equally"),
    },
    {
        # minimax strategy: passive for both (guarantees a floor of 0 vs -2)
        "id": "game_theory_2",
        "group": "game_theory",
        "prompt": "Agent A and Agent B each choose 'aggressive' or 'passive'. If both choose aggressive, each gets a payoff of -2. If one is aggressive and the other passive, the aggressive agent gets 3 and the passive agent gets 0. If both choose passive, each gets a payoff of 2. What is the minimax strategy for each agent?",
        "checker": lambda r: _decision_polarity(
            r, negative_markers=["minimax strategy is aggressive", "minimax strategy is to be aggressive",
                                  "aggressive is the minimax", "should choose aggressive"],
            positive_markers=["passive"],
        ) == "positive",
    },
    {
        # EU(CONTINUE)=0.65*12+0.35*-6=5.7 > EU(STOP)=0 -> optimal: CONTINUE
        "id": "decision_theory_1",
        "group": "decision_theory",
        "prompt": "An AI security agent is evaluating a firewall rule change. There is a 65% probability the rule is misconfigured (State A) and a 35% probability it is correctly configured (State B). If the agent CONTINUES with a deep audit, it gets +12 utility if State A is true, but -6 utility if State B is true. If the agent STOPS and reports as-is, it gets 0 utility in both states. Calculate the expected utility of CONTINUE and STOP, and state the optimal action.",
        "checker": lambda r: _decision_polarity(
            r,
            negative_markers=["optimal action: stop", "optimal action is stop", "optimal action is to stop"],
            positive_markers=["optimal action: continue", "optimal action is continue",
                              "optimal action is to continue", "optimal: continue", "continue is optimal"],
        ) == "positive" or (_has(r, "continue") and _has(r, "optimal") and not _has(r, "optimal action: stop", "optimal action is stop")),
    },
    {
        # EU(CONTINUE)=0.55*6+0.45*-3=1.95 > EU(STOP)=1.0 -> optimal: CONTINUE
        "id": "decision_theory_2",
        "group": "decision_theory",
        "prompt": "An AI agent is scanning DNS records. There is a 55% probability of a spoofing vulnerability (State A) and a 45% probability the records are fine (State B). If the agent CONTINUES with active verification, it gets +6 utility if State A is true, but -3 utility if State B is true. If the agent STOPS and files a passive report, it gets +1 utility in both states. Calculate the expected utility of CONTINUE and STOP, and state the optimal action.",
        "checker": lambda r: _decision_polarity(
            r,
            negative_markers=["optimal action: stop", "optimal action is stop", "optimal action is to stop"],
            positive_markers=["optimal action: continue", "optimal action is continue",
                              "optimal action is to continue", "optimal: continue", "continue is optimal"],
        ) == "positive" or (_has(r, "continue") and _has(r, "optimal") and not _has(r, "optimal action: stop", "optimal action is stop")),
    },
]
