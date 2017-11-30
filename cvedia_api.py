#!/usr/bin/python

import sys
import telnetlib
import time
import atexit
import argparse
import random
import signal
import textwrap
import atexit
import types
import json
import requests
import logging
import os
import itertools

from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool

def output (s):
	print ('[{}] {}'.format(datetime.now().strftime("%H:%M:%S.%f"), s))

def gracefull_shutdown():
	output('Completed, wasted {}s ... BYE'.format(time.time() - _start))

def chunks(iterable, chunk_size):
	i = 0;
	while i < len(iterable):
		yield iterable[i:i+chunk_size]
		i += chunk_size

def jsonLoad(content):
	try:
		return json.loads(content.decode('utf-8'))
	except AttributeError:
		return json.loads(content('utf-8'))

def upload_file_star(args):
	return upload_file(*args)

def upload_file(req_path, fn):
	r = api_req(
		'public/upload/{}'.format(req_path),
		method='POST',
		data={
			'qqfilename': os.path.basename(fn)
		},
		files={
			'qqfile': open(fn, 'rb')
		}
	)
	r = jsonLoad(r.content)
	
	if debug:
		output('Result:\n{}'.format(json.dumps(r, indent=4, sort_keys=True)))
	
	output('Uploaded: {}'.format(fn))
	
	if r['success']:
		return True
	else:
		return False

def api_req(path, method='GET', data=False, files=False, headers=False, json=False):
	if headers == False:
		try:
			headers = def_headers
		except NameError:
			headers = False
	
	if method == 'GET':
		r = requests.get('{}/{}/{}'.format(api, api_version, path), headers=headers)
	elif method == 'POST':
		if json != False:
			headers['Content-type'] = 'application/json'
			r = requests.post('{}/{}/{}'.format(api, api_version, path), headers=headers, json=json)
		elif files == False:
			r = requests.post('{}/{}/{}'.format(api, api_version, path), headers=headers, data=data)
		else:
			r = requests.post('{}/{}/{}'.format(api, api_version, path), headers=headers, data=data, files=files)
	
	if r.status_code >= 300:
		raise RuntimeError('Unexpected return code {}\nFull reply: {}\n'.format(r.status_code, r.content))
	
	if debug:
		output('HTTP Code: {}\nRAW:\n\n{}\n'.format(r.status_code, r.content))
	
	return r

# MAIN #########################################################################

print ('CVEDIA API Tool - v1.1.0\nCopyright (c) 2017 CVEDIA B.V.\n')

