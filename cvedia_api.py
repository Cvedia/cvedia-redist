#!/usr/bin/python

import sys
import time
import argparse
import signal
import textwrap
import types
import json
import logging
import os
import itertools
import cvedia

from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool
from cvedia import common, helpers, settings_manager

print ('CVEDIA API Tool - v2.0.0\nCopyright (c) 2017 CVEDIA B.V.\n')

parser = argparse.ArgumentParser(
	formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	description=textwrap.dedent('''\
This script perform several simple operations with cvedia api, this is intended
for experimentation and to be used as an example.

Note: API url must be in the same control domain of the FRONTEND url, otherwise
registration will fail.

''')
)

parser.add_argument('-a', '--api', default="https://api.cvedia.com", help='API URL')
parser.add_argument('-f', '--frontend', default="https://cvedia.com", help='Frontend URL')
parser.add_argument('--api_version', type=int, default=1, help='Specifies API version to use')
parser.add_argument('--register', action='store_true', help='Initiate a interactive client authorization process')
parser.add_argument('--refresh_token', action='store_true', help='Refresh token for existing registered application')

parser.add_argument('--create_dataset', default=False, help='Creates a new dataset from a json configuration file')

parser.add_argument('--datasets', action='store_true', help='List datasets')
parser.add_argument('--datasets_categories', action='store_true', help='List datasets categories')
parser.add_argument('--datasets_formats', action='store_true', help='List datasets formats')
parser.add_argument('--datasets_licenses', action='store_true', help='List datasets licenses')
parser.add_argument('--datasets_roles', action='store_true', help='List datasets roles')
parser.add_argument('--datasets_permissions', action='store_true', help='List datasets permissions')

parser.add_argument('--dataset_search', help='Searches for datasets matching name field (can be combined with --dataset_index)')

parser.add_argument('--dataset_meta', action='store_true', help='List all meta data from a single dataset')
parser.add_argument('--dataset_meta_key', help='List meta data from a single key')
parser.add_argument('--dataset_meta_upload', type=argparse.FileType('r'), help='Set dataset meta data from a file')
parser.add_argument('--dataset_meta_delete', action='store_true', help='Deletes all dataset meta data')
parser.add_argument('--dataset_meta_delete_key', help='Deletes one specific key from dataset meta data, you can specify multiple parameters , delimited')
parser.add_argument('--dataset_meta_search', help='Searches for value in meta data (can be combined with --dataset_index)')
parser.add_argument('--dataset_meta_search_key', help='Searches for value in a specific key of meta data must be combined with --dataset_meta_search for value (can be combined with --dataset_index)')

parser.add_argument('--project', help='List a project from job_id')
parser.add_argument('--projects', help='List projects from a dataset')
parser.add_argument('--projects_all', action='store_true', help='List all projects')

parser.add_argument('--export', type=argparse.FileType('r'), help='Defines a file to send for export api, can be combined with --project to define a jobid')

# generic switches

parser.add_argument('--dataset_index', help='Defines a destination dataset index for other operations')
parser.add_argument('--dataset_type', default='train', choices=['train','test','validation'], help='Defines dataset type, train, validation or test, defaulting to train')
parser.add_argument('--upload_path', nargs='*', help='Uploads a file(s) or / and folder(s) to dataset, this allows multiple types of files')
parser.add_argument('--per_page', type=int, default=25, help='Sets number of results per page')
parser.add_argument('--page', type=int, default=1, help='Defines page')
parser.add_argument('--scroll', type=str, help='Defines a scroll id for long exports')

# script options

parser.add_argument('--config', default='api-config.json', help='Defines a config file to load when doing operations other than register')
parser.add_argument('--client_id', help='Client ID')
parser.add_argument('--client_secret', help='Client Secret')
parser.add_argument('--debug', action='store_true', help='Shows debug output for http requests')
parser.add_argument('--threads', default=32, type=int, help='Defines a number of threads for parallel operations in general')

settings = cvedia.settings_manager.Singleton()
args = parser.parse_args()

for k in args.__dict__:
	settings[k] = args.__dict__[k]

cvedia.common.init()

