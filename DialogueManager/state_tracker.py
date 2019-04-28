import math

import numpy as np
import rdflib
from keras import Model
import Ontologies.onto_fbrowser as fbrowser
from Ontologies import graph
from keras.models import load_model


def to_int_onehot(arr):
    return np.argmax(arr)


def to_int_binary(bitlist):
    out = 0
    for bit in bitlist:
        bit = int(round(bit))
        out = (out << 1) | bit
    return out


def bin_array(num, m):
    """Convert a positive integer num into an m-bit bit numpy array"""
    return np.array(list(np.binary_repr(num).zfill(m))).astype(np.int8)


def onehot_array(num, m):
    """Convert a positive integer num into one_hot numpy array"""
    arr = np.zeros(m)
    arr[num] = 1
    return arr


class StateTracker(object):
    encoder_size = 20
    node_size = 9
    edge_size = 7
    triplet_size = 2 * node_size + edge_size

    def __init__(self, size, ontology) -> None:
        """
        StateTracker constructor
        :param (int) size:
        :param (rdflib.Graph) ontology:
        """
        super().__init__()
        self.cursor = 0
        self.encoder = self.load_encoder()
        size = int(math.ceil(size / self.encoder_size))
        self.vectors = [np.zeros(self.encoder_size) for i in range(size)]
        self.ontology = rdflib.Graph()
        self.ontology += ontology
        self.graph = graph.Graph(ontology.triples((None, None, None)))
        self.recent_user_triplets = []
        self.recent_agent_triplets = []
        self.all_episode_triplets = []
        self.state_map = {
            'ontology': self.ontology,
            'graph': self.graph,
            'recent_triplets': self.recent_user_triplets,
            'recent_agent_triplets': self.recent_agent_triplets,
            'last_user_action': None,
            'last_agent_action': None
        }

    def get_possible_actions(self):
        """
        gets the possible action given current state
        method to be redefined by children state trackers
        :return (np.array,list) : a numpy array that contains action's triples encodings
        and a list of tuples that contains action dict and its "ask" method
        """
        return np.array([]), []

    def get_action_size(self):
        return 1

    def get_state_size(self):
        return self.encoder_size * len(self.vectors)

    def load_encoder(self, one_hot=True):
        model = None
        if one_hot:
            self.int_to_vec = onehot_array
            self.vec_to_int = to_int_onehot
            path = 'model_onehot.h5'
            self.node_size = 2 ** self.node_size
            self.edge_size = 2 ** self.edge_size
        else:
            self.int_to_vec = bin_array
            self.vec_to_int = to_int_binary
            path = 'model_binary.h5'
        self.triplet_size = 2 * self.node_size + self.edge_size
        # model = load_model(path)
        return model

    def get_state(self, encoded=True):
        self.state_map['recent_triplets'] = self.recent_user_triplets
        if encoded:
            self.state_map['encoded'] = np.concatenate(self.vectors, axis=None)
        return self.state_map

    def triplet_encoding_shape(self, number_of_triplets):
        return number_of_triplets, self.triplet_size

    def nodes_encoding_shape(self, number_of_tuples, number_of_nodes):
        return number_of_tuples, number_of_nodes * self.node_size

    def encode_triplet(self, s, p, o):
        return np.concatenate((self.int_to_vec(s, self.node_size),
                               self.int_to_vec(p, self.edge_size),
                               self.int_to_vec(o, self.node_size)))

    def encode_nodes(self, nodes):
        return np.concatenate([self.int_to_vec(n, self.node_size) for n in nodes])

    def transform_nodes_rdf_to_encoding(self, nodes):

        transformed = np.zeros(self.nodes_encoding_shape(len(nodes), len(nodes[0])))
        for i, (ns) in enumerate(nodes):
            ns = self.graph.get_encoded_list_nodes(ns)
            encoded = self.encode_nodes(ns)
            transformed[i, :] = encoded
        return transformed

    def transform_triplets_rdf_to_encoding(self, triplets, encoded_triplets=False):
        """
        transforms rdflib.Graph to encoded graph
        :param (iterable) triplets: sub graph to transform
        :return (numpy.array): encoded triplets
        """

        transformed = np.zeros(self.triplet_encoding_shape(len(triplets)))
        for i, (s, p, o) in enumerate(triplets):
            if not encoded_triplets:
                s, p, o = self.graph.get_encoded_triplet((s, p, o))
            encoded = self.encode_triplet(s, p, o)
            transformed[i, :] = encoded
        return transformed

    def add_sub_graph(self, graph):
        """
        adds sub_graph to state's knowledge graph
        :param (rdflib.Graph) graph:
        :return:
        """
        self.add_triplets(graph.triples((None, None, None)))

    def add_triplets(self, triplets):
        self.graph.add_all(triplets)
        self.ontology += triplets
        self.update_inner_state(triplets)

    def update_inner_state(self, triplets):
        """
        method to be redefined by children classes to update inner variables for fast graph manipulation if needed
        :param (list) triplets: a list of triplets to be added to the knowledge graph
        :return:
        """
        pass

    def encode_triplets(self, triplets):
        """
        adds triplets to state's knowledge graph
        :param (list) triplets: list of triplets to add to state graph
        :return:
        """
        graph = self.transform_triplets_rdf_to_encoding(triplets)
        i = self.cursor
        self.vectors[i] = self.encoder.predict([graph, self.vectors[i]])
        self.cursor = (self.cursor + 1) % len(self.vectors)

    def get_triplets_from_action(self, user_action):
        """

        :param (dict) user_action:
        :return (list): list of triplets from user's action
        """
        return []

    def get_triplets_from_agent_action(self, agent_action):
        """

        :param (dict) agent_action:
        :return (list): list of triplets from user's action
        """
        return []

    def add_to_all_triplets(self,triplets):
        self.all_episode_triplets += self.graph.get_encoded_triplets(triplets)

    def update_state_user_action(self, user_action, update_encoding=True):
        self.state_map['last_user_action'] = user_action
        self.recent_user_triplets = self.get_triplets_from_action(user_action)
        self.add_triplets(self.recent_user_triplets)
        self.all_episode_triplets += self.recent_user_triplets
        if update_encoding:
            self.encode_triplets(self.recent_user_triplets)

    def update_state_agent_action(self, agent_action, update_encoding=True):
        self.state_map['last_agent_action'] = agent_action
        self.recent_agent_triplets = self.get_triplets_from_agent_action(agent_action)
        self.add_triplets(self.recent_agent_triplets)
        self.all_episode_triplets += self.recent_agent_triplets
        if update_encoding:
            self.encode_triplets(self.recent_agent_triplets)

    def get_new_triplets(self):
        new_triplets = self.recent_agent_triplets + self.recent_user_triplets
        return self.transform_triplets_rdf_to_encoding(new_triplets)

    def get_episode_triplets(self):
        return self.transform_triplets_rdf_to_encoding(self.all_episode_triplets, encoded_triplets=True)


if __name__ == '__main__':
    state = StateTracker(5, fbrowser.graph)
    print(state.transform_triplets_rdf_to_encoding(fbrowser.graph.triples()).shape)
