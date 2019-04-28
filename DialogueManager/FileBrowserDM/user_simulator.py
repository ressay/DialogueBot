import json
import random, copy
from DialogueManager.dialogue_config import FAIL, SUCCESS, NO_OUTCOME
from DialogueManager.user_simulator import UserSimulator
from rdflib import Graph
from DialogueManager.FileBrowserDM.file_tree_sim import FileTreeSimulator





class UserSimulatorFB(UserSimulator):
    """Simulates a real user, to train the agent with reinforcement learning."""
    """
    Debugging mask
    """
    CURRENT_TREE = 1
    GOAL_TREE = 2
    SUB_GOALS = 4
    GOAL_DIR = 8
    SIMILARITY = 16
    """
    User possible actions
    """
    Change_directory_desire = "Change_directory_desire"
    Delete_file_desire = 'Delete_file_desire'
    Create_file_desire = 'Create_file_desire'
    # Create_directory_desire = 'Create_directory_desire'
    u_inform = 'inform'
    u_request = 'request'
    confirm = 'confirm'
    deny = 'deny'
    def __init__(self, constants, ontology):
        """
        The constructor for UserSimulator. Sets dialogue config variables.

        Parameters:
            constants (dict): Dict of constants loaded from file
            ontology (rdflib.Graph): ontology graph
        """
        super().__init__(constants, ontology)
        self.agent_tree_actions = ["Create_file",  "Delete_file"]
        for a in self.agent_tree_actions:
            self.user_responses[a] = self._build_response
        self.user_responses['Change_directory'] = self._build_response
        self.user_responses['inform'] = self._build_response
        self.user_responses['ask'] = self._ask_response
        self.user_responses['request'] = self._req_response
        self.debug = 0

    def generate_goal(self):
        goal_tree = FileTreeSimulator()
        self.goal = {'goal_tree': goal_tree, 'end_directory': goal_tree.get_random_directory().path(), 'sub_goal': []}
        # print("new goal:")
        # goal_tree.print_tree()
        self.generate_next_focused_file()


    def reset(self):
        """
        Resets the user sim. by emptying the state and returning the initial action.

        Returns:
            dict: The initial action of an episode
        """
        self.state = {
            # empty file tree
            'current_file_tree': FileTreeSimulator([]),
            'focused_file': {'file': -1, 'map': {}, 'delete': -1},
            'current_directory': '~/',
            'previous_directory': '~/',
            'previous_similarity': [0, 1],
            'current_similarity': [0, 1],
            'previous_uAction': None,
            'current_uAction': None
        }
        self.round = 0
        self.generate_goal()
        return self._return_init_action()

    def _return_init_action(self):
        """
        Returns the initial action of the episode.

        The initial action has an intent of request, required init. inform slots and a single request slot.

        Returns:
            dict: Initial user response
        """
        user_response = self.generate_tree_desire_intent()
        self.state['previous_intent'] = user_response
        return user_response

    def step(self, agent_action):
        """
        Return the response of the user sim. to the agent by using rules that simulate a user.

        Given the agent action craft a response by using deterministic rules that simulate (to some extent) a user.
        Some parts of the rules are stochastic. Check if the agent has succeeded or lost or still going.

        Parameters:
            agent_action (dict): The agent action that the user sim. responds to

        Returns:
            dict: User sim. response
            int: Reward
            bool: Done flag
            int: Success: -1, 0 or 1 for loss, neither win nor loss, win
        """
        self.state['previous_uAction'] = self.state['current_uAction']
        done = False
        self.round += 1
        # First check round num, if equal to max then fail
        if self.round == self.max_round:
            done = True
            success = FAIL
            user_response = self._end_response()
        else:
            try:
                success = self.update_state(agent_action)
                if success:
                    done = True
                    user_response = self._end_response()
                else:
                    agent_intent = agent_action['intent']
                    assert agent_intent in self.agent_possible_intents, 'Not acceptable agent action'
                    user_response = self.user_responses[agent_intent](agent_action)
            except Exception as e:
                print('ERROR HAPPENED AND IGNORING IT: ',e)
                return self._default_response(), -5, False, False
        self.state['current_uAction'] = user_response
        reward = self.reward_function(agent_action, success)
        self.print_debug()
        return user_response, reward, done, 1 if success == 1 else 0

    def reward_function(self, agent_action, success):
        if success:
            return self.goal['goal_tree'].r_size()
        if self.sub_goal_exists():  # if there are pending sub_goals
            reward = self.get_sub_goal_reward(self.goal['sub_goal'][0])
            if reward:
                return reward
        f, t = self.state['current_similarity']
        pf, pt = self.state['previous_similarity']
        if f / t > pf / pt:  # tree similarity got better
            return 1
        if self.state['current_uAction']['intent'] == self.confirm:  # if confirming an action for agent, reward is neutral
            return 0
        return -1

    def apply_agent_tree_action(self, agent_action, f_sim):
        """

        :param (dict) agent_action: dictionary that contains agent action
        :param (FileTreeSimulator) f_sim: tree simulator to apply the agent action on
        :return:
        """
        intent = agent_action['intent']
        assert intent in self.agent_tree_actions, "trying to apply action that doesn't exist in agent_tree_actions"
        if intent == 'Create_file':
            f_sim.add_file(agent_action['file_name'], agent_action['is_file'], agent_action['path'],True)
        elif intent == 'Delete_file':
            f_sim.remove_file(agent_action['file_name'], agent_action['path'])

    def update_sub_goals(self):
        for sub_goal in self.goal['sub_goal']:
            last_dir = sub_goal['dirs'][-1]
            current_dir = self.state['current_directory']
            if current_dir[-1] == '/': current_dir = current_dir[:-1]
            if last_dir[-1] == '/':last_dir = last_dir[:-1]
            if sub_goal['name'] == 'Change_directory' and current_dir == last_dir:
                self.goal['sub_goal'].remove(sub_goal)

    def update_state(self, agent_action):
        """
        :param (dict) agent_action: action of the dialogue manager
        :return (int) : 1 if success reached, 0 else wise
        """
        intent = agent_action['intent']
        f_sim = self.state['current_file_tree']
        goal_sim = self.goal['goal_tree']
        self.state['previous_directory'] = self.state['current_directory']

        if intent in self.agent_tree_actions:
            self.apply_agent_tree_action(agent_action, f_sim)
            self.generate_next_focused_file()
        elif intent == 'Change_directory':
            self.state['current_directory'] = agent_action['new_directory']
        self.update_sub_goals()
        found, total = f_sim.tree_similarity(goal_sim)
        self.state['previous_similarity'] = self.state['current_similarity']
        self.state['current_similarity'] = [found, total]
        return 1 if found == total else 0

    def generate_next_focused_file(self):
        f_sim = self.state['current_file_tree']
        result = f_sim.get_first_dissimilarity(self.goal['goal_tree'])
        if result is not None:
            f, m, d = result
            self.state['focused_file'] = {
                'file': f == 1,
                'map': m,
                'delete': not d  # found in current_file_tree but not in goal_tree
            }

    """
    File browser user intents:
    default: when user sim doesn't know how to respond
    end: user sim ends conversation
    inform: user simulator informs the agent about:
        file_name
        file_parent
        desire
    """

    def sub_goal_exists(self):
        return len(self.goal['sub_goal']) > 0

    def next_sub_goal(self):
        return self.goal['sub_goal'][0]

    def add_change_directory_sub_goal(self, dirs):
        self.goal['sub_goal'].append({'name': 'Change_directory', 'dirs': dirs})

    def generate_sub_goal_intent(self):
        sub_goal = self.next_sub_goal()
        if sub_goal['name'] == 'Change_directory':
            assert self.state['current_directory'] != sub_goal['dirs'][-1], 'sub goal already reached'
            dirs = sub_goal['dirs']
            index = int(random.uniform(0, len(dirs) - 0.01))
            directory = dirs[index].split('/')[-1]
            return {'intent': self.Change_directory_desire, 'directory': directory}
        return None

    def debug_bitmask(self,bitmask):
        self.debug = bitmask

    def debug_add(self,bitmask):
        self.debug |= bitmask

    def print_debug(self):
        if self.debug & self.CURRENT_TREE:
            print('DEBUG: Current file tree:')
            self.state['current_file_tree'].print_tree()
        if self.debug & self.GOAL_TREE:
            print('DEBUG: Goal tree:')
            self.goal['goal_tree'].print_tree()
        if self.debug & self.SUB_GOALS:
            print('DEBUG: Sub goals:')
            for goal in self.goal['sub_goal']:
                print(goal)
        if self.debug & self.GOAL_DIR:
            print('DEBUG: End directory:')
            print(self.goal['end_directory'])
        if self.debug & self.SIMILARITY:
            print('DEBUG: tree similarity')
            print(self.state['current_similarity'])

    def generate_tree_desire_intent(self):
        """
        generate an action related to tree creation
        :return (dict): the generated action
        """
        proba_file = 0.8
        proba_parent = 0.2
        proba_change_dir = 0.7

        def next_dir(origin, destination):
            """
            :param (str) origin: path origin
            :param (str) destination: path destination
            :return (str,list) : next directory to take and list of directories to get to destination in order
            """
            def paths(dirs):
                return ["/".join(dirs[:i+1]) for i in range(len(dirs))]
            if origin[-1] == '/':
                origin = origin[:-1]
            if destination[-1] == '/':
                destination = destination[:-1]

            if origin == destination:
                return None
            origin = origin.split('/')
            destination = destination.split('/')

            if len(origin) > len(destination):
                return origin[-2], paths(origin)[len(destination)::-1]

            i = 0
            for o, d in zip(origin, destination[:len(origin)]):
                if o != d:
                    return origin[-2], paths(origin)[i::-1]

            if random.uniform(0, 1) < 0.5:  # returns next directory
                return destination[len(origin)], paths(destination)[len(origin):]
            # generate any index randomly between length origin and length destination (directories to get to
            # destination from origin)
            index = int(random.uniform(len(origin), len(destination) - 0.01))
            return destination[index], paths(destination)[len(origin):]

        # if tree already finished
        if self.state['current_similarity'][0] == self.state['current_similarity'][1]:
            result = next_dir(self.state['current_directory'], self.goal['end_directory'])
            if result is not None:
                directory, dirs = result
                return {'intent': self.Change_directory_desire, 'directory': directory}

        if self.sub_goal_exists():
            return self.generate_sub_goal_intent()


        focused_file = self.state['focused_file']
        file_map = focused_file['map']

        if random.uniform(0, 1) < proba_change_dir:
            result = next_dir(self.state['current_directory'], file_map['parent'].path())

            if result is not None:
                directory, dirs = result
                self.add_change_directory_sub_goal(dirs)
                return {'intent': self.Change_directory_desire, 'directory': directory}

        is_file = 0
        if focused_file['delete']:
            intent = self.Delete_file_desire
        else:
            intent = self.Create_file_desire
            if focused_file['file']:
                is_file = 1

        response = {'intent': intent}
        name = focused_file['map']['name']
        parent_name = focused_file['map']['parent'].name
        params = {'file_name': name, 'parent_directory': parent_name, 'is_file':is_file}

        if random.uniform(0, 1) > proba_file:
            del params['file_name']
        if random.uniform(0, 1) > proba_parent:
            del params['parent_directory']

        for k in params:
            response[k] = params[k]
        return response

    def _build_response(self, agent_action):
        response = self.generate_tree_desire_intent()
        return response

    def _ask_response(self, agent_action):
        assert agent_action['intent'] == 'ask', 'intent is not "ask" in ask_response'
        asked_action = agent_action['action']
        if asked_action['intent'] in self.agent_tree_actions:
            file_sim_copy = self.state['current_file_tree'].copy()
            self.apply_agent_tree_action(asked_action, file_sim_copy)
            f, t = file_sim_copy.tree_similarity(self.goal['goal_tree'])
            pf, pt = self.state['current_similarity']
            # file_sim_copy.print_tree()
            # print('DEBUG ASK: COPY:',f,t,' CURRENT SIM: ',pf,pt)
            if f / t > pf / pt:
                return {'intent': self.confirm}
        elif asked_action['intent'] == 'Change_directory':
            if not self.sub_goal_exists():
                return {'intent': self.deny}
            sub_goal = self.next_sub_goal()
            if sub_goal['name'] == 'Change_directory' \
                    and asked_action['new_directory'] in sub_goal['dirs']:
                return {'intent': self.confirm}
        return {'intent': self.deny}

    def _req_response(self, agent_action):
        response = {'intent': self.u_inform}
        requested = agent_action['slot']
        focused_file = self.state['focused_file']['map']
        if requested == 'file_name':
            response['file_name'] = focused_file['name']
        elif requested == 'parent_directory':
            if 'file_name' not in agent_action \
                    or focused_file['name'] == agent_action['file_name']:
                parent = focused_file['parent']
            else:
                name = agent_action['file_name']
                f, m = self.goal['goal_tree'].lookup_file_name(name)
                parent = m['parent']
            response['parent_directory'] = parent.name
        else:
            return self._default_response()
        return response

    def get_sub_goal_reward(self, sub_goal):
        reward = 0
        if sub_goal['name'] == 'Change_directory':
            current_dir = self.state['current_directory']
            if current_dir in sub_goal['dirs']:
                reward = sub_goal['dirs'].index(current_dir) + 1
                del sub_goal['dirs'][:reward]
                if not len(sub_goal['dirs']):  # finished sub_goal
                    self.goal['sub_goal'].remove(sub_goal)
        return reward


if __name__ == '__main__':
    c = json.load(open('constants.json', 'r'))
    sim = UserSimulatorFB(c, Graph())
    print(sim.reset())
    sim.add_change_directory_sub_goal(['~','dir1','dir2'])
    print(sim.goal['sub_goal'])
