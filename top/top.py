import logging
import random

import numpy as np
import torch
import yaml
import os
import wget

from unsupervised.encoder import Encoder
from unsupervised.learning import GInfoMinMax
from torch_geometric.loader import DataLoader

from sklearn.metrics.pairwise import cosine_similarity
from umap import UMAP
from sklearn.decomposition import PCA
import matplotlib
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, normalize

from tqdm import tqdm

class L1Normalizer:
    def __init__(self):
        self.norms = None

    def fit(self, embeddings):
        """
        Compute the L1 norms of the embeddings.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - self: The fitted L1Normalizer instance.
        """
        self.norms = np.linalg.norm(embeddings, ord=1, axis=1, keepdims=True)
        return self

    def transform(self, embeddings):
        """
        Apply L1 normalization to the embeddings using the computed norms.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - A numpy array of L1 normalized embeddings.
        """
        if self.norms is None:
            raise ValueError("The model has not been fitted yet. Please call 'fit' with appropriate data before using 'transform'.")
        return embeddings / self.norms

    def fit_transform(self, embeddings):
        """
        Compute the L1 norms and apply L1 normalization to the embeddings.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - A numpy array of L1 normalized embeddings.
        """
        self.fit(embeddings)
        return self.transform(embeddings)

class L2Normalizer:
    def __init__(self):
        self.norms = None

    def fit(self, embeddings):
        """
        Compute the L2 norms of the embeddings.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - self: The fitted L2Normalizer instance.
        """
        self.norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return self

    def transform(self, embeddings):
        """
        Apply L2 normalization to the embeddings using the computed norms.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - A numpy array of L2 normalized embeddings.
        """
        if self.norms is None:
            raise ValueError("The model has not been fitted yet. Please call 'fit' with appropriate data before using 'transform'.")
        return embeddings / self.norms

    def fit_transform(self, embeddings):
        """
        Compute the L2 norms and apply L2 normalization to the embeddings.
        
        Args:
        - embeddings: A numpy array of shape (num_samples, embedding_dim) with data embeddings.
        
        Returns:
        - A numpy array of L2 normalized embeddings.
        """
        self.fit(embeddings)
        return self.transform(embeddings)

def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    np.random.seed(seed)
    random.seed(seed)

def get_emb_y(loader, encoder, device, dtype='numpy', is_rand_label=False, every = 1, node_features = False):
    with torch.no_grad():
        x, y = encoder.get_embeddings(loader, device, is_rand_label, every = every, node_features = node_features)
    if dtype == 'numpy':
        return x,y
    elif dtype == 'torch':
        return torch.from_numpy(x).to(device), torch.from_numpy(y).to(device)
    else:
        raise NotImplementedError



def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                     textcolors=("black", "white"),
                     threshold=None, **textkw):
    """
    A function to annotate a heatmap.

    Parameters
    ----------
    im
        The AxesImage to be labeled.
    data
        Data used to annotate.  If None, the image's data is used.  Optional.
    valfmt
        The format of the annotations inside the heatmap.  This should either
        use the string format method, e.g. "$ {x:.2f}", or be a
        `matplotlib.ticker.Formatter`.  Optional.
    textcolors
        A pair of colors.  The first is used for values below a threshold,
        the second for those above.  Optional.
    threshold
        Value in data units according to which the colors from textcolors are
        applied.  If None (the default) uses the middle of the colormap as
        separation.  Optional.
    **kwargs
        All other arguments are forwarded to each call to `text` used to create
        the text labels.
    """

    if data is None:
        data = im.get_array()

    # Normalize the threshold to the images color range.
    if threshold is not None:
        threshold = im.norm(threshold)
    else:
        # For data between -1 and 1, the middle is 0
        threshold = im.norm(0)

    # Set default alignment to center, but allow it to be
    # overwritten by textkw.
    kw = dict(horizontalalignment="center",
              verticalalignment="center")
    kw.update(textkw)

    # Get the formatter in case a string is supplied
    if isinstance(valfmt, str):
        valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

    # Loop over the data and create a `Text` for each "pixel".
    # Change the text's color depending on the data.
    texts = []
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
            texts.append(text)

    return texts

