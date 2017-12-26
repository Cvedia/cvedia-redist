# Documentation

Full documentation of CVEDIA API is available on https://docs.cvedia.com
To see all options cvedia_api.py provides, run `python cvedia_api.py --help`

# Quick Start

1. Register the app: `python cvedia_api.py --register`
2. Create a dataset: `python cvedia_api.py --create_dataset examples/create_dataset.json` -- You might have an error if the name already exists
3. Upload images to dataset: `python cvedia_api.py --dataset_index <index name> --upload examples/image.json`
4. Upload annotations to the image: `python cvedia_api.py --dataset_index <index name> --upload examples/annotation.json`
5. Bind custom arbitrary values to a image entity: `python cvedia_api.py --dataset_index <index name> --upload examples/image_custom_meta.json`
   - Query arbitrary values for exporting: `python cvedia_api.py --dataset_index <index name> --export examples/export_custom_mql.json`
6. Replace an existing image with a different one: `python cvedia_api.py --dataset_index <index name> --upload examples/image_replace.json`
7. Output cifar-10 dataset with augmentations and filters: `python cvedia_api.py --dataset_index cifar-10 --export examples/export_cifar_mql.json`

# What is this

This is a collection of tools that shows the API functionality of CVEDIA API.

# How to install

You can test either in python or php.

### Linux install

On a ubuntu system you probably already have
that installed, to make sure just run:

`apt-get install python -y`

### Windows install

Download python 2.7 (python 3 would also work) here:

`https://www.python.org/ftp/python/2.7/python-2.7.amd64.msi`

# Running

python cvedia_api.py --help

Shows all possible options.

Before using this you need to register an app, otherwise you won't be able to
access your private content, for that you can run:

`python cvedia_api.py --register`

This will show a set of instructions you will need to follow in order to register
the app and be able to authenticate it. This process only needs to happen once
as after the app is registered it will save a configuration file with the tokens.

Note that by registering an app you will allow it to access all your user data
on cvedia, including private datasets.

## Examples

`python cvedia_api.py --datasets`

Lists all datasets from the system plus the ones you own / have access to

`python cvedia_api.py --projects mydataset-hrao`

Lists all projects from mydataset-hrao

`python cvedia_api.py --dataset_index mydataset-hrao --dataset_type train --upload /storage/path/to/dataset /storage/path/to/dataset2 --threads 64`

Will recusevely upload all the files from folders /storage/path/to/dataset /storage/path/to/dataset2
in 64 threads to dataset index mydataset-hrao on type `train`

## Note

Dataset `name` is different from dataset `index`, usually api commands only use
`index`, name only used on the frontend. You should be able to find the name
using the dataset list function.
