from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import h5py
import pdb
from collections import OrderedDict
import shutil

class GeneDataset(Dataset):
    """Gene expression dataset"""

    def __init__(self, root_dir='.', data_path='30by30_dataset.npy', data_type_path='30by30_types.npy', data_subtype='30by30_subtypes.npy', transform=None):


        data_path = os.path.join(root_dir, data_path)
        data_type_path = os.path.join(root_dir, data_type_path)
        data_subtype = os.path.join(root_dir, data_subtype)

        # Load the dataset
        self.data, self.data_type, self.data_subtype = np.load(data_path), np.load(data_type_path), np.load(data_subtype)

        self.nb_gene = self.data.shape[0]
        self.nb_tissue = len(set(self.data_type))
        self.nb_patient = self.data.shape[1]

        # TODO: for proper pytorch form, we should probably do that on the fly, but heh. todo future me.
        self.X_data, self.Y_data = self.dataset_make(self.data, log_transform=True)
        #self.X_data = self.X_data[:1000]
        #self.Y_data = self.Y_data[:1000]

        #import ipdb; ipdb.set_trace()

        self.root_dir = root_dir
        self.transform = transform # heh

    def __len__(self):
        return len(self.X_data)

    def __getitem__(self, idx):

        sample = self.X_data[idx]
        label = self.Y_data[idx]

        sample = [sample, label]

        if self.transform:
            sample = self.transform(sample)

        return sample

    def dataset_make(self, gene_exp, log_transform=True):

        #    indices_p1 = numpy.random.randint(0, gene_exp.shape[1]-1,nb_examples)
        indices_p1 = np.arange(gene_exp.shape[1])
        indices_g = np.arange(gene_exp.shape[0])
        X_data = np.transpose([np.tile(indices_g, len(indices_p1)), np.repeat(indices_p1, len(indices_g))])
        Y_data = gene_exp[X_data[:, 0], X_data[:, 1]]

        print "Total number of examples: ", Y_data.shape

        if log_transform:
            Y_data = np.log10(Y_data + 1)
        return X_data, Y_data

    def input_size(self):
        return self.nb_gene, self.nb_patient

    def extra_info(self):
        # get some extra info to dumb with the embeddings.
        info = OrderedDict()
        info['type'] = self.data_type
        info['subtype'] = self.data_subtype
        return info

class KmerDataset(Dataset):

    def __init__(self, root_dir='/data/milatmp1/dutilfra/dataset/kmer/', data_path='duodenum1.24.hdf5', tmp_folder='/Tmp/dutilfra/dataset/kmer/' , transform=None):


        tmp_path = os.path.join(tmp_folder, data_path)
        data_path = os.path.join(root_dir, data_path)

        if not os.path.exists(tmp_folder):
            print "Copying the data in {}...".format(tmp_path)
            os.makedirs(tmp_folder)
            shutil.copyfile(data_path, tmp_path)
            print "Done!"
            data_path = tmp_path


        # Load the dataset
        self.data = h5py.File(data_path)['kmer']
        #self.data = np.array(self.data)


        self.nb_kmer = self.data.shape[0]
        self.nb_tissue = 1 # TODO
        self.nb_patient = 1 # TODO

        self.root_dir = root_dir
        self.transform = transform # heh

    def __len__(self):
        return len(self.data)

    def process_data(self, data):

        kmers = data[:, 0]
        counts = data[:, 1]

        # Turn the kmer in vocab of [0, 1, 2, 3] (A, C, G, T)
        # We should probably do that in the other file. And more properly.
        kmers_int = []
        for kmer in kmers:
            kmer = kmer.replace('A', '0').replace('C', '1').replace('G', '2').replace('T', '3')
            kmer = np.array(list(kmer), dtype=int).reshape((-1, 1))

            # Adding the patient id (TODO: For now there is only one patient)
            kmer = [kmer, 0]

            kmers_int.append(kmer)

        #kmers_int = np.array(kmers_int)
        # Take the log of the counts, (to check)
        counts = np.log(counts.astype(int) + 1)

        return kmers_int, counts

    def __getitem__(self, idx):
        #pdb.set_trace()

        #import ipdb; ipdb.set_trace()

        sample = self.data[idx, :-1]
        label = self.data[idx, -1]
        label = np.log(label)
        #print sample, label

        #sample = [list(x.replace('A', '0').replace('C', '1').replace('G', '2').replace('T', '3')) for x in sample]
        #sample = np.array(sample).astype(int)
        #import ipdb; ipdb.set_trace()

        sample = np.pad(sample, ((0, 1),), 'constant', constant_values=(0,))# adding the patient TODO: the real one.


        sample = [sample, label]

        if self.transform:
            sample = self.transform(sample)


        return sample

    def input_size(self):

        # 4 for [A, C, G, T]
        # We have only one patient right now. (TODO: add more patient)

        return 4, 1

    def extra_info(self):
        # get some extra info to dumb with the embeddings.
        info = OrderedDict()
        return info

def get_dataset(opt):

    # All of the different datasets.

    if opt.dataset == 'gene':
        dataset = GeneDataset(root_dir=opt.data_dir)
    elif opt.dataset == 'kmer':
        dataset = KmerDataset()
    else:
        raise NotImplementedError()
    #import ipdb;
    #ipdb.set_trace()

    #TODO: check the num_worker, might be important later on, for when we will use a bunch of big files.
    dataloader = DataLoader(dataset, batch_size=opt.batch_size,
                            shuffle=True, num_workers=1)

    return dataloader
