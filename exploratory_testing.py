import unittest
from unittest.mock import Mock

class Action:
    def __init__(self, actions, devices) -> None:
        self.ACTIONS = actions
        self.DEVICES = devices

class MockClass:
    def __init__(self, act_dict) -> None:
        self.actions = act_dict
        self.settings = {"devices" : {"E4" : True, "EEG" : True, "EYE" : True}}

    def activation_check(self, act):
        def actions_traverse(visited, current):
            visited.add(current)
            if not self.actions[current].ACTIONS:
                return visited
            for a in self.actions[current].ACTIONS:
                if not a in visited:
                    visited.update(actions_traverse(visited, a))
            return visited

        for d in self.actions[act].DEVICES:
            if not self.settings["devices"][d]:
                return []
        
        return list(actions_traverse(set(), act))

ACT_DICT = {
    "T1" : Action([],["E4", "EEG", "EYE"]),
    "T2" : Action([],["E4"]),
    "T3" : Action([],["EYE"]),
    "T4" : Action([],["EEG"]),
}

class TestDependent(unittest.TestCase):
    def setUp(self) -> None:
        self.test_class = MockClass(ACT_DICT)
    
    def test_T1(self):
        self.assertEqual(["T1"], self.test_class.activation_check("T1"))
    
    def test_T2(self):
        self.test_class.settings["E4"] = False
        print(self.test_class.settings)
        self.assertEqual([], self.test_class.activation_check("T2"))
    
    def test_T3(self):
        self.test_class.settings["EYE"] = False
        self.assertEqual([], self.test_class.activation_check("T3"))

    def test_T4(self):
        self.test_class.settings["EEG"] = False
        print(self.test_class.activation_check("T4"))
        self.assertEqual([], self.test_class.activation_check("T4"))


if __name__ == "__main__":
    unittest.main()


