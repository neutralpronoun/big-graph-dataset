.. _get-started:

Welcome to the project! We're excited to have you on board.
We'll be collaborating through GitHub, with everyone working in their own branch.

There are a few rules for the datasets, demonstrated in ``bgd/real/example_dataset.py``:
 - Please cite your sources for data in documentation - see the existing datasets for examples
 - Where possible start from existing datasets that have been used in-literature (to avoid ethics paperwork)
 - If using generators, use generators that are well-understood (for example Erdos-Renyi graphs)
 - The datasets need at least a train/val/test split
 - Datasets should be many small (less than 400 node) graphs
 - Ideally the number of graphs in each dataset should be controllable
 - Data should be downloaded in-code to keep the repo small. If this isn't possible let me know.


Set Up & Contributing
=====================

1. Clone the Repository
------------------------

Open your terminal and run the following command to clone the main repository::

    git clone https://github.com/alexodavies/big-graph-dataset.git

2. Navigate to the repository directory:
------------------------------------------

    cd big-graph-dataset

3. Create a new branch: 
------------------------

    git checkout -b your-name

Replace ``your-name`` with your name or a  descriptive name for your data.

3. Work your magic:
--------------------------

 - Copy ``bgd/real/example_dataset.py`` into the relevant sub-directory (``bgd/real/``, ``bgd/synthetic/`` depending on your data)
 - Re-tool it for your data (``NAME_dataset.py`` or something similar)
 - Add your dataset to relevant ``__init__.py`` files (``bgd/X/__init__.py`` and ``bgd/__init__.py``)

4. Stage your changes: 
-----------------------

Add the files you modified or created to the staging area::

    git add NAME_dataset.py

5. Commit your changes: 
------------------------

Commit your changes with a descriptive message::

    git commit -m "A very detailed and useful commit message that everyone likes to read."

6. Push Your Branch to GitHub
-----------------------------
Push your branch to the main repository on GitHub::

    git push origin your-name

7. Create a Pull Request
------------------------
   - Go to the repository on `GitHub <https://github.com/alexodavies/big-graph-dataset.git>`. 
   - Click on the "Pull Requests" tab.
   - Click the "New pull request" button.
   - Select the branch you just pushed from the "compare" drop-down menu.
   - Provide a title and description for your pull request.
   - Click "Create pull request".

8. Merge the pull request: 
--------------------------
After your code is reviewed, the pull request will be merged into the main branch by the project maintainer (`Alex O. Davies <alexander.davies@bristol.ac.uk>`).

Summary of Git Commands
-----------------------
::

    # Clone the repository
    git clone https://github.com/alexodavies/big-graph-dataset.git
    cd big-graph-dataset

    # Create a new branch
    git checkout -b your-name

    # Make changes, stage, and commit
    git add NAME_dataset.py
    git commit -m "Add detailed description of changes"

    # Push your branch to GitHub
    git push origin your-name


Python Environments
===================

**Please use Python 3.11.X**

A *generic* environment is under `requirements_dev.txt`, use `pip install -r requirements_dev. txt` within a virtual (Conda etc.) environment to get everything installed::


    conda create -n big-graph-dataset python=3.11 numpy<=2.0.0 pytorch<=2.4.1 -c pytorch
    conda activate big-graph-dataset
    pip install -r requirements_dev.txt


.. Alternatively my MacOS environment, with specific versioning, is under `requirements_macos.txt`, install with `pip install -r requirements_macos. txt`.

There is also a packaged conda environment in `environment.yml` - you can run `conda env create -f enviroment.yml` to try this instead of the pip installs.

If this doesn't work, create and activate a new environment (here with Conda)::


    conda create -n big-graph-dataset python=3.11 numpy=1.26.4 pytorch=2.4.1
    conda activate big-graph-dataset


then these commands should install (most of) the relevant libraries::


    pip install torch torchvision torchaudio 
    pip install torch_geometric torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.4.0+cpu.html
    pip install matplotlib pandas wget umap-learn



**Enviroment Issues**

 - The packaged enviroment uses CPU versions of PyTorch and PyTorch Geometric. If you have a GPU, you can install the GPU versions by changing the `torch` and `torch_geometric` lines in `requirements_dev.txt` to the GPU versions from the PyTorch website.
 - Some packages don't play well with others. If you have significant issues, please get in touch.
 - I sometimes run into a `OSError: [Errno 66] Directory not empty` error during `pip install -r requirements_dev. txt` from littleballoffur - this is a `numpy` versioning issue, try `pip install numpy==1.26.4`.
 - `torch_sparse` can take a long time to install
 - **If your code requires new package installs please tell me** (email, but this can also be detailed in the pull request)

Testing Code
============

In your ``if __name == `__main__`` section you can use some prepared code::

    from ..utils import describe_one_dataset, vis_grid

    ... rest of your code ...

    if __name__ == "__main__":
        # Please set the last part of the path to your dataset name!
        dataset = NAMEDataset(os.getcwd()+'/bgd_files/'+'NAME', stage = "train")
        describe_one_dataset(dataset)
        vis_grid(dataset[:16], os.getcwd()+"/bgd_files/NAME/train.png")

        # Option to instead show the plot in GUI
        vis_grid(dataset[:16], os.getcwd()+"/bgd_files/NAME/train.png", show_plot = True)

You'd run this from the root ``big-graph-dataset`` with::

    python -m bgd.(real/synthetic).NAME_dataset

assuming that you've added your dataset to the relevant ``__init__.py`` files.

**Please don't make changes to any other files!**


Feel free to reach out if you have any questions or need further assistance. Happy coding!

**Citing**

.. code-block:: bibtex

   @misc{big-graph-dataset,
   title = {{Big Graph Dataset} Documentation},
   howpublished = {https://big-graph-dataset.readthedocs.io/}}
