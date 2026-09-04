#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Known scam archetypes — linguistic fingerprints.

Each scenario lists marker regexes and weights. Matching raises confidence that
a call follows a known scam playbook. Markers are matched case-insensitively
against the final transcript text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Scenario:
    key: str
    name: str
    description: str
    advice: str
    markers: list[tuple[str, float]]  # (regex, weight 0..1)
    threshold: float = 0.35  # normalized score needed to declare a match

    def score(self, text: str) -> tuple[float, list[str]]:
        """Return (0..1 confidence, matched marker labels)."""
        text_l = text.lower()
        total = 0.0
        matched: list[str] = []
        for pattern, weight in self.markers:
            if re.search(pattern, text_l):
                total += weight
                matched.append(pattern)
        # normalize by sum of weights present in this scenario
        max_total = sum(w for _, w in self.markers)
        return min(total / max_total if max_total else 0.0, 1.0), matched


SCENARIOS: list[Scenario] = [
    Scenario(
        key="government_impostor",
        name="Government impostor",
        description=(
            "Caller claims to be from a government agency (IRS, police, immigration, "
            "social security) and demands immediate payment or personal information."
        ),
        advice=(
            "Hang up. Real government agencies never demand immediate payment by phone, "
            "never ask for gift cards or wire transfers, and never threaten arrest for "
            "not paying on the spot. Look up the agency's real number yourself and call it."
        ),
        markers=[
            (r"\b(internal revenue service|the i\.r\.s\.?|irs)\b", 0.9),
            (r"\b(social security administration|ssa officer)\b", 0.9),
            (r"\b(criminal investigation unit|federal crime|warrant (?:for|out for) your arrest)\b", 1.0),
            (r"\b(you have (?:a )?warrant|arrest warrant)\b", 1.0),
            (r"\b(law enforcement (?:will|is coming)|police (?:will|are on the way))\b", 0.8),
            (r"\b(immigration|customs and border|border patrol)\b", 0.5),
            (r"\b(clear (?:your )?(?:tax|legal) (?:debt|issue)|resolve this (?:case|matters?))\b", 0.5),
            (r"\b(your (?:ssn|social security number) (?:has been|is) (?:suspended|compromised|used))\b", 1.0),
            (r"\b(tax fraud|tax evasion)\b", 0.7),
        ],
        threshold=0.30,
    ),
    Scenario(
        key="bank_fraud",
        name="Bank / card fraud impersonation",
        description=(
            "Caller pretends to be your bank's fraud department, often citing a fake "
            "suspicious charge, then asks you to 'verify' accounts or move money."
        ),
        advice=(
            "Hang up and call your bank using the number on the back of your card. "
            "Your real bank will NEVER ask you to move money to a 'safe account' "
            "or read back a one-time passcode."
        ),
        markers=[
            (r"\b(fraud (?:department|team|alert|unit)|unauthorized transaction)\b", 0.8),
            (r"\b(suspicious (?:charge|activity|transaction) (?:on|in) your account)\b", 0.8),
            (r"\b(safe account|secure account|transfer (?:your )?(?:funds|money) (?:to|into) (?:a |the )?(?:safe|secure))\b", 1.0),
            (r"\b(your (?:account|card) (?:has been|is) (?:compromised|frozen|locked|suspended))\b", 0.7),
            (r"\b(verify (?:your|the) (?:identity|account|details|card number))\b", 0.5),
            (r"\b(one[- ]time (?:passcode|code|password)|otp)\b", 0.9),
            (r"\b(last (?:four|4) digits)\b", 0.4),
            (r"\b(declined (?:transaction|charge)|charge of \d{3,})\b", 0.5),
        ],
        threshold=0.30,
    ),
    Scenario(
        key="tech_support",
        name="Tech support scam",
        description=(
            "Caller claims your computer has a virus or security error and pushes you "
            "to install remote-access software or pay for 'repairs'."
        ),
        advice=(
            "Hang up. Real tech companies never call you about viruses out of the blue. "
            "Never let a stranger remote-control your computer."
        ),
        markers=[
            (r"\b(your (?:computer|laptop|windows) (?:has|is) (?:a )?(?:virus|infected|malware|error))\b", 1.0),
            (r"\b(tech(?:nical)? support|microsoft (?:support|windows team)|apple (?:support|care))\b", 0.8),
            (r"\b(remote (?:access|session|connection)|teamviewer|anydesk)\b", 1.0),
            (r"\b(download (?:this|the) (?:app|software|program)|go to (?:this )?website and (?:download|enter))\b", 0.8),
            (r"\b(expired (?:subscription|license|warranty))\b", 0.7),
            (r"\b(refund (?:for|of) \d+|double (?:refund|charge))\b", 0.5),
        ],
        threshold=0.30,
    ),
    Scenario(
        key="grandparent",
        name="Grandparent / emergency scam",
        description=(
            "Caller pretends to be a grandchild or official (often 'bail') with an "
            "emergency needing money immediately, begging secrecy."
        ),
        advice=(
            "Hang up and call your family member directly on their usual number. "
            "Real emergencies survive a callback."
        ),
        markers=[
            (r"\b(grandma|grandpa|grandmother|grandson|granddaughter|it'?s me)\b", 0.6),
            (r"\b(i'?m in (?:jail|prison|the hospital|an accident))\b", 1.0),
            (r"\b(bail money|lawyer fee)\b", 1.0),
            (r"\b(don'?t tell (?:mom|dad|mommy|daddy|your parents|anyone))\b", 1.0),
            (r"\b(i (?:broke|crashed) (?:my|the) (?:car|phone))\b", 0.5),
            (r"\b(courier (?:will|is coming) (?:to )?pick ?up|envelope of cash)\b", 1.0),
        ],
        threshold=0.30,
    ),
    Scenario(
        key="prize_lottery",
        name="Prize / lottery / grant scam",
        description=(
            "You 'won' something but must pay a fee or give bank details to receive it."
        ),
        advice=(
            "Real prizes never require you to pay a fee upfront or share bank details "
            "to claim them."
        ),
        markers=[
            (r"\b(you(?:'ve)? (?:won|been selected|are a (?:winner|finalist)))\b", 0.9),
            (r"\b(lottery|sweepstakes|prize|jackpot|publisher'?s clearing house)\b", 0.8),
            (r"\b(claim (?:your )?(?:prize|winnings)|processing fee|administration fee)\b", 1.0),
            (r"\b(federal grant|government grant|free grant money)\b", 0.9),
            (r"\b(taxes and (?:fees|processing) (?:must be|have to be) paid (?:first|upfront))\b", 1.0),
        ],
        threshold=0.35,
    ),
    Scenario(
        key="romance_investment",
        name="Romance / investment scam",
        description=(
            "Builds emotional trust fast, then steers to crypto or investment "
            "'opportunities', or asks for money for travel/emergencies."
        ),
        advice=(
            "Never send money or invest based on advice from someone you have only "
            "met online or by phone. Verify identities."
        ),
        markers=[
            (r"\b(i (?:love|really like) (?:talking|chatting) (?:with|to) you|we have (?:such )?a connection)\b", 0.5),
            (r"\b(invest|trading|crypto|bitcoin|forex|returns? on your money)\b", 0.8),
            (r"\b(guaranteed (?:return|profit)|double your money|risk[- ]free)\b", 1.0),
            (r"\b(i need (?:money|help) (?:for|to) (?:my )?(?:plane|ticket|customs|hospital))\b", 1.0),
            (r"\b(my (?:brother|uncle|friend) (?:works|is) (?:at|in) (?:the exchange|wall street))\b", 0.7),
        ],
        threshold=0.35,
    ),
]


def match_scenarios(text: str) -> list[tuple[Scenario, float, list[str]]]:
    """Return all scenarios with confidence >= threshold, sorted best-first."""
    results = []
    for sc in SCENARIOS:
        conf, matched = sc.score(text)
        if conf >= sc.threshold:
            results.append((sc, conf, matched))
    results.sort(key=lambda x: -x[1])
    return results