if settings.create_dataset != False:
	try:
		if os.stat(settings.create_dataset):
			dataset_config = json.load(open(settings.create_dataset, 'r'))
			r = cvedia.common.api_req(
				'public/datasets',
				method='POST',
				json=dataset_config
			)
			
			cvedia.common.output('Dataset creation result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))
			sys.exit(0)
	except os.error:
		cvedia.common.output('Unable to load create dataset json file: {}'.format(settings.create_dataset))
		sys.exit(1)

if settings.datasets:
	cvedia.common.output('Listing datasets...')
	r = cvedia.common.api_req('public/datasets')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.datasets_categories:
	cvedia.common.output('Listing datasets categories...')
	r = cvedia.common.api_req('public/datasets/categories')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.datasets_formats:
	cvedia.common.output('Listing datasets formats...')
	r = cvedia.common.api_req('public/datasets/formats')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.datasets_licenses:
	cvedia.common.output('Listing datasets categories...')
	r = cvedia.common.api_req('public/datasets/licenses')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.datasets_roles:
	cvedia.common.output('Listing datasets roles...')
	r = cvedia.common.api_req('public/datasets/roles')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.datasets_permissions:
	cvedia.common.output('Listing datasets permissions...')
	r = cvedia.common.api_req('public/datasets/permissions')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.projects_all:
	cvedia.common.output('Listing all projects...')
	r = cvedia.common.api_req('public/projects')
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.project:
	if not settings.dataset_index:
		raise RuntimeError('You must define a --dataset_index')
	
	cvedia.common.output('Listing project {} from dataset {}...'.format(settings.project, settings.dataset_index))
	r = cvedia.common.api_req('public/datasets/{}/projects/{}'.format(settings.dataset_index, settings.project))
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.projects:
	cvedia.common.output('Listing projects from {}...'.format(settings.projects))
	r = cvedia.common.api_req('public/datasets/{}/projects'.format(settings.projects))
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_meta:
	cvedia.common.output('Listing meta for {}...'.format(settings.dataset_index))
	r = cvedia.common.api_req('public/datasets/{}/meta'.format(settings.dataset_index))
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_meta_key:
	cvedia.common.output('Listing meta key {} for {}...'.format(settings.dataset_meta_key, settings.dataset_index))
	r = cvedia.common.api_req('public/datasets/{}/meta/{}'.format(settings.dataset_index, settings.dataset_meta_key))
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_meta_upload:
	cvedia.common.output('Uploading dataset meta data for {}...'.format(settings.dataset_index))
	r = cvedia.common.api_req(
		'public/datasets/{}/meta'.format(settings.dataset_index),
		method='POST',
		json=cvedia.common.jsonLoadFile(settings.dataset_meta_upload)
	)
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_meta_delete:
	cvedia.common.output('Deleting dataset meta data for {}...'.format(settings.dataset_index))
	r = cvedia.common.api_req(
		'public/datasets/{}/meta'.format(settings.dataset_index),
		method='DELETE'
	)
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_meta_delete_key:
	cvedia.common.output('Deleting dataset meta key {} data for {}...'.format(settings.dataset_meta_delete_key, settings.dataset_index))
	r = cvedia.common.api_req(
		'public/datasets/{}/meta/{}'.format(settings.dataset_index, settings.dataset_meta_delete_key),
		method='DELETE'
	)
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.dataset_search:
	if settings.dataset_index:
		cvedia.common.output('Searching dataset {} for {}...'.format(settings.dataset_index, settings.dataset_search))
		r = cvedia.common.api_req(
			'public/datasets/search?name={}&index={}&per_page={}&page={}'.format(settings.dataset_search, settings.dataset_index, settings.per_page, settings.page),
			method='GET'
		)
	else:
		cvedia.common.output('Searching datasets for {}...'.format(settings.dataset_search))
		r = cvedia.common.api_req(
			'public/datasets/search?name={}&per_page={}&page={}'.format(settings.dataset_search, settings.per_page, settings.page),
			method='GET'
		)
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if not settings.dataset_meta_search and settings.dataset_meta_search_key:
	raise RuntimeError('You must define --dataset_meta_search')

if settings.dataset_meta_search:
	if settings.dataset_index:
		if settings.dataset_meta_search_key:
			cvedia.common.output('Searching dataset {} meta key {} for {}...'.format(settings.dataset_index, settings.dataset_meta_search_key, settings.dataset_meta_search))
			r = cvedia.common.api_req(
				'public/datasets/search?meta[{}]={}&index={}&per_page={}&page={}'.format(settings.dataset_meta_search_key, settings.dataset_meta_search, settings.dataset_index, settings.per_page, settings.page),
				method='GET'
			)
		else:
			cvedia.common.output('Searching dataset {} meta for {}...'.format(settings.dataset_index, settings.dataset_meta_search))
			r = cvedia.common.api_req(
				'public/datasets/search?meta={}&index={}&per_page={}&page={}'.format(settings.dataset_meta_search, settings.dataset_index, settings.per_page, settings.page),
				method='GET'
			)
	else:
		if settings.dataset_meta_search_key:
			cvedia.common.output('Searching dataset meta key {} for {}...'.format(settings.dataset_meta_search_key, settings.dataset_meta_search))
			r = cvedia.common.api_req(
				'public/datasets/search?meta[{}]={}&per_page={}&page={}'.format(settings.dataset_meta_search_key, settings.dataset_meta_search, settings.per_page, settings.page),
				method='GET'
			)
		else:
			cvedia.common.output('Searching dataset meta for {}...'.format(settings.dataset_meta_search))
			r = cvedia.common.api_req(
				'public/datasets/search?meta={}&per_page={}&page={}'.format(settings.dataset_meta_search, settings.per_page, settings.page),
				method='GET'
			)
		
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))