parser = argparse.ArgumentParser(
	formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	description=textwrap.dedent('''\
This script perform several simple operations with cvedia api, this is intended
for experimentation and to be used as an example.
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

parser.add_argument('--project', help='List a project from job_id')
parser.add_argument('--projects', help='List projects from a dataset')
parser.add_argument('--projects_all', action='store_true', help='List all projects')

parser.add_argument('--dataset_index', help='Defines a destination dataset index for other operations')
parser.add_argument('--dataset_type', default='train', choices=['train','test','validation'], help='Defines dataset type, train, validation or test, defaulting to train')
parser.add_argument('--upload_path', nargs='*', help='Uploads a file(s) or / and folder(s) to dataset, this allows multiple types of files')

parser.add_argument('--config', default='api-config.json', help='Defines a config file to load when doing operations other than register')
parser.add_argument('--client_id', help='Client ID')
parser.add_argument('--client_secret', help='Client Secret')
parser.add_argument('--debug', action='store_true', help='Shows debug output for http requests')
parser.add_argument('--threads', default=32, type=int, help='Defines a number of threads for parallel operations in general')

args = parser.parse_args()

for k in args.__dict__:
	globals()[k] = args.__dict__[k]

_start = time.time()
signal.signal(signal.SIGINT, gracefull_shutdown)
atexit.register(gracefull_shutdown)

if debug:
	output('Enabling http debug mode')
	try:
		import http.client as http_client
	except ImportError:
		# Python 2
		import httplib as http_client
	
	http_client.HTTPConnection.debuglevel = 1
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	requests_log = logging.getLogger("requests.packages.urllib3")
	requests_log.setLevel(logging.DEBUG)
	requests_log.propagate = True

# SPECIAL METHODS ##############################################################

if register:
	try:
		if os.stat(config):
			output('Warning: {} already exists, you might overwrite an existing authentication!\n'.format(config))
			
			if raw_input('Proceed? [y/n] ') != 'y':
				output('Aborting')
				sys.exit(0)
	except os.error:
		output('Existing config {} doesn\'t exists'.format(config))
	
	output("Registering a new client...")
	r = api_req('auth/client', method='POST')
	obj = jsonLoad(r.content)
	output('New client registration details:\n\nclient_id: {}\nclient_secret: {}\n\nVisit this url:\n{}/{}/auth/authorize?response_type=code&client_id={}&state=auth\n\nAuthorize the APP and paste the authorization code and press enter to continue.\n\n'.format(obj['client_id'], obj['client_secret'], api, api_version, obj['client_id']))
	
	obj['auth_code'] = raw_input('Code: ')
	obj['auth_code'] = obj['auth_code'].strip()
	
	output('\nRequesting authorization...')
	
	r = api_req(
		'auth/token',
		method='POST',
		data={
			'client_id': obj['client_id'],
			'client_secret': obj['client_secret'],
			'grant_type': 'authorization_code',
			'code': obj['auth_code'],
			'redirect_uri':'{}/account/authorize/'.format(frontend)
		}
	)
	
	output('Code: {}\n\nContent: {}\n\n'.format(r.status_code, r.content))
	output('Saving config file...')
	
	obj['token'] = jsonLoad(r.content)
	obj['token']['refresh_time'] = obj['token']['expires_in'] + time.time()
	
	with open(config, 'w') as outfile:
		json.dump(obj, outfile)
	
	output('Completed registration process')
	sys.exit(0)

# ALL OTHER APIS ###############################################################

config_fn = config

try:
	if os.stat(config_fn):
		output('Loading config: {} ...'.format(config_fn))
except os.error:
	output('Config file: {} doesn\'t exists, you might want to --register this app before running'.format(config_fn))
	sys.exit(1)

config = json.load(open(config_fn, 'r'))
bucket = False

def_headers = {
	'Authorization': '{} {}'.format(config['token']['token_type'], config['token']['access_token'])
}

# check if current token still valid
if time.time() > config['token']['refresh_time']:
	output('Access token is old, forcing refresh')
	refresh_token = True

if refresh_token:
	r = api_req(
		'auth/token',
		method='POST',
		data={
			'client_id': config['client_id'],
			'client_secret': config['client_secret'],
			'grant_type': 'refresh_token',
			'refresh_token': config['token']['refresh_token']
		}
	)
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))
	
	output('Saving config file...')
	
	config['token'] = jsonLoad(r.content)
	config['token']['refresh_time'] = config['token']['expires_in'] + time.time()
	
	with open(config_fn, 'w') as outfile:
		json.dump(config, outfile)
	
	output('Token refresh succeeded!')
	def_headers['Authorization'] = '{} {}'.format(config['token']['token_type'], config['token']['access_token'])

if create_dataset != False:
	try:
		if os.stat(create_dataset):
			dataset_config = json.load(open(create_dataset, 'r'))
			r = api_req(
				'public/datasets',
				method='POST',
				json=dataset_config
			)
			
			output('Dataset creation result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))
			sys.exit(0)
	except os.error:
		output('Unable to load create dataset json file: {}'.format(create_dataset))
		sys.exit(1)

if datasets:
	output('Listing datasets...')
	r = api_req('public/datasets')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if datasets_categories:
	output('Listing datasets categories...')
	r = api_req('public/datasets/categories')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if datasets_formats:
	output('Listing datasets formats...')
	r = api_req('public/datasets/formats')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if datasets_licenses:
	output('Listing datasets categories...')
	r = api_req('public/datasets/licenses')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if datasets_roles:
	output('Listing datasets roles...')
	r = api_req('public/datasets/roles')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if datasets_permissions:
	output('Listing datasets permissions...')
	r = api_req('public/datasets/permissions')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if projects_all:
	output('Listing all projects...')
	r = api_req('public/projects')
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if project:
	output('Listing project {}...'.format(project))
	r = api_req('public/projects/{}'.format(project))
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if projects:
	output('Listing projects from {}...'.format(projects))
	r = api_req('public/datasets/{}/projects'.format(projects))
	
	output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))

if dataset_index:
	output('Resolving index {} to bucket...'.format(dataset_index))
	r = api_req('public/datasets/{}'.format(dataset_index))
	data = jsonLoad(r.content)
	output('Result:\n{}'.format(json.dumps(data, indent=4, sort_keys=True)))
	bucket = data['data']['bucket']
	output('Resolved bucket for dataset: {} to {}'.format(dataset_index, bucket))

if upload_path:
	if bucket == False:
		raise RuntimeError('You must set a dataset to upload to')
	
	fns = []
	i = 0
	for path in upload_path:
		if os.path.isfile(path):
			fns.append(path)
			i = i + 1
		else:
			for folder, subdirs, files in os.walk(path):
				for fn in files:
					fns.append(os.path.join(path, fn))
					i = i + 1
				for subdir in subdirs:
					upload_path.append(os.path.join(path, subdir))
	
	output('Found: {} files in {} folders'.format(i, len(upload_path)))
	j = 0
	success = 0
	fail = 0
	
	for cfn in chunks(fns, threads):
		output('[{:3.2f}% {}/{} S:{} F:{}] Uploading with {} threads...'.format(100 * (j / i), j, i, success, fail, threads))
		
		pool = ThreadPool(threads)
		results = pool.map(upload_file_star, zip(itertools.repeat(bucket + '/' + dataset_type), cfn))
		pool.close()
		pool.join()
		
		for r in results:
			if r == True:
				success = success + 1
			else:
				fail = fail + 1
			
			j = j + 1
	
	output('Uploaded: {} files, {} success, {} fails'.format(j, success, fail))
