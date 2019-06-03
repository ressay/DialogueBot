from DialogueManager.FileBrowserDM.user_simulator import UserSimulatorFB
import Ontologies.onto_fbrowser as fbrowser

class IntentTracker(object):

    open_file_requirements = {
        'file_name': (True, []),
        'parent_directory': (False, ['file_name'])
    }
    rename_file_requirements = {
        'old_name': (True, []),
        'new_name': (True, ['old_name']),
        'parent_directory': (False, ['old_name'])
    }
    search_file_requirements = {
        'file_name': (True, [])
    }
    change_directory_requirements = {
        'directory': (True, [])
    }
    intents_requirements = {
        UserSimulatorFB.Open_file_desire: open_file_requirements,
        UserSimulatorFB.Rename_file_desire: rename_file_requirements,
        UserSimulatorFB.u_request: search_file_requirements,
        UserSimulatorFB.Change_directory_desire: change_directory_requirements
    }
    slot_converter = {
        'directory': ['file_name'],
        'old_name': ['old_name', 'file_name'],
        'new_name': ['new_name', 'file_name'],
        'parent_directory': ['parent_directory', 'file_name']
    }

    def __init__(self) -> None:
        super().__init__()
        self.current_intent_info = {
            'name': None
        }
        self.current_intent_requirements = {

        }

    def set_current_intent(self, user_action):
        self.current_intent_requirements = self.intents_requirements[user_action['intent']]
        self.current_intent_info = {
            'name': user_action['intent']
        }
        for key in self.current_intent_requirements:
            if key in user_action:
                self.current_intent_info[key] = user_action[key]

    def add_inform_intent(self, user_action, prev_user_action):
        if prev_user_action['intent'] == 'request':
            slot = prev_user_action['slot']
            cslots = self.slot_converter[slot] if slot in self.slot_converter else [slot]
            for s in cslots:
                if s in user_action:
                    value = user_action[s]
                    del user_action[s]
                    user_action[slot] = value
                    break

        for key in self.current_intent_requirements:
            if key in user_action:
                self.current_intent_info[key] = user_action[key]

    def clear_current_intent(self):
        self.current_intent_info = {
            'name': None
        }
        self.current_intent_requirements = {

        }

    def all_required_slots_filled(self):
        for key in self.current_intent_requirements:
            r, _ = self.current_intent_requirements[key]
            if r and key not in self.current_intent_info:
                return False
        return True
    def has_intent(self):
        return self.current_intent_info['name'] is not None

    def is_intent_supported(self, user_action):
        return user_action['intent'] in self.intents_requirements

    def get_request_key_needs(self, key):
        assert key in self.current_intent_requirements, "key is not in current intent possible slots" + key
        _, needed = self.current_intent_requirements[key]
        result = {}
        for slot in needed:
            if slot not in self.current_intent_info:
                return None
            result[slot] = self.current_intent_info[slot]
        return result


