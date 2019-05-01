import rdflib
import sys
from rdflib import Literal, BNode
from DialogueManager.state_tracker import StateTracker
import Ontologies.onto_fbrowser as fbrowser
import Ontologies.python_from_ontology as onto
from DialogueManager.FileBrowserDM.user_simulator import UserSimulatorFB as usim
from DialogueManager.FileBrowserDM.utils import agent_actions


class StateTrackerFB(StateTracker):
    def __init__(self, size, ontology, one_hot=True, lazy_encoding=True) -> None:
        """
        StateTracker constructor
        :param (int) size:
        :param (rdflib.Graph) ontology:
        """
        super().__init__(size, ontology, one_hot, lazy_encoding)
        self.focused_file = None
        self.user_actions_map = {
            usim.Create_file_desire: self.agent_actions_desire_triplets_u,
            usim.Change_directory_desire: self.agent_actions_desire_triplets_u,
            usim.Delete_file_desire: self.agent_actions_desire_triplets_u,
            usim.u_inform: self.inform_triplets_u,
            usim.confirm: self.ask_triplets_u,
            usim.deny: self.ask_triplets_u,
            usim.default: self.default,
            usim.end: self.default
        }
        self.children = {}
        self.parent = {}
        self.nodes_by_name = {}
        self.name_by_node = {}
        self.file_exists = set()
        self.file_type = {}
        self.root = None
        self.current_path_node, self.current_path = None, None
        self.add_known_files_to_graph()
        self.agent_actions_map = {
            "Create_file": self.create_file_triplets_a,
            "Delete_file": self.delete_file_triplets_a,
            "Change_directory": self.change_directory_triplets_a,
            "inform": self.default,
            "ask": self.ask_triplets_a,
            "request": self.request_triplets_a
        }

    def reset(self, size, ontology, one_hot=True, lazy_encoding=True):
        super().reset(size, ontology, one_hot, lazy_encoding)
        self.focused_file = None
        self.children = {}
        self.parent = {}
        self.nodes_by_name = {}
        self.name_by_node = {}
        self.file_exists = set()
        self.file_type = {}
        self.root = None
        self.current_path_node, self.current_path = None, None
        self.add_known_files_to_graph()

    def get_possible_actions(self, encode_actions=True):
        actions = []
        is_file_map = {fbrowser.Directory: 0, fbrowser.RegFile: 1, fbrowser.File: -1}
        actions.append({'intent': 'Change_directory',
                        'new_directory': '~/',
                        'file_node': self.root, 'action_node': fbrowser.Change_directory})

        def ask_action(act):
            return {'intent': 'ask', 'action': act}

        for key in self.parent:
            if key in self.name_by_node:
                value = self.name_by_node[key]
                is_file = is_file_map[self.file_type[key]]
                if key in self.file_exists:
                    actions.append({'intent': 'Delete_file', 'file_name': value,
                                    'path': self.get_path_of_file_node(key, False),
                                    'action_node': fbrowser.Delete_file, 'file_node': key})
                    if self.file_type[key] == fbrowser.Directory:
                        actions.append({'intent': 'Change_directory',
                                        'new_directory': self.get_path_of_file_node(key),
                                        'file_node': key, 'action_node': fbrowser.Change_directory})
                else:
                    if is_file == -1:
                        actions.append({'intent': 'Create_file', 'file_name': value, 'is_file': 0,
                                        'path': self.get_path_of_file_node(key, False), 'file_node': key,
                                        'action_node': fbrowser.Create_file})
                        actions.append({'intent': 'Create_file', 'file_name': value, 'is_file': 1,
                                        'path': self.get_path_of_file_node(key, False), 'file_node': key,
                                        'action_node': fbrowser.Create_file})
                    else:
                        actions.append({'intent': 'Create_file', 'file_name': value, 'is_file': is_file,
                                        'path': self.get_path_of_file_node(key, False), 'file_node': key,
                                        'action_node': fbrowser.Create_file})
                    actions.append({'intent': 'request', 'slot': 'parent_directory',
                                    'file_name': value, 'file_node': key, 'action_node': fbrowser.A_request})
            else:
                actions.append({'intent': 'request', 'slot': 'file_name',
                                'file_node': key, 'action_node': fbrowser.A_request})

        action_nodes = [(m['action_node'], m['file_node']) for m in actions]
        actions = sum([[act, ask_action(act)] for act in actions], [])
        if encode_actions:
            action_nodes = self.transform_nodes_rdf_to_encoding(action_nodes)
        else:
            action_nodes = [self.graph.get_encoded_list_nodes(a) for a in action_nodes]
        return action_nodes, actions

    def get_action_size(self):
        return self.node_size * 2

    def update_inner_state(self, triplets):
        super().update_inner_state(triplets)
        for s, p, o in triplets:
            if p == onto.rdf_type and o in (fbrowser.Directory, fbrowser.RegFile, fbrowser.File):
                self.set_file_in_inner_state(s)
                self.set_file_type(s, o)
            if p == fbrowser.has_name:
                self.set_file_name(s, o)
            if p == fbrowser.contains_file:
                self.set_file_in_inner_state(o, s)

    ############## USER ACTION TRIPLETS

    def get_triplets_from_action(self, user_action):
        """

        :param (dict) user_action:
        :return (list): list of triplets from user's action
        """
        return self.user_actions_map[user_action['intent']](user_action)

    def default(self, user_action):
        return []

    # TODO OPTIONAL ADD_USER_ACTION NODES
    def inform_triplets_u(self, user_action):
        # print('inform triplets:',user_action)
        triplets = []
        assert 'inform' == user_action['intent'], "intent is not inform inside inform_triplets method"
        if 'file_name' in user_action:
            self.update_focused_file({'file_name': user_action['file_name']})
            triplets.append((self.focused_file['node'], fbrowser.has_name, Literal(user_action['file_name'])))
            return triplets
        if 'parent_directory' in user_action:
            t = self.get_file_from_graph({'file_name': user_action['parent_directory']})
            # t = self.ontology.triples((None,fbrowser.has_name,Literal(user_action['parent_directory'])))
            if t is None:
                directory = BNode()
                triplets.append((directory, fbrowser.has_name, Literal(user_action['parent_directory'])))
                triplets.append((directory, onto.rdf_type, fbrowser.Directory))
            else:
                directory = t
            f = self.get_focused_file_node()
            triplets.append((directory, fbrowser.contains_file, f))
        return triplets

    def ask_triplets_u(self, user_action):
        triplets = []
        prev_aAction = self.state_map['last_agent_action']
        if prev_aAction['intent'] != 'ask':
            print('confirming not "ask" intent', file=sys.stderr)
            return triplets
        node = prev_aAction['action_node']
        if user_action['intent'] == 'confirm':
            triplets.append((fbrowser.User, fbrowser.confirm, node))
        else:
            triplets.append((fbrowser.User, fbrowser.deny, node))
        return triplets

    def agent_actions_desire_triplets_u(self, user_action):
        triplets = []
        desires = {
            usim.Change_directory_desire: (fbrowser.Change_directory, fbrowser.Directory),
            usim.Delete_file_desire: (fbrowser.Delete_file, fbrowser.File),
            usim.Create_file_desire: (fbrowser.Create_file, None)
        }
        desire, file_type = desires[user_action['intent']]
        if file_type is None:
            file_type = fbrowser.File if 'is_file' not in user_action \
                else fbrowser.Directory if not user_action['is_file'] else fbrowser.RegFile
        if desire == fbrowser.Change_directory:
            user_action['file_name'] = user_action['directory']
        file_node = self.get_file_from_graph(user_action)
        if file_node is None:
            file_node = BNode()
            triplets.append((file_node, onto.rdf_type, file_type))
            if 'file_name' in user_action:
                triplets.append((file_node, fbrowser.has_name, Literal(user_action['file_name'])))
            if 'parent_directory' in user_action:
                parent_dir = self.get_file_from_graph({'file_name': user_action['parent_directory']})
                if parent_dir is None:
                    parent_dir = BNode()
                    triplets.append((parent_dir, onto.rdf_type, fbrowser.Directory))
                    triplets.append((parent_dir, fbrowser.has_name, Literal(user_action['parent_directory'])))
                triplets.append((parent_dir, fbrowser.contains_file, file_node))
        file_info = user_action.copy()
        file_info['node'] = file_node
        file_info['type'] = file_type
        self.set_focused_file(file_info)
        # d = BNode()
        # triplets.append((d, onto.rdf_type, desire))
        # triplets.append((fbrowser.User, fbrowser.has_desire, d))
        triplets.append((desire, fbrowser.has_parameter, file_node))
        return triplets

    ################ AGENT ACTION TRIPLETS

    def get_triplets_from_agent_action(self, agent_action):
        """

        :param (dict) agent_action:
        :return (list): list of triplets from user's action
        """
        return self.agent_actions_map[agent_action['intent']](agent_action)

    def ask_triplets_a(self, agent_action):
        triplets = []
        assert 'ask' == agent_action['intent'], "intent not ask in ask triplets agent method"
        ask_node = BNode()
        agent_action['action_node'] = ask_node
        triplets.append((ask_node, onto.rdf_type, fbrowser.A_ask))
        # TODO FIX ACTION_NODE
        triplets.append((ask_node, fbrowser.has_parameter, agent_action['action']['action_node']))
        # triplets.append((fbrowser.Agent, fbrowser.a_acted, ask_node))
        return triplets

    def request_triplets_a(self, agent_action):
        triplets = []
        # req_node = BNode()
        # triplets.append((req_node, onto.rdf_type, fbrowser.A_request))
        # triplets.append((fbrowser.Agent, fbrowser.a_acted, req_node))
        triplets.append((fbrowser.Agent, fbrowser.a_acted, fbrowser.A_request))
        return triplets

    def create_file_triplets_a(self, agent_action):
        triplets = []
        file_node = agent_action['file_node']
        # action_node = BNode()
        # triplets.append((action_node, onto.rdf_type, fbrowser.Create_file))
        triplets.append((fbrowser.Create_file, fbrowser.has_parameter, file_node))
        # triplets.append((fbrowser.Agent, fbrowser.a_acted, action_node))
        # update inner state
        self.add_file_existence(file_node)
        return triplets

    def delete_file_triplets_a(self, agent_action):
        triplets = []
        # action_node = BNode()
        # triplets.append((action_node, onto.rdf_type, fbrowser.Delete_file))
        triplets.append((fbrowser.Delete_file, fbrowser.has_parameter, agent_action['file_node']))
        # triplets.append((fbrowser.Agent, fbrowser.a_acted, action_node))

        # update inner state
        self.remove_file_existence(agent_action['file_node'])
        return triplets

    def change_directory_triplets_a(self, agent_action):
        triplets = []
        action_node = BNode()
        # triplets.append((action_node, onto.rdf_type, fbrowser.Change_directory))
        triplets.append((fbrowser.Change_directory, fbrowser.change_dir_to, agent_action['file_node']))
        # triplets.append((fbrowser.Agent, fbrowser.a_acted, action_node))

        # update inner state
        self.change_directory_node(agent_action['file_node'])
        return triplets

    ############### FILE RELATED METHODS

    def set_focused_file(self, file_info):
        self.focused_file = {'node': file_info['node'], 'type': file_info['type']}
        if 'file_name' in file_info:
            self.focused_file['file_name'] = file_info['file_name']
        if 'parent_directory' in file_info:
            self.focused_file['parent_directory'] = file_info['parent_directory']

    def update_focused_file(self, file_info):
        if 'node' in file_info:
            self.focused_file['node'] = file_info['node']
        if 'type' in file_info:
            self.focused_file['type'] = file_info['type']
        if 'file_name' in file_info:
            self.focused_file['file_name'] = file_info['file_name']
        if 'parent_directory' in file_info:
            self.focused_file['parent_directory'] = file_info['parent_directory']

    def get_focused_file_node(self):
        prev = self.state_map['last_agent_action']
        if prev['intent'] == 'request':
            return prev['file_node']  # TODO add node to agent action
        return self.focused_file['node']

    def add_root_file(self):
        """
        adds root directory
        :return: root's node and root's name
        """
        triplets = []
        root_uri = fbrowser.prefix1 + "root_directory"
        name = "~"
        root = rdflib.URIRef(root_uri)
        self.add_file_existence(root)
        self.root = root
        self.file_type[root] = fbrowser.Directory
        triplets.append((root, onto.rdf_type, fbrowser.Directory))
        self.nodes_by_name[name] = [root]
        self.name_by_node[root] = name
        triplets.append((root, fbrowser.has_name, Literal(name)))
        self.current_path_node, self.current_path = root, name
        self.add_triplets(triplets)

    def add_known_files_to_graph(self):
        """
        adds root directory for now
        :return: root's node and root's name
        """
        self.add_root_file()

    def add_file_existence(self, file_node):
        self.file_exists.add(file_node)
        if file_node in self.parent:
            p = self.parent[file_node]
            if p not in self.file_exists:
                self.add_file_existence(p)


    def remove_file_existence(self, file_node):
        self.file_exists.remove(file_node)
        if file_node not in self.children:
            return
        for c in self.children[file_node]:
            if c in self.file_exists:
                self.remove_file_existence(c)

    def get_path_of_file(self, file_name):
        """
        gets file's ancestors
        :param file_name:
        :return:
        """
        assert file_name in self.nodes_by_name, str(file_name) + " not in inner state of state tracker"
        node = self.choose_suitable_node(self.nodes_by_name[file_name])
        return self.get_path_of_file_node(node)

    def get_path_of_file_node(self, node, add_self=True):
        """
        gets file's ancestors
        :param node:
        :return:
        """
        if node == self.root:
            return self.root
        assert node in self.parent, "PATH FROM NODE ERROR: node has no parent directory"
        file_name = self.name_by_node[node]
        path = file_name if add_self else ""
        node = self.parent[node]
        while True:
            path = self.name_by_node[node] + '/' + path
            if node not in self.parent:
                break
            node = self.parent[node]
        return path

    def choose_suitable_node(self, nodes):
        # TODO implement LCA to find most plausible node
        return nodes[0]

    def set_file_in_inner_state(self, s, parent=None):
        if parent is None:
            parent = self.current_path_node
        if parent == s:  # case root do nothing
            return
        if s in self.parent:
            assert self.parent[s] in self.children, str(s) + " has parent " + str(self.parent[s]) + \
                                                    " but is not in parent's children"
            self.children[self.parent[s]].remove(s)
        self.parent[s] = parent
        if parent not in self.children:
            self.children[parent] = set()
        self.children[parent].add(s)

    def set_file_name(self, s, o):
        o = str(o)
        if o not in self.nodes_by_name:
            self.nodes_by_name[o] = []
        self.nodes_by_name[o].append(s)
        self.name_by_node[s] = o

    def set_file_type(self, s, o):
        self.file_type[s] = o

    def change_directory(self, path):
        dirs = path.split('/')
        if dirs[-1] == "":
            del dirs[-1]
        node = self.choose_suitable_node(self.nodes_by_name[dirs[0]])
        for dir in dirs[1:]:
            children = self.children[node]
            found = False
            for child in children:
                if self.name_by_node[child] == dir:
                    node = child
                    found = True
            if not found:
                raise Exception('incorrect path exception')
        self.change_directory_node(node)

    def change_directory_node(self, node):
        self.current_path, self.current_path_node = self.get_path_of_file_node(node), node

    def get_file_from_graph(self, file_info):
        """
        gets file's node from graph, None if it does not exist
        :param file_info:
        :return:
        """
        if 'file_name' not in file_info:
            return None
        file_name = file_info['file_name']
        if file_name not in self.nodes_by_name:
            return None
        nodes = self.nodes_by_name[file_name]
        if 'parent_directory' in file_info:
            parent = file_info['parent_directory']
            nodes = [n for n in self.nodes_by_name[file_name]
                     if n in self.parent and self.name_by_node[self.parent[n]] == parent
                     ]
            if not len(nodes):
                return None
        return self.choose_suitable_node(nodes)


if __name__ == '__main__':
    state_tracker = StateTrackerFB(1, fbrowser.graph)
