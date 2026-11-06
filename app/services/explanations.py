
def generate_explanation(user, circle, recommendation):
    """
    Generate a short, data-backed explanation for a Circle recommendation.
    """

    reasons = []

    
    user_interests = {
        topic.slug: topic.label
        for topic in user.interests
    }

    matched_interests = [
        user_interests[topic.slug]
        for topic in circle.topics
        if topic.slug in user_interests
    ]

    if matched_interests:
        if len(matched_interests) == 1:
            reasons.append(
                f"Matches your interest in {matched_interests[0]}."
            )
        else:
            reasons.append(
                "Matches your interests in "
                + ", ".join(matched_interests[:3])
                + "."
            )

    
    if recommendation["freshness_score"] > 0:
        reasons.append("This Circle has recent activity.")

    if recommendation["activity_score"] > 0:
        reasons.append(
            "Recent posts and conversations show member engagement."
        )

    
    if circle.join_policy == "open":
        reasons.append("It's open to join.")
    elif circle.join_policy == "request":
        reasons.append("You can request to join.")

   
    if not matched_interests and not reasons:
        return "Recommended based on available Circle information."

    if not matched_interests:
        return " ".join(reasons)

    return " ".join(reasons)
