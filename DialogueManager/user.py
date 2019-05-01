import json

from rdflib import Graph

from DialogueManager.FileBrowserDM.state_tracker import StateTrackerFB
from DialogueManager.FileBrowserDM.user_simulator import UserSimulatorFB
import Ontologies.onto_fbrowser as fbrowser

class UserAgent:
    """Connects a real user to the conversation through the console."""

    def __init__(self,user_sim=None,state_tracker=StateTrackerFB(1,fbrowser.graph)):
        """
        The constructor for User.
        :param (DialogueManager.user_simulator.UserSimulator) user_sim:
        """
        self.user_sim = user_sim
        self.state_tracker = state_tracker

    def return_response(self,user_action):
        """
        Asks user in console for response then receives a response as input.

        Format must be like this:

        Create_directory, file_name:dir1; path:~/
        Delete_file, file_name:dir1; path:~/
        Create_file, file_name:file1; path:~/; is_file:1
        request, slot:parent_directory
        ask, intent:Create_directory; file_name: dir1; path:~/
        ask, intent:Create_RegFile; file_name: file1; path:~/
        Change_directory, new_directory:~/dir1

        intents, informs keys and values, and request keys and values cannot contain / , :

        Returns:
            dict: The response of the user
        """
        self.state_tracker.update_state_user_action(user_action,False)
        print("possible actions:")
        nodes,actions = self.state_tracker.get_possible_actions()
        actions = actions[::2]
        for i, a in enumerate(actions):
            print(i+1,': '),
            print(a)
        # a,an = self.state_tracker.get_possible_actions()

        # print(a)
        input_string = input('Response: ')
        response = actions[int(input_string)-1]
        # input_string = input_string.replace(' ','')
        # intent,input_string = input_string.split(',')
        # arguments = input_string.split(';')
        # response = {'intent':intent}
        # if intent == 'ask':
        #     r = {}
        #     for arg in arguments:
        #         key,val = arg.split(':')
        #         r[key] = val
        #     response['action'] = r
        #     return response
        # for arg in arguments:
        #     key,val = arg.split(':')
        #     response[key] = val
        self.state_tracker.update_state_agent_action(response,False)
        return response

    def start_conversation(self):
        assert self.user_sim, 'User simulator not defined'
        mask = UserSimulatorFB.CURRENT_TREE | UserSimulatorFB.SIMILARITY | UserSimulatorFB.GOAL_DIR \
        | UserSimulatorFB.SUB_GOALS
        user_sim.debug_add(mask)
        response = self.user_sim.reset()
        print(response)
        while True:
            response, reward, done, success = self.user_sim.step(self.return_response(response))
            print(response)
            print('reward is:',reward)
            if done:
                print('end of conversation with'),
                if success:
                    print('success')
                else:
                    print('failure')
                print('******')
                print('starting new conversation')
                response = self.user_sim.reset()
                self.state_tracker = StateTrackerFB(1,fbrowser.graph)
                print(response)

if __name__ == '__main__':

    c = json.load(open('FileBrowserDM/constants.json', 'r'))
    user_sim = UserSimulatorFB(c,Graph())
    user = UserAgent(user_sim)
    user.start_conversation()


