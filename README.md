# What is this?

This is a tool that shows the API functionality of CVEDIA API.

# How to install?

This script requires python

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
