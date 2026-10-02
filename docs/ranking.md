# Ranking

`EventRanker` computes an inspectable relevance score, not a probability:

- 35% career-field match
- 20% networking strength
- 15% distance
- 10% topic match
- 10% listing quality
- 10% time relevance

Career matching expands parent/child relationships in the taxonomy. This lets a
software-engineering search match JavaScript, Python, cloud, Linux, security,
and other technical communities without an exact-title keyword.

Networking strength is classified separately from topic relevance. Interaction
signals (meetup, networking, workshop, Q&A, career fair, recruiter involvement)
increase it. Passive webinar and prerecorded signals reduce it. Live virtual
events receive a neutral distance value because they are not geographically
constrained.

Every API result includes the component breakdown and a deterministic
explanation. Scores should be tuned against editorial judgments and user
outcomes before adding personalization or learned ranking.
