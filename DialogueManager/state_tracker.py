from keras import Model
import numpy as np

class StateTracker(object):
    encoder_size = 50
    def __init__(self,size,ontology) -> None:
        super().__init__()
        self.cursor = 0
        self.encoder = self.load_encoder()
        self.vectors = [np.zeros(self.encoder_size) for i in range(size)]
        self.ontology = ontology

    def get_state_size(self):
        return self.encoder_size*len(self.vectors)

    def load_encoder(self):
        model = Model()
        model.load_weights('encoder.h5')
        return model

    def get_state(self):
        return np.concatenate(self.vectors,axis=None)

    def transform_graph(self,graph):
        return graph

    def add_sub_graph(self,graph):
        graph = self.transform_graph(graph)
        i = self.cursor
        self.vectors[i] = self.encoder.predict((graph,self.vectors[i]))
        self.cursor = (self.cursor+1) % len(self.vectors)