if settings.export:
	if not settings.dataset_index:
		raise RuntimeError('You must define a --dataset_index to export')
	
	extra_body = {}
	if not settings.scroll or settings.scroll == '1':
		if settings.per_page:
			per_page = settings.per_page
		else:
			per_page = 1000
		
		extra_body['limit'] = per_page
		
		if settings.page:
			page = (settings.page - 1)*per_page;
		else:
			page = 0
		
		extra_body['offset'] = page

		if settings.scroll == '1':
			extra_body['scroll'] = True	
	else:
		'''
		When you do a export without a scroll you can still get the same data, however
		if your query is too complex or you are willing to get a large number of
		entities back, it's ideal to use a scroll id, with this you will be able
		to do a full scan on the dataset without overburdening the database and getting
		results way faster.
		
		It works like this:
		
		1. You send a request with limit and offset and scroll=1; the limit will define
		how large your pages will be, this will return the first page and a scroll id.
		
		2. For the following requests you will use the scroll id returned from the
		first request, then just repeat this process, you don't need to send
		page nor limit, everytime you read the system automatically incrases that.
		
		Finally there's one caveat that scroll ids will not be open forever, they
		have a expiry limit of 30 minutes, if you don't read anything in 30 minutes
		it will go away.
		
		Running a export with offset (page) increments is possible as well.
		'''
		extra_body['scroll_id'] = settings.scroll	
	
	
	file_settings = cvedia.common.jsonLoadFile(settings.export)
	file_settings.update(extra_body)

	if settings.project:
		cvedia.common.output('Generating export of project {} for dataset {}...'.format(settings.project, settings.dataset_index))
		r = cvedia.common.api_req(
			'public/datasets/{}/exports/{}'.format(settings.dataset_index, settings.project),
			method='POST',
			json=file_settings
		)
	else:
		cvedia.common.output('Generating export for dataset {}...'.format(settings.dataset_index))
		r = cvedia.common.api_req(
			'public/datasets/{}/exports'.format(settings.dataset_index),
			method='POST',
			json=file_settings
		)
		
	#cvedia.common.output(r.content)
	
	cvedia.common.output('Result:\n{}'.format(json.dumps(cvedia.common.jsonLoad(r.content), indent=4, sort_keys=True)))
	
	if 'X-ScrollID' in r.headers:
		cvedia.common.output('Scroll ID: {}'.format(r.headers['X-ScrollID']))
		
	if 'X-ScrollDuration' in r.headers:
		cvedia.common.output('Scroll Lifetime: {}s'.format(r.headers['X-ScrollDuration']))	

if settings.upload_path:
	helpers.resolve_bucket()
	if settings.bucket == False:
		raise RuntimeError('You must set a dataset to upload to')
	
	fns = []
	i = 0
	for path in settings.upload_path:
		if os.path.isfile(path):
			fns.append(path)
			i = i + 1
		else:
			for folder, subdirs, files in os.walk(path):
				for fn in files:
					fns.append(os.path.join(folder, fn))
					i = i + 1
				for subdir in subdirs:
					settings.upload_path.append(os.path.join(folder, subdir))
	
	cvedia.common.output('Found: {} files in {} folders'.format(i, len(settings.upload_path)))
	j = 0
	success = 0
	fail = 0
	
	for cfn in chunks(fns, settings.threads):
		cvedia.common.output('[{:3.2f}% {}/{} S:{} F:{}] Uploading with {} threads...'.format(100 * (j / i), j, i, success, fail, settings.threads))
		
		pool = ThreadPool(settings.threads)
		results = pool.map(cvedia.common.upload_file_star, zip(itertools.repeat(settings.bucket + '/' + settings.dataset_type), cfn))
		pool.close()
		pool.join()
		
		for r in results:
			if r == True:
				success = success + 1
			else:
				fail = fail + 1
			
			j = j + 1
	
	cvedia.common.output('Uploaded: {} files, {} success, {} fails'.format(j, success, fail))
