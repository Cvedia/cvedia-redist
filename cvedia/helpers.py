import json
from . import common, settings_manager

settings = settings_manager.Singleton()

def resolve_bucket(index = None):
	if index == None:
		index = settings.dataset_index
	
	common.output('Resolving index {} to bucket...'.format(index))
	r = common.api_req('public/datasets/{}'.format(index))
	data = common.jsonLoad(r.content)
	common.output('Result:\n{}'.format(json.dumps(data, indent=4, sort_keys=True)))
	settings.bucket = data['data']['bucket']
