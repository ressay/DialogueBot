import json
from DialogueManager.FileBrowserDM.state_tracker import StateTrackerFB
from DialogueManager.agent import Agent
import Ontologies.onto_fbrowser as fbrowser


class AgentFB(Agent):
    def __init__(self, state_size, constants, train_by_batch=True,use_multiprocessing=True) -> None:
        super().__init__(state_size, constants, train_by_batch,use_multiprocessing)

    def init_state_tracker(self):
        return StateTrackerFB(self.state_size, fbrowser.graph)


if __name__ == '__main__':
    c = json.load(open('constants.json', 'r'))
    agent = AgentFB(10, c)
    # agent._build_model()
