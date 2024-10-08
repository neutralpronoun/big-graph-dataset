import os
import torch
from torch.nn.functional import one_hot
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from torch_geometric.data import InMemoryDataset, Data
from tqdm import tqdm
from ..utils import describe_one_dataset
import random

from torch_geometric.datasets import TUDataset
from torch_geometric.io import fs, read_tu_data
import os.path as osp
import fsspec

# from ogb.utils.features import get_atom_feature_dims, get_bond_feature_dims
# from ogb.graphproppred import PygGraphPropPredDataset


# full_atom_feature_dims = get_atom_feature_dims()
# full_bond_feature_dims = get_bond_feature_dims()


# def to_onehot_atoms(x):
#     one_hot_tensors = []
#     for i, num_values in enumerate(full_atom_feature_dims):
#         one_hot = torch.nn.functional.one_hot(x[:, i], num_classes=num_values)
#         one_hot_tensors.append(one_hot)

#     return torch.cat(one_hot_tensors, dim=1)

# def to_onehot_bonds(x):
#     one_hot_tensors = []
#     for i, num_values in enumerate(full_bond_feature_dims):
#         one_hot = torch.nn.functional.one_hot(x[:, i], num_classes=num_values)
#         one_hot_tensors.append(one_hot)

#     return torch.cat(one_hot_tensors, dim=1)


# Having this and mv defined here seems to fix issues that were present using the originals from TorchGeometric. I do not know why - aod.
def get_fs(path: str) -> fsspec.AbstractFileSystem:
    r"""Get filesystem backend given a path URI to the resource.

    Here are some common example paths and dispatch result:

    * :obj:`"/home/file"` ->
      :class:`fsspec.implementations.local.LocalFileSystem`
    * :obj:`"memory://home/file"` ->
      :class:`fsspec.implementations.memory.MemoryFileSystem`
    * :obj:`"https://home/file"` ->
      :class:`fsspec.implementations.http.HTTPFileSystem`
    * :obj:`"gs://home/file"` -> :class:`gcsfs.GCSFileSystem`
    * :obj:`"s3://home/file"` -> :class:`s3fs.S3FileSystem`

    A full list of supported backend implementations of :class:`fsspec` can be
    found `here <https://github.com/fsspec/filesystem_spec/blob/master/fsspec/
    registry.py#L62>`_.

    The backend dispatch logic can be updated with custom backends following
    `this tutorial <https://filesystem-spec.readthedocs.io/en/latest/
    developer.html#implementing-a-backend>`_.

    Args:
        path (str): The URI to the filesystem location, *e.g.*,
            :obj:`"gs://home/me/file"`, :obj:`"s3://..."`.
    """
    return fsspec.core.url_to_fs(path)[0]


def mv(path1: str, path2: str) -> None:
    fs1 = get_fs(path1)
    fs2 = get_fs(path2)
    assert fs1.protocol == fs2.protocol
    fs1.mv(path1, path2)

# Redefine download to use above definitions for mv and get_fs
class CustomTUDataset(TUDataset):
    def download(self) -> None:
        url = self.cleaned_url if self.cleaned else self.url
        fs.cp(f'{url}/{self.name}.zip', self.raw_dir, extract=True)
        for filename in fs.ls(osp.join(self.raw_dir, self.name)):
            print(filename == osp.join(self.raw_dir, osp.basename(filename)))
            print(filename, "\n", osp.join(self.raw_dir, osp.basename(filename)))
            mv(filename, osp.join(self.raw_dir, osp.basename(filename)))
        fs.rm(osp.join(self.raw_dir, self.name))

