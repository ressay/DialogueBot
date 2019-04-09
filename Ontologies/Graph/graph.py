"""
RDF Graph class
"""

class Graph(object):
    def __init__(self,triplets:list) -> None:
        """
        graph constructor
        :param triplets (list): contains 3-tuples subject predicate object as RDF triplets
        """
        super().__init__()
        self.triplets = []
        self.id_triplets = []
        self.nodes = []
        self.edges = []
        self.node_id = {}
        self.edge_id = {}
        self.init_triplets(triplets)

    def _add_node(self,node):
        """
        adds node's URI map to local integer id
        :param node (string): URI of the node
        :return:
        """
        if node not in self.node_id:
            self.node_id[node] = len(self.nodes)
            self.nodes.append(node)

    def _add_edge(self,edge):
        """
        adds edge's URI map to local integer id
        :param edge (string): URI of the edge
        :return:
        """
        if edge not in self.edge_id:
            self.edge_id[edge] = len(self.edges)
            self.edges.append(edge)

    def add_triplet(self,s,p,o):
        """
        adds triplet to the graph
        :param s (string): URI of the subject node
        :param p (string): URI of the predicate edge
        :param o (string): URI of the object node
        :return:
        """
        self._add_node(s)
        self._add_node(o)
        self._add_edge(p)
        self.id_triplets.append((self.node_id[s], self.edge_id[p], self.node_id[o]))

    def init_triplets(self,triplets:list):
        """
        creates a graph with list of triplets given in parameters
        :param triplets (list): list of triplets
        :return:
        """
        self.triplets = triplets
        for s,p,o in triplets:
            self.add_triplet(s,p,o)

    def get_encoded_triplet(self,t):
        """
        map triplet URIs to their ids
        :param t:
        :return: tuple of integers, id of each URI given in input
        """
        s,p,o = t
        return self.node_id[s],self.edge_id[p],self.node_id[o]

