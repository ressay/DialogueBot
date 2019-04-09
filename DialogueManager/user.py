import json

from rdflib import Graph

from DialogueManager.FileBrowserDM.user_simulator import UserSimulatorFB


class UserAgent:
    """Connects a real user to the conversation through the console."""

    def __init__(self,user_sim= None):
        """
        The constructor for User.
        :param (DialogueManager.user_simulator.UserSimulator) user_sim:
        """
        self.user_sim = user_sim

    def return_response(self):
        """
        Asks user in console for response then receives a response as input.

        Format must be like this:

        Create_directory, file_name:dir1; path:~/
        Delete_file, file_name:dir1; path:~/
        Create_RegFile, file_name:file1; path:~/
        request, slot:parent_directory
        ask, intent:Create_directory; file_name: dir1; path:~/
        ask, intent:Create_RegFile; file_name: file1; path:~/
        Change_directory, new_directory:~/dir1

        intents, informs keys and values, and request keys and values cannot contain / , :

        Returns:
            dict: The response of the user
        """

        input_string = input('Response: ')
        input_string = input_string.replace(' ','')
        intent,input_string = input_string.split(',')
        arguments = input_string.split(';')
        response = {'intent':intent}
        if intent == 'ask':
            r = {}
            for arg in arguments:
                key,val = arg.split(':')
                r[key] = val
            response['action'] = r
            return response
        for arg in arguments:
            key,val = arg.split(':')
            response[key] = val
        return response

    def start_conversation(self):
        assert self.user_sim, 'User simulator not defined'
        mask = UserSimulatorFB.CURRENT_TREE | UserSimulatorFB.SIMILARITY | UserSimulatorFB.GOAL_DIR \
        | UserSimulatorFB.SUB_GOALS
        user_sim.debug_add(mask)
        response = self.user_sim.reset()
        print(response)
        while True:
            user_response, reward, done, success = self.user_sim.step(self.return_response())
            print(user_response)
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
                print(response)

if __name__ == '__main__':

    c = json.load(open('FileBrowserDM/constants.json', 'r'))
    user_sim = UserSimulatorFB(c,Graph())
    user = UserAgent(user_sim)
    user.start_conversation()