class GeneralEmbeddingEvaluation:
    """
    Class for evaluating embeddings and visualizing the results.

    Methods:
        __init__(): Initializes the GeneralEmbeddingEvaluation object.
        embedding_evaluation(encoder, train_loaders, names): Performs embedding evaluation using the given encoder, train loaders, and names.
        get_embeddings(encoder, loaders, names): Retrieves the embeddings from the encoder and loaders.
        vis(all_embeddings, separate_embeddings, names): Visualizes the embeddings using UMAP and PCA projections.
        centroid_similarities(embeddings, names): Calculates the pairwise similarities between the centroids of the embeddings.
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def embedding_evaluation(self, encoder, train_loaders, names):
        """
        Evaluate the embeddings generated by the encoder.

        Args:
            encoder: The encoder model used to generate the embeddings.
            train_loaders: A list of data loaders for the data.
            names: A list of names corresponding to the data loaders.

        Returns:
            None
        """
        train_all_embeddings, train_separate_embeddings = self.get_embeddings(encoder, train_loaders, names)
        self.centroid_similarities(train_separate_embeddings, names)
        # self.vis(train_all_embeddings, train_separate_embeddings, names)

    def get_embeddings(self, encoder, loaders, names):
        """
        Get embeddings for the given encoder and loaders.

        Args:
            encoder: The encoder model.
            loaders: A list of data loaders.
            names: A list of names corresponding to the loaders.

        Returns:
            A tuple containing the concatenated embeddings of all loaders and a list of separate embeddings for each loader.
        """
        encoder.eval()
        all_embeddings = None
        separate_embeddings = []
        pbar = tqdm(loaders, desc="Getting embeddings")
        for i, loader in enumerate(pbar):
            pbar.set_description(names[i])
            train_emb, train_y = get_emb_y(loader, encoder, self.device, is_rand_label=False, every=1, node_features=False)

            separate_embeddings.append(train_emb)
            if all_embeddings is None:
                all_embeddings = train_emb
            else:
                all_embeddings = np.concatenate((all_embeddings, train_emb))

        scaler = StandardScaler().fit(all_embeddings)
        for embedding in separate_embeddings:
            embedding = scaler.transform(embedding)
            embedding = normalize(embedding)

        all_embeddings = scaler.transform(all_embeddings)
        all_embeddings = normalize(all_embeddings)

        return all_embeddings, separate_embeddings

    def vis(self, all_embeddings, separate_embeddings, names):
        """
        Visualizes the embeddings using UMAP and PCA projections.

        Args:
            all_embeddings (numpy.ndarray): The combined embeddings of all graphs.
            separate_embeddings (list): A list of separate embeddings for each graph.
            names (list): A list of names corresponding to each graph.

        Returns:
            None
        """
        fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 8))

        cmap = plt.get_cmap('viridis')
        unique_categories = np.unique(names)
        colors = cmap(np.linspace(0, 1, len(unique_categories)))
        color_dict = {category: color for category, color in zip(unique_categories, colors)}

        cmap = plt.get_cmap('autumn')
        unique_categories = np.unique(names)
        colors = cmap(np.linspace(0, 1, len(unique_categories)))
        mol_color_dict = {category: color for category, color in zip(unique_categories, colors)}

        embedder = UMAP(n_components=2, n_jobs=4, n_neighbors = 30).fit(all_embeddings)

        for i, emb in enumerate(separate_embeddings):
            proj = embedder.transform(emb)
            name = names[i]
            if "ogb" in name:
                plot_marker = "^"
                color = mol_color_dict[name]
            else:
                plot_marker = "x"
                color = color_dict[name]

            ax1.scatter(proj[:, 0], proj[:, 1],
                        alpha= 1 - proj.shape[0] / all_embeddings.shape[0], s = 5,
                        label=f"{names[i]}", # - {proj.shape[0]} graphs",
                        c = color, marker = plot_marker)

        ax1.set_title("UMAP Embedding")

        embedder = PCA(n_components=2).fit(all_embeddings)


        for i, emb in enumerate(separate_embeddings):
            proj = embedder.transform(emb)
            name = names[i]
            if "ogb" in name:
                plot_marker = "^"
                color = mol_color_dict[name]
            else:
                plot_marker = "x"
                color = color_dict[name]

            ax2.scatter(proj[:, 0], proj[:, 1],
                        alpha= 1 - proj.shape[0] / all_embeddings.shape[0], s = 5,
                        c = color, marker = plot_marker)
            
                # Get the legend handles and labels

        ax2.set_title("PCA Projection")

        handles, labels = ax2.get_legend_handles_labels()



        # Create a new legend with increased size for scatter points
        new_handles = []
        for ihandle, handle in enumerate(handles):
            new_handle = plt.Line2D([0], [0],
             marker="^" if "ogb" in labels[ihandle] else "o", color='w',
               markerfacecolor=handle.get_facecolor()[0], markersize=3000)
            new_handles.append(new_handle)

        fig.legend(handles = new_handles, labels = labels,
                    bbox_transform = fig.transFigure,
                     loc='lower center',
                     ncol = 5, frameon = False, bbox_to_anchor = (0.5, 0.))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.2)
        plt.savefig("outputs/embedding.png")
        plt.close()


    def centroid_similarities(self, embeddings, names):
        """
        Calculate centroid similarities for a given set of embeddings and names.

        Parameters:
        embeddings (list of numpy arrays): List of embeddings, where each embedding is a numpy array.
        names (list of str): List of names corresponding to the embeddings.

        Returns:
        None

        This method calculates the centroid similarities for a given set of embeddings. It first calculates the centroid
        for each embedding by taking the mean along the axis 0. Then, it calculates the pairwise similarities between
        the centroids using cosine similarity. Finally, it visualizes the pairwise similarities as a heatmap and saves
        the plot as "outputs/pairwise-similarity.png".
        """
        embed_dim = embeddings[0].shape[1]
        centroids = np.zeros((len(embeddings), embed_dim))

        for i, embedding in enumerate(embeddings):
            centroids[i, :] = np.mean(embedding, axis=0)

        pairwise_similarities = cosine_similarity(centroids)
        print(pairwise_similarities)

        fig, ax = plt.subplots(figsize=(7, 6))

        im = ax.imshow(pairwise_similarities, cmap="binary", vmin=-1, vmax=1)

        ax.set_xticks(np.arange(len(names)), labels=names)
        ax.set_yticks(np.arange(len(names)), labels=names)

        annotate_heatmap(im, valfmt="{x:.3f}")

        plt.savefig("outputs/pairwise-similarity.png")

def get_top_model():
    checkpoint_url = "https://github.com/alexodavies/general-gcl/raw/main/outputs/all-100.pt"
    config_url = "https://github.com/alexodavies/general-gcl/raw/main/outputs/all-100.yaml"

    if "bgd_models" not in os.listdir():
        os.mkdir("bgd_models")
    os.chdir("bgd_models")

    if "all-100.pt" not in os.listdir():
        checkpoint = wget.download(checkpoint_url)
    if "all-100.yaml" not in os.listdir():
        config = wget.download(config_url)

    os.chdir("../")



def compute_top_scores(datasets, names):
    """
    Computes the top scores for graph structures using the ToP encoder.

    ToP scores use a pre-trained ToP model to compute the similarity between graphs across datasets.

    This function will also produce embedding visualisations using GeneralEmbeddingEvaluation.

    Args:
        datasets (list): A list of datasets containing graph structures.
        names (list): A list of names corresponding to each dataset.

    Returns:
        None
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # setup_seed(args.seed)
    get_top_model()
    checkpoint = "all-100.pt"

    checkpoint_path = f"bgd_models/{checkpoint}"
    cfg_name = checkpoint.split('.')[0] + ".yaml"
    config_path = f"bgd_models/{cfg_name}"

    with open(config_path, 'r') as stream:
        try:
            # Converts yaml document to python object
            wandb_cfg = yaml.safe_load(stream)

            # Printing dictionary
            print(wandb_cfg)
        except yaml.YAMLError as e:
            print(e)

    args = wandb_cfg

    # Get datasets
    train_loaders = [DataLoader(data, batch_size=64) for data in datasets]
    
    model = GInfoMinMax(
        Encoder(emb_dim=args["emb_dim"]["value"],
                 num_gc_layers=args["num_gc_layers"]["value"], 
                 drop_ratio=args["drop_ratio"]["value"],
                pooling_type="standard"),
        proj_hidden_dim=args["emb_dim"]["value"]).to(device)

    model_dict = torch.load(checkpoint_path, map_location=torch.device('cpu'))
    model.load_state_dict(model_dict['encoder_state_dict'])


    # Get embeddings
    general_ee = GeneralEmbeddingEvaluation()
    model.eval()

    general_ee.embedding_evaluation(model.encoder, train_loaders, names)

            
