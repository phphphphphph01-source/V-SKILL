from database.models import SkillScore, LearningTopic
def learning_plan_data(user_id):
    weak=SkillScore.query.filter_by(user_id=user_id).order_by(SkillScore.score.asc()).limit(3).all()
    ids=[x.skill_id for x in weak]
    topics=[]
    for sid in ids:
        topics.extend(LearningTopic.query.filter_by(skill_id=sid).order_by(LearningTopic.level).limit(3).all())
    return topics[:7]
