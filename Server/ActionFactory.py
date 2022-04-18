from VSCAction import *
def action_factory(serv):
    action_lst = [
        SurveyAction(1/10, serv), TestAction(1/10, serv),
        EstimatedEmotion(1/10, serv), ActionBreak(1/30, serv)]
    action_dict = {}
    try:
        for a in action_lst:
            action_dict[a.NAME] = a
    except Exception:
        print("Actions needs NAME, DEVICES and ACTIONS to function.")
        raise
    for a in action_dict:
        for dep in action_dict[a].ACTIONS:
            action_dict[dep].observe(action_dict[a])
    return action_dict