class ActionTracker(object):
    file_node_slot_filler = {
        'file_name': 'desire',
        'directory': 'desire',
        'old_name': 'desire'
    }

    user_action_to_onto_node = {
        UserSimulatorFB.Open_file_desire: fbrowser.Open_file,
        UserSimulatorFB.Rename_file_desire: fbrowser.Rename_file,
        UserSimulatorFB.u_request: fbrowser.A_inform,
        UserSimulatorFB.Change_directory_desire: fbrowser.Change_directory
    }

    def __init__(self, state_tracker) -> None:
        super().__init__()
        self.state_tracker = state_tracker
        self.nodes_updater = {
            UserSimulatorFB.Open_file_desire: self.get_open_file_nodes,
            UserSimulatorFB.Rename_file_desire: self.get_rename_file_nodes,
            UserSimulatorFB.u_request: self.get_search_file_nodes,
            UserSimulatorFB.Change_directory_desire: self.get_change_directory_nodes
        }
        self.possible_actions = {
            UserSimulatorFB.Open_file_desire: self.possible_actions_open,
            UserSimulatorFB.Rename_file_desire: self.possible_actions_rename,
            UserSimulatorFB.u_request: self.possible_actions_search,
            UserSimulatorFB.Change_directory_desire: self.possible_actions_change_dir
        }
        self.current_action_info = {
            'desire': None,
            'nodes_info': None
        }

        self.intent_tracker = IntentTracker()

    def update_action_info(self):
        intent = self.intent_tracker.current_intent_info['name']
        self.current_action_info['desire'] = self.user_action_to_onto_node[intent]
        self.update_files_nodes()

    def set_current_action(self, user_action):
        self.intent_tracker.set_current_intent(user_action)
        self.update_action_info()

    def add_inform_intent(self, user_action, prev_user_action):
        self.intent_tracker.add_inform_intent(user_action, prev_user_action)
        self.update_action_info()

    def clear_current_action(self):
        self.intent_tracker.clear_current_intent()
        self.current_action_info = {
            'desire': None,
            'nodes_info': None
        }

    def has_intent(self):
        return self.intent_tracker.current_intent_info['name'] is not None

    def is_intent_supported(self, user_action):
        return user_action['intent'] in self.intent_tracker.intents_requirements

    def update_files_nodes(self):
        self.current_action_info['nodes_info'] = self.nodes_updater[self.intent_tracker.current_intent_info['name']]()
        # print('nodes:', self.current_action_info['nodes_info'])

    def get_possible_actions(self):
        actions = []
        for key in self.intent_tracker.current_intent_requirements:
            # print('start', key)
            if key == 'name':
                # print('no name')
                continue
            needs = self.intent_tracker.get_request_key_needs(key)
            if needs is None:
                # print('needs is None')
                continue
            if key in self.file_node_slot_filler:
                needs['file_node'] = self.current_action_info[self.file_node_slot_filler[key]]
                actions.append(self.create_request_action(key, needs))
            else:
                for node in self.current_action_info['nodes_info']['candidate_nodes']:
                    needs['file_node'] = node
                    actions.append(self.create_request_action(key, needs))
        if self.intent_tracker.all_required_slots_filled():
            actions += self.possible_actions[self.intent_tracker.current_intent_info['name']]()
        return actions

    def possible_actions_open(self):
        candidates = self.current_action_info['nodes_info']['candidate_nodes']
        if candidates is None or len(candidates) == 0:
            return []
        actions = []
        for node in candidates:
            actions.append({'intent': 'Open_file', 'file_name': self.intent_tracker.current_intent_info['file_name'],
                            'path': self.state_tracker.get_path_with_real_root(node, False),
                            'action_node': fbrowser.Open_file, 'file_node': node})
        return actions

    def possible_actions_rename(self):
        candidates = self.current_action_info['nodes_info']['candidate_nodes']
        if candidates is None or len(candidates) == 0:
            return []
        actions = []
        for node in candidates:
            actions.append({'intent': 'Rename_file', 'old_name': self.intent_tracker.current_intent_info['old_name'],
                            'new_name': self.intent_tracker.current_intent_info['new_name'],
                            'path': self.state_tracker.get_path_with_real_root(node, False),
                            'action_node': fbrowser.Rename_file, 'file_node': node})
        return actions

    def possible_actions_change_dir(self):
        candidates = self.current_action_info['nodes_info']['candidate_nodes']
        if candidates is None or len(candidates) == 0:
            # print('out here because candidates is ', candidates)
            return []
        actions = []
        for node in candidates:
            actions.append({'intent': 'Change_directory',
                            'new_directory': self.state_tracker.get_path_with_real_root(node),
                            'action_node': fbrowser.Change_directory, 'file_node': node})
        return actions

    def possible_actions_search(self):
        candidates = self.current_action_info['nodes_info']['candidate_nodes']
        if candidates is None or len(candidates) == 0:
            return []
        actions = [{'intent': 'inform', 'file_name': self.intent_tracker.current_intent_info['file_name'],
                    'paths': [self.state_tracker.get_path_with_real_root(node, False) for node in candidates],
                    'action_node': fbrowser.U_inform, 'file_node': fbrowser.U_inform}]
        return actions

    """
    FILE NODES UPDATE METHODS
    """

    def get_open_file_nodes(self):
        candidates = self.state_tracker.get_files_from_graph(self.intent_tracker.current_intent_info)
        return {'candidate_nodes': candidates if candidates is not None else []}

    def get_rename_file_nodes(self):
        file_infos = self.intent_tracker.current_intent_info.copy()
        if 'old_name' in file_infos:
            file_infos['file_name'] = file_infos['old_name']
        candidates = self.state_tracker.get_files_from_graph(file_infos)
        return {'candidate_nodes': candidates if candidates is not None else []}

    def get_search_file_nodes(self):
        candidates = self.state_tracker.get_files_from_graph(self.intent_tracker.current_intent_info)
        return {'candidate_nodes': candidates if candidates is not None else []}

    def get_change_directory_nodes(self):
        file_infos = {}
        if 'directory' in self.intent_tracker.current_intent_info:
            file_infos['file_name'] = self.intent_tracker.current_intent_info['directory']
        candidates = self.state_tracker.get_files_from_graph(file_infos)
        return {'candidate_nodes': candidates if candidates is not None else []}

    """
    STATIC METHODS
    """

    @staticmethod
    def create_request_action(key, needed):
        action = {'intent': 'request', 'slot': key, 'action_node': fbrowser.A_request}
        for slot in needed:
            action[slot] = needed[slot]
        return action
