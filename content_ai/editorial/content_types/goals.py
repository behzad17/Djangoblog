"""Editorial goal detection (heuristic)."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_ai.editorial.content_types.constants import EditorialGoal
from content_ai.editorial.content_types.registry import get_profile, resolve_goal


@dataclass(frozen=True, slots=True)
class GoalDetectionResult:
    goal: str
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'goal': self.goal,
            'confidence': round(float(self.confidence), 3),
            'reasons': list(self.reasons),
        }


_GOAL_SIGNALS: dict[str, tuple[str, ...]] = {
    EditorialGoal.TEACH: (
        'how to',
        'guide',
        'steg',
        'learn',
        'utbildning',
        'آموزش',
        'راهنما',
    ),
    EditorialGoal.WARN: (
        'warning',
        'varning',
        'risk',
        'fara',
        'هشدار',
        'خطر',
    ),
    EditorialGoal.ANNOUNCE: (
        'announce',
        'meddelar',
        'pressmeddelande',
        'launch',
        'اطلاعیه',
        'اعلام',
    ),
    EditorialGoal.EXPLAIN: (
        'explainer',
        'förklarar',
        'why',
        'varför',
        'توضیح',
        'چرا',
    ),
    EditorialGoal.COMPARE: (
        'compare',
        'jämför',
        'versus',
        'mot',
        'مقایسه',
    ),
    EditorialGoal.SUMMARISE: (
        'summary',
        'sammanfattning',
        'in brief',
        'خلاصه',
    ),
    EditorialGoal.PERSUADE: (
        'opinion',
        'debatt',
        'should',
        'bör',
        'نظر',
    ),
    EditorialGoal.INSPIRE: (
        'inspire',
        'story',
        'portrait',
        'موفقیت',
    ),
    EditorialGoal.INFORM: (
        'news',
        'nyheter',
        'report',
        'خبر',
    ),
}


def detect_editorial_goal(
    *,
    content_type: str = '',
    title: str = '',
    text: str = '',
    override: str | None = None,
) -> GoalDetectionResult:
    if override:
        goal = resolve_goal(override, content_type=content_type)
        return GoalDetectionResult(
            goal=goal,
            confidence=1.0,
            reasons=['Editor override selected this editorial goal.'],
        )

    profile = get_profile(content_type)
    blob = f'{title}\n{(text or "")[:1200]}'.lower()
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}
    for goal, tokens in _GOAL_SIGNALS.items():
        score = 0.0
        matched: list[str] = []
        for token in tokens:
            if token in blob:
                score += 1.0
                matched.append(token)
        if score:
            scores[goal] = score
            reasons[goal] = [
                f'Matched goal signal “{token}”.' for token in matched[:3]
            ]

    # Bias toward the content type's default goal.
    scores[profile.default_goal] = scores.get(profile.default_goal, 0.0) + 1.25
    reasons.setdefault(profile.default_goal, []).append(
        f'Default goal for {profile.label} is {profile.default_goal}.'
    )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    winner, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = min(0.96, 0.5 + (top / (top + second + 1.0)) * 0.45)
    return GoalDetectionResult(
        goal=winner,
        confidence=confidence,
        reasons=reasons.get(winner, [])[:4],
    )
