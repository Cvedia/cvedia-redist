import sys
import time
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

from . import settings_manager
from datetime import datetime

_start = False
settings = False

def init():
	global settings, _start
	
	_start = time.time()
	settings = settings_manager.Singleton()
	signal.signal(signal.SIGINT, gracefull_shutdown)
	atexit.register(gracefull_shutdown)
	
	if settings.debug:
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
	
	if settings.register:
		try:
			if os.stat(settings.config):
				output('Warning: {} already exists, you might overwrite an existing authentication!\n'.format(settings.config))
				
				if raw_input('Proceed? [y/n] ') != 'y':
					output('Aborting')
					sys.exit(0)
		except os.error:
			output('Existing config {} doesn\'t exists'.format(settings.config))
		
		output("Registering a new client...")
		r = api_req('auth/client', method='POST')
		obj = jsonLoad(r.content)
		output('New client registration details:\n\nclient_id: {}\nclient_secret: {}\n\nVisit this url:\n{}/{}/auth/authorize?response_type=code&client_id={}&state=auth\n\nAuthorize the APP and paste the authorization code and press enter to continue.\n\n'.format(obj['client_id'], obj['client_secret'], settings.api, settings.api_version, obj['client_id']))
		
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
				'redirect_uri':'{}/account/authorize/'.format(settings.frontend)
			}
		)
		
		output('Code: {}\n\nContent: {}\n\n'.format(r.status_code, r.content))
		output('Saving config file...')
		
		obj['token'] = jsonLoad(r.content)
		obj['token']['refresh_time'] = obj['token']['expires_in'] + time.time()
		
		with open(settings.config, 'w') as outfile:
			json.dump(obj, outfile)
		
		output('Completed registration process')
		sys.exit(0)
	
	settings.config_fn = settings.config
	loadConfig()
	checkTokenValidity()

def loadConfig(config_fn=None):
	try:
		if os.stat(settings.config_fn):
			output('Loading config: {} ...'.format(settings.config_fn))
	except os.error:
		output('Config file: {} doesn\'t exists, you might want to --register this app before running'.format(settings.config_fn))
		sys.exit(1)
	
	settings.config = json.load(open(settings.config_fn, 'r'))
	bucket = False
	
	settings.def_headers = {
		'Authorization': '{} {}'.format(settings.config['token']['token_type'], settings.config['token']['access_token'])
	}

def checkTokenValidity():
	if time.time() > settings.config['token']['refresh_time']:
		output('Access token is old, forcing refresh')
		settings.refresh_token = True
	
	if settings.refresh_token:
		r = api_req(
			'auth/token',
			method='POST',
			data={
				'client_id': settings.config['client_id'],
				'client_secret': settings.config['client_secret'],
				'grant_type': 'refresh_token',
				'refresh_token': settings.config['token']['refresh_token']
			}
		)
		
		output('Result:\n{}'.format(json.dumps(jsonLoad(r.content), indent=4, sort_keys=True)))
		output('Saving config file...')
		
		settings.config['token'] = jsonLoad(r.content)
		settings.config['token']['refresh_time'] = settings.config['token']['expires_in'] + time.time()
		
		with open(settings.config_fn, 'w') as outfile:
			json.dump(settings.config, outfile)
		
		output('Token refresh succeeded!')
		settings.def_headers['Authorization'] = '{} {}'.format(settings.config['token']['token_type'], settings.config['token']['access_token'])

def output (s):
	print ('[{}] {}'.format(datetime.now().strftime("%H:%M:%S.%f"), s))

def gracefull_shutdown():
	output('Completed, wasted {}s ... BYE'.format(time.time() - _start))

def chunks(iterable, chunk_size):
	i = 0;
	while i < len(iterable):
		yield iterable[i:i+chunk_size]
		i += chunk_size

def jsonLoadFile(fn):
	if type(fn) == str:
		fh = open(fn, 'r')
		content = fh.read()
		fh.close()
	else: # assumes a file type was sent
		content = fn.read()
	
	return jsonLoad(content)

def jsonLoad(content):
	try:
		return json.loads(content.decode('utf-8'))
	except AttributeError:
		return json.loads(content('utf-8'))
	except:
		return False

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
	
	if settings.debug:
		output('Result:\n{}'.format(json.dumps(r, indent=4, sort_keys=True)))
	
	output('Uploaded: {}'.format(fn))
	
	if r['success']:
		return True
	else:
		return False

def api_req(path, method='GET', data=False, files=False, headers=False, json=False):
	if headers == False:
		try:
			headers = settings.def_headers
		except NameError:
			headers = False
	
	if method == 'GET':
		r = requests.get('{}/{}/{}'.format(settings.api, settings.api_version, path), headers=headers)
	else:
		method = method.lower()
		call_func = getattr(requests, method)
		
		if json == False and data == False and files == False:
			r = call_func('{}/{}/{}'.format(settings.api, settings.api_version, path), headers=headers)
		elif json != False:
			headers['Content-type'] = 'application/json'
			r = call_func('{}/{}/{}'.format(settings.api, settings.api_version, path), headers=headers, json=json)
		elif files == False:
			r = call_func('{}/{}/{}'.format(settings.api, settings.api_version, path), headers=headers, data=data)
		else:
			r = call_func('{}/{}/{}'.format(settings.api, settings.api_version, path), headers=headers, data=data, files=files)
	
	if r.status_code >= 500:
		try:
			raise RuntimeError('\nError {} from API\nFull reply: {}\n'.format(r.status_code, r.content))
		except:
			raise RuntimeError('\nError {} from API with NO CONTENT\n'.format(r.status_code))
	elif r.status_code >= 300:
		try:
			raise RuntimeError('\nUnexpected return code {}\nFull reply: {}\n'.format(r.status_code, r.content))
		except:
			raise RuntimeError('\nUnexpected return code {} from API with NO CONTENT\n'.format(r.status_code))
	
	if settings.debug:
		try:
			output('HTTP Code: {}\nRAW:\n\n{}\n'.format(r.status_code, r.content))
		except:
			output('HTTP Code: {}\nRAW: NO DATA\n'.format(r.status_code))
	
	return r
