#!/usr/bin/php
<?php

define('API_URL', 'https://api.beta.cvedia.com');
define('UI_URL', 'https://beta.cvedia.com');
define('CONFIG_PATH', basename(__FILE__).'.config');
define('TOKEN_TIMEOUT', 600); //Access token will refresh TOKEN_TIMEOUT seconds before it expired. Set it depending on the single file size you upload

if (php_sapi_name() != "cli")
	die('CLI ONLY');

$opts = getopt(
	'p:hi:t:c:b:a:l:',
	array('help', 'debug', 'relative:')
);

if (empty($opts) || isset($opts['help']) || isset($opts['h']) || !isset($opts['p']) || ((!isset($opts['i']) || empty($opts['i'])) && (!isset($opts['b']) || empty($opts['b']))) || empty($opts['p']))
	show_help();

function show_help() {
	global $opts;
	
	echo "\nUsage: " . $_SERVER['PHP_SELF'] . " -p <path>

Required options:

\t-p <path> Folder or filename to upload
\t-i <dataset name> Dataset index name

Optional:

\t-l <token> Authorization code
\t-b <bucket id> Bucket ID
\t-c <number> Number of concurrent curl requests, defaults to 16
\t-t <type> Type, defaults to `train`
\t-a <url> API URL, defaults to " . API_URL . "
\t--relative <path> Relative to be used as root, example `dataset/8bit`
\t--debug Dump all returns from api

Options got:\n" . print_r($opts, true);
	exit(0);
}

function loadFiles($path) {
	if (is_file($path))
		return array($path);
	
	$dh = opendir($path);
	$output = array();
	
	while (($file = readdir($dh)) !== false) {
		if ($file == '.' || $file == '..')
			continue;
		
		$rfile = "{$path}/{$file}";
		if (is_dir($rfile)) {
			foreach (loadFiles($rfile) as $ret)
				$output[] = $ret;
		} else {
			$output[] = $rfile;
		}
	}
	
	closedir($dh);
	
	return $output;
}

function createEmptyConfig() {
	return array(
		'client_id' => '',
		'authorization_code' => false,
		'access_token' => false
	);
}

function saveConfig($config) {
	file_put_contents(CONFIG_PATH, json_encode($config));
	return true;
}

function curlAuthRequest($is_post, $uri, $post_fields = array(), $http_headers = array()) {
	global $api;
	
	$ch = curl_init();
		
	curl_setopt_array($ch, array(
		CURLOPT_VERBOSE => false,
		CURLOPT_RETURNTRANSFER => true,
		CURLOPT_TIMEOUT => 300,
		CURLOPT_MAXREDIRS => 5,
		CURLOPT_HEADER => false,
		CURLOPT_FOLLOWLOCATION => true,
		CURLOPT_URL => $api . $uri,
		CURLOPT_POST => $is_post,
		//CURLOPT_POSTFIELDS => $post_fields,
		CURLOPT_HTTPHEADER => $http_headers
	));
	
	if (count($post_fields) > 0) 
		curl_setopt($ch, CURLOPT_POSTFIELDS, $post_fields);

	$body = curl_exec($ch); 
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE); 
    curl_close($ch); 
    
    if ($debug) {
	    echo $uri;
	    print_r($post_fields);
	    print_r($http_headers);
	    print_r($body);
	    echo $httpCode;
	}    
	
	return array(
		'body' => json_decode($body, true),
		'code' => $httpCode
	);
}

function refreshAccessToken() {
	global $api, $config, $obtain_auth_code_msg;
	
	$data = curlAuthRequest(true, '/1/auth/token', array(
				'grant_type' => 'refresh_token',
				'client_id' => $config['client_id'],
				'client_secret' => $config['client_secret'],
				'refresh_token' => $config['refresh_token']
			));

	if ($data['code'] == 200) {       	
        $config['access_token'] = $data['body']['access_token'];
        $config['refresh_token'] = $data['body']['refresh_token'];
        $config['refresh_time'] = time() + $data['body']['expires_in'];
        saveConfig($config);
	} else
		die("\nError while exchanging refresh token".$obtain_auth_code_msg);
	
}

if (!function_exists('curl_file_create')) {
	function curl_file_create($filename, $mimetype = '', $postname = '') {
		return "@$filename;filename="
			. ($postname ?: basename($filename))
			. ($mimetype ? ";type=$mimetype" : '');
	}
}


$_start = microtime(true);

if (!file_exists(CONFIG_PATH)) {
	$config = createEmptyConfig();
} else {
	$config = json_decode(file_get_contents(CONFIG_PATH), true);	
	if ($config === false) $config = createEmptyConfig();
}

$path = $opts['p'];
$authorization_code = isset($opts['l']) ? $opts['l'] : $config['authorization_code'];
$index = isset($opts['i']) ? $opts['i'] : false;;
$bucket = isset($opts['b']) ? $opts['b'] : false;
$type = isset($opts['t']) ? $opts['t'] : 'train';
$api = isset($opts['a']) ? $opts['a'] : API_URL;
$debug = isset($opts['debug']) ? true : false;
$relative = isset($opts['relative']) ? $opts['relative'] : false;
$concurrency = isset($opts['c']) ? intval($opts['c']) : 16;

if ($relative !== false && substr($relative, -1) == '/')
	$relative = substr($relative, 0, -1);
if ($concurrency <= 0)
	die("\nInvalid concurrency value.\n");
