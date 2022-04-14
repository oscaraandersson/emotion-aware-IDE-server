from VSCAction import *
def action_factory(serv):
    action_lst = [
        SurveyAction(1/10, serv), TestAction(1/10, serv),
        EstimatedEmotion(1/10, serv), StuckAction(60, serv), ActionBreak(1/30, serv)]
    action_dict = {}
    try:
        for a in action_lst:
            a_dict = {
                "devices" : a.DEVICES,
                "act" : a.ACTIONS,
                "client" : a.CLIENT_ACTION,
                "obj" : a,
                "active" : False,
                "running" : False
            }
            action_dict[a.NAME] = a_dict
    except Exception:
        print("Actions needs NAME, DEVICES and ACTIONS to function.")
        raise
    for a in action_dict:
        for dep in action_dict[a]["act"]:
            action_dict[dep]["obj"].observe(action_dict[a]["obj"])
    return action_dict
