import torch
import torch.nn.functional as F
from torch import nn

# TODO: keras model. To transform into pytorch.
# print ('constructing network...')
# ep = Sequential()
# eg = Sequential()
#
# ep.add(Embedding(nb_patient, p_emb_size, input_length=1, embeddings_regularizer=l2(1e-5)))
# eg.add(Embedding(nb_genes, g_emb_size, input_length=1, embeddings_regularizer=l2(1e-5)))
#
# model = Sequential()
# model.add(Merge([ep, eg], mode='concat'))
# model.add(Flatten())
# model.add(Dense(150, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(100, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(75, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(50, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(25, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(10, activation='tanh', kernel_regularizer=l2(1e-5)))
# model.add(Dense(1))


class FactorizedMLP(nn.Module):

    def __init__(self, layers_size, inputs_size, emb_size=2):
        super(FactorizedMLP, self).__init__()

        self.layers_size = layers_size
        self.emb_size = emb_size
        self.inputs_size = inputs_size


        # The embedding
        # TODO: At one point we will probably need to refactor that for it to be more general. Maybe.
        assert len(inputs_size) == 2

        self.emb_1 = nn.Embedding(inputs_size[0], emb_size)
        self.emb_2 = nn.Embedding(inputs_size[1], emb_size)

        # The list of layers.
        layers = []
        dim = [emb_size * 2] + layers_size # Adding the emb size.
        for size_in, size_out in zip(dim[:-1], dim[1:]):
            layer = nn.Linear(size_in, size_out)
            layers.append(layer)

        self.mlp_layers = nn.ModuleList(layers)

        # Last layer
        self.last_layer = nn.Linear(dim[-1], 1)

    def get_embeddings(self, x):

        gene, patient = x[:, 0], x[:, 1]
        # Embedding.
        gene = self.emb_1(gene.long())
        patient = self.emb_2(patient.long())

        return gene, patient

    def forward(self, x):


        # Get the embeddings
        emb_1, emb_2 = self.get_embeddings(x)

        # Forward pass.
        mlp_input = torch.cat([emb_1, emb_2], 1)

        # TODO: the proper way in pytorch is to use a Sequence layer.
        for layer in self.mlp_layers:
            mlp_input = layer(mlp_input)
            mlp_input = F.tanh(mlp_input)

        mlp_output = self.last_layer(mlp_input)

        return mlp_output

class BagFactorizedMLP(FactorizedMLP):

    '''
    Simple bag of words approach. Each kmers is a word. We only sum them.
    '''

    def get_embeddings(self, x):

        kmer, patient = x[:, :-1], x[:, -1]
        # Embedding.
        kmer = self.emb_1(kmer.squeeze(-1).long())
        patient = self.emb_2(patient.long())

        # Sum the embeddings (TODO: try fancy RNN and stuff)
        kmer = kmer.sum(dim=1)
        patient = patient.sum(dim=1)

        return kmer, patient

def get_model(opt, inputs_size):

    # All of the different models.

    # TODO: find a way to remove the if.
    if opt.model == 'factor':
        model_class = FactorizedMLP
    elif opt.model == 'bag':
        model_class = BagFactorizedMLP
    else:
        raise NotImplementedError()


    model = model_class(layers_size=opt.layers_size, emb_size=opt.emb_size, inputs_size=inputs_size)

    return model