if (empty($type))
	die("\nInvalid type.\n");
if (empty($api))
	die("\nInvalid API.\n");
if (!file_exists($path))
	die("\nInvalid file/path: $path\n");
if ($bucket === false) {
	echo "\nResolving bucket for $index ...";
	$bucket = json_decode(file_get_contents($api . '/1/public/datasets/' . $index), true);

	if ($bucket === false || !isset($bucket['data']['bucket']))
		die("\nUnable to resolve bucket!\n");
	$bucket = $bucket['data']['bucket'];
	
	echo "\nUsing bucket: ".$bucket . "\n";
}

if ($config['client_id'] == '') {
	$data = curlAuthRequest(true, '/1/auth/client');

	if ($data['code'] !== 200)
		die("\nUnable to create new client, exiting.\n");

	$config['client_id'] = $data['body']['client_id'];
	$config['client_secret'] = $data['body']['client_secret'];
	saveConfig($config);
}

$obtain_auth_code_msg = "\nPlease, navigate to\n".$api."/1/auth/authorize?response_type=code&client_id=".$config['client_id']."&state=state\nto obtain Authorization code. Than call the script again with -l option and Authorization code as its value\n";

if ($authorization_code !== false) {
	
	if (($config['access_token'] === false) || ($config['authorization_code'] != $authorization_code)) {
		
		$config['authorization_code'] = $authorization_code;
		
		$data = curlAuthRequest(true, '/1/auth/token', array(
				'grant_type' => 'authorization_code',
				'client_id' => $config['client_id'],
				'client_secret' => $config['client_secret'],
				'code' => $config['authorization_code'],
				'redirect_uri' => UI_URL.'/account/authorize/'
			));

		if ($data['code'] == 200) {       	
        	$config['access_token'] = $data['body']['access_token'];
        	$config['refresh_token'] = $data['body']['refresh_token'];
        	$config['refresh_time'] = time() + $data['body']['expires_in'];
        	saveConfig($config);
		} else
			die("\nError while exchanging tokens".$obtain_auth_code_msg);
	}

	$data = curlAuthRequest(false, '/1/auth/test', array(), array(
			'Authorization: Bearer '.$config['access_token']
		));

	if ($data['code'] !== 200) //token refresh
		refreshAccessToken();
		
} else 
	die($obtain_auth_code_msg);
	
echo "\nLoading files from $path ...";
$files = loadFiles($path);
$count = count($files);
echo $count . " files found\n";

if ($count == 0)
	die("\nNothing to upload, exiting.\n");

echo "\nUploading...\n";

$errors = array();
$k = 0;
$pl = strlen($path);

foreach (array_chunk($files, $concurrency) as $bulk) {
	
	if ($config['refresh_time'] - TOKEN_TIMEOUT < time()) //let's check the token and refresh if required
		refreshAccessToken();
	
	$ch = array();
	$mh = curl_multi_init();
	
	foreach ($bulk as $i => $file) {
		$bfn = basename($file);
		$k++;
		
		$ln = round(($k / $count) * 100, 2) . '% ' . $bfn;
		echo $ln . str_repeat(' ', max(0, 80 - strlen($ln))) . "\r";
		
		$ch[$i] = curl_init();
		
		curl_setopt_array($ch[$i], array(
			CURLOPT_VERBOSE => false,
			CURLOPT_RETURNTRANSFER => true,
			CURLOPT_TIMEOUT => 300,
			CURLOPT_MAXREDIRS => 5,
			CURLOPT_HEADER => false,
			CURLOPT_FOLLOWLOCATION => true,
			# CURLOPT_URL => $api . '/1/public/upload/' . $index,
			CURLOPT_URL => $api . '/1/public/upload/' . $bucket . '/' . $type,
			CURLOPT_POST => true,
			CURLOPT_POSTFIELDS => array(
				# 'type' => $type,
				'qqfilename' => $relative === false ? $bfn : $relative . substr($file, $pl),
				'qqfile' => curl_file_create(realpath($file))
			),
			CURLOPT_HTTPHEADER => array(
				'Authorization: Bearer '.$config['access_token']
			)
		));
		
		curl_multi_add_handle($mh, $ch[$i]);
	}
	
	$active = null;
	
	do {
		usleep(1);
		$mrc = curl_multi_exec($mh, $active);
	} while ($active > 0 || $mrc == CURLM_CALL_MULTI_PERFORM);
	
	foreach ($ch as $i => $h) {
		$result = curl_multi_getcontent($ch[$i]);
		
		$httpCode = curl_getinfo($ch[$i], CURLINFO_HTTP_CODE); 
		if ($httpCode != 200) //ubnornal, but may happen if TOKEN_TIMEOUT is too low
			refreshAccessToken();
		
		if ($debug)
			echo "\nRAW OUTPUT: " . print_r($result, true) . "\n";
		
		$result = json_decode($result, true);
		
		if ($result === false || isset($result['error']))
			$errors[] = 'File: ' . $bulk[$i] . ' Error: ' . (isset($result['error']) ? print_r($result['error'], true) : 'Unknown');
		
		curl_multi_remove_handle($mh, $ch[$i]);
	}
	
	curl_multi_close($mh);
}

if (!empty($errors))
	print_r($errors);

echo "\nUploaded " . $count . " files, " . count($errors) . " errors, " . (microtime(true) - $_start) . "s wasted\n\n";