class FromTUDataset(InMemoryDataset):
    r"""
    Contributor: Alex O. Davies (minimal alterations to existing code from PyG)
    
    Contributor email: `alexander.davies@bristol.ac.uk`

    Returns a `torch_geometric.data.InMemoryDataset` for each TUDataset.
    This allows standard dataset operations like concatenation with other datasets.

    The datasets were originally collected in this paper:

        `Morris, Christopher, et al. "TUDataset: A collection of benchmark datasets for learning with graphs." (2020).`

    Args:
        root (str): Root directory where the dataset should be saved.
        ogb_dataset (list): a TUDataset to be converted back to `InMemoryDataset`.
        stage (str): The stage of the dataset to load. One of "train", "val", "test", "None". If None, returns the whole original dataset. Otherwise returns one of a (80,10,10) train/val/test split. This split is shuffled on each new production of the torch geometric data objects. (default: :obj:`None`)
        transform (callable, optional): A function/transform that takes in an :obj:`torch_geometric.data.Data` object and returns a transformed version. The data object will be transformed before every access. (default: :obj:`None`)
        pre_transform (callable, optional): A function/transform that takes in an :obj:`torch_geometric.data.Data` object and returns a transformed version. The data object will be transformed before being saved to disk. (default: :obj:`None`)
        pre_filter (callable, optional): A function that takes in an :obj:`torch_geometric.data.Data` object and returns a boolean value, indicating whether the data object should be included in the final dataset. (default: :obj:`None`)
        num (int): The number of samples to take from the original dataset. -1 takes all available samples for that stage. Ignored if stage is not None. (default: :obj:`-1`).

    **STATS:**

    .. list-table::
        :widths: 20 10 10 10 10 10
        :header-rows: 1

        * - Name
          - #graphs
          - #nodes
          - #edges
          - #features
          - #classes
        * - MUTAG
          - 188
          - ~17.9
          - ~39.6
          - 7
          - 2
        * - ENZYMES
          - 600
          - ~32.6
          - ~124.3
          - 3
          - 6
        * - PROTEINS
          - 1,113
          - ~39.1
          - ~145.6
          - 3
          - 2
        * - COLLAB
          - 5,000
          - ~74.5
          - ~4914.4
          - 0
          - 3
        * - IMDB-BINARY
          - 1,000
          - ~19.8
          - ~193.1
          - 0
          - 2
        * - REDDIT-BINARY
          - 2,000
          - ~429.6
          - ~995.5
          - 0
          - 2
        * - ...
          -
          -
          -
          -
          -
    """
    def __init__(self, root, ogb_dataset, stage = "train", num = -1, transform=None, pre_transform=None, pre_filter=None):
        self.ogb_dataset = ogb_dataset
        self.stage = stage
        self.stage_to_index = {"train":0,
                               "val":1,
                               "test":2,
                               "train-adgcl":3}
        self.num = num
        self.task = "graph-classification"
        print(f"Converting OGB stage {self.stage}")
        super().__init__(root, transform, pre_transform, pre_filter)
        self.data, self.slices = torch.load(self.processed_paths[self.stage_to_index[self.stage]])

    @property
    def raw_file_names(self):
        return ['dummy.csv']

    @property
    def processed_file_names(self):
        return ['train.pt',
                'val.pt',
                'test.pt']


    def process(self):
        # Read data into huge `Data` list.
        if os.path.isfile(self.processed_paths[self.stage_to_index[self.stage]]):
            print(f"\nTU files exist at {self.processed_paths[self.stage_to_index[self.stage]]}")
            return
        print("Got to pyg process")
        data_list = self.ogb_dataset
        num_classes = data_list.num_classes
        data_list = [data for data in data_list]
        random.Random(4).shuffle(data_list)
        print("Shuffled")
        num_samples = len(data_list)
        if self.stage == "train":
            data_list = data_list[:int(0.8 * num_samples)]
        elif self.stage == "val":
            data_list = data_list[int(0.8 * num_samples):int(0.9 * num_samples)]
        elif self.stage == "test":
            data_list = data_list[int(0.9 * num_samples):]

        num_samples = len(data_list)
        keep_n = len(data_list)

        
        if num_samples < self.num:
            keep_n = num_samples
        else:
            keep_n = self.num
        # if self.stage is None:
        #     if num_samples < self.num:
        #         keep_n = num_samples
        #     else:
        #         keep_n = self.num
        # else:

        data_list = data_list[:keep_n]
        print(f"Converting {keep_n} samples")
        for i, item in enumerate(data_list):

            data = Data(x = item.x, 
                        edge_index=item.edge_index,
                        edge_attr= item.edge_attr, 
                        y = one_hot(item.y, num_classes = num_classes))
            
            data_list[i] = data

        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]

        print(data_list)
        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[self.stage_to_index[self.stage]])


def from_tu_dataset(root,  stage="train", num=-1):
    """
    Load a TU dataset and convert it to the Big Graph Dataset format.

    Args:
        name (str): The name of the TU dataset. ("MUTAG", "ENZYMES", "PROTEINS", "COLLAB", "IMDB-BINARY", "REDDIT-BINARY")
        stage (str, optional): The stage of the dataset to load (e.g., "train", "valid", "test", None). Defaults to None, which returns the whole dataset. Otherwise returns one of a (80/10/10) train/val/test split.
        num (int, optional): The number of samples to load. Set to -1 to load all samples. Defaults to -1. Ignored if stage is not None.

    Returns:
        FromOGBDataset: The converted dataset in the Big Graph Dataset format.
    """
    name = root.split('/')[-1]
    root = root[:-len(name)]
    print(root, name)



    dataset = CustomTUDataset(root + name, name)
    return FromTUDataset(root + name, dataset, stage = stage, num = num)

if __name__ == "__main__":
    mutag = from_tu_dataset("bgd_files/PROTEINS", stage = "train")
    describe_one_dataset(mutag)