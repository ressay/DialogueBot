"""
RDF Graph class
"""

class Graph(object):
    def __init__(self,triplets) -> None:
        """
        graph constructor
        :param triplets: contains 3-tuples subject predicate object as RDF triplets
        """
        super().__init__()
        self.triplets = []
        self.id_triplets = []
        self.nodes = [None]
        self.edges = [None]
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
        :param (str) edge: URI of the edge
        :return:
        """
        if edge not in self.edge_id:
            self.edge_id[edge] = len(self.edges)
            self.edges.append(edge)

    def add_triplet(self,s,p,o):
        """
        adds triplet to the graph
        :param (str) s: URI of the subject node
        :param (str) p: URI of the predicate edge
        :param (str) o: URI of the object node
        :return:
        """
        self._add_node(s)
        self._add_node(o)
        self._add_edge(p)
        self.id_triplets.append((self.node_id[s], self.edge_id[p], self.node_id[o]))

    def init_triplets(self,triplets):
        """
        creates a graph with list of triplets given in parameters
        :param (iterable) triplets: list of triplets
        :return:
        """
        self.triplets = triplets
        for s,p,o in triplets:
            self.add_triplet(s,p,o)

    def add_all(self,triplets):
        for s,p,o in triplets:
            self.add_triplet(s,p,o)

    def get_encoded_triplets(self, triplets):
        return [self.get_encoded_triplet(t) for t in triplets]

    def get_encoded_triplet(self,t):
        """
        map triplet URIs to their ids
        :param t:
        :return: tuple of integers, id of each URI given in input
        """
        s,p,o = t
        return self.node_id[s],self.edge_id[p],self.node_id[o]

    def get_decoded_triplet(self,t):
        """
        map triplet ids to their URIs
        :param t:
        :return: tuple of integers, URI of each id given in input
        """
        s,p,o = t
        return self.nodes[s],self.edges[p],self.nodes[o]

    def get_encoded_list_nodes(self,nodes):
        """
        map triplet URIs to their ids
        :param t:
        :return: tuple of integers, id of each URI given in input
        """
        return [self.node_id[n] for n in nodes]

