#!/usr/bin/env python2

"""
Usage:
    download.py [options]

Options:
    -h, --help                      Show this help message and exit.
    -r HOURS, --recent HOURS        Run downloader for any cases with modifications in last X hours [default: 24].
    -c CASENUM, --case CASENUM      Run downloader for specific cases.
    --config CONFIGFILE             Provide a file containing credentials and settings [default: ~/.zendesk.ini]
"""

import ConfigParser, datetime, json, os, re, requests, subprocess, sys
from docopt import docopt
import pprint

def splitext(path):
    #for ext in ['.tar.xz']:
    ext = '.tar.xz'
    if path.endswith(ext):
        path, ext = path[:-len(ext)], path[-len(ext):]
    #    break
    else:
    	path, ext = os.path.splitext(path)
	if ext == "":
		ext = ".txt"
    return path, ext[1:]

def get_updated_tickets(base_url, user, password, start_time):
	ticket_list = []
	url = "{0}/api/v2/incremental/tickets.json?start_time={1}".format(base_url, start_time.strftime("%s"))
	#result = zenpy.tickets.incremental(start_time=start_time)
	result = requests.get(url, auth=(user, password)).json()
	for ticket in result['tickets']:
		ticket_list.append(ticket['id'])
	return ticket_list

def get_case_info(base_url, user, password, ticket_id):
	case_info = {}
	url = "{0}/api/v2/tickets/{1}.json".format(base_url, ticket_id)
	result = requests.get(url, auth=(user, password)).json()
	if "error" in result:
		case_info['error'] = result['error']
	else:
		case_info['id'] = result['ticket']['id']
		case_info['org_id'] = result['ticket']['organization_id']

		if case_info['org_id'] != "None":
			url = "{0}/api/v2/organizations/{1}.json".format(base_url, case_info['org_id'])
			result = requests.get(url, auth=(user, password)).json()
			if "error" in result:
				case_info['org_name'] = "None"
			else:
				org_name = result['organization']['name']
				# TODO: replace search and replace with regex pattern replace
				#pattern = re.compile['[ .,()\{\}[]!@#$%^&+*=~<>?]']
				#org_name = pattern.sub('', result['organization']['name'])
				for ch in [' ','.',',','(',')','!','@','#','$','%','^','&','*',';',':','?','<','>','=','{','}','[',']','/']:
					if ch in org_name:
						org_name=org_name.replace(ch,"")
				case_info['org_name'] = org_name
	return case_info

def get_attachment_list(base_url, user, password, ticket_id):
	attachment_list = []
	url = "{0}/api/v2/tickets/{1}/comments.json".format(base_url, ticket_id)
	result = requests.get(url, auth=(user, password)).json()
	for comment in result['comments']:
		if comment['attachments']:
			key = 0
			for item in comment['attachments']:
				attachment = {}
				attachment['id'] = comment['attachments'][key]['id']
				attachment['name'] = comment['attachments'][key]['file_name']
				attachment['url'] = comment['attachments'][key]['content_url']
				attachment_list.append(attachment.copy())
				key+=1
	return attachment_list

def download_file(attachment, directory="."):
	pattern = re.compile('[^\w.-]+')
	attachment['name'] = pattern.sub('', attachment['name'])
	filename, file_extension = splitext(attachment['name'])
	if "." in filename:
	    local_filename = "{0}_{1}.{2}.{3}".format(filename.split(".", 1)[0], attachment['id'], filename.split(".", 1)[1], file_extension)
	else:
		local_filename = "{0}_{1}.{2}".format(filename.split(".", 1)[0], attachment['id'], file_extension)
	print "    {0}".format(local_filename)
	if not os.path.exists("{0}/{1}".format(directory, local_filename)):
		print "        Downloading..."
		if not os.path.exists(directory):
			os.makedirs(directory)
			os.chmod(directory,0o775)
	    # NOTE the stream=True parameter
		r = requests.get(attachment['url'], stream=True)
		with open("{0}/{1}".format(directory, local_filename), 'wb') as f:
			for chunk in r.iter_content(chunk_size=1024):
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
	else:
		print "        Already downloaded"
	return local_filename

def extract_file(attachment, directory="."):
	filename, file_extension = splitext(attachment['name'])
	if "cl_support" in filename and file_extension == "tar.xz":
		if not os.path.exists("{0}/{1}".format(directory, filename)):
			print "        Extracting..."
			local_filename = "{0}_{1}.{2}".format(attachment['name'].split(".", 1)[0], attachment['id'], attachment['name'].split(".", 1)[-1])
			cmd = "tar xf {0}/{1} -C {2}".format(directory, local_filename, directory)
			subprocess.call(cmd,shell=True)
		else:
			print "        Already extracted"
	else:
		print "        Not a cl_support, will not extract"

def download_attachments(base_url, user, password, ticket_id, directory):
	print "CS#{0}".format(ticket_id)
	attachment_list = get_attachment_list(base_url, user, password, ticket_id)
	if attachment_list:
		for attachment in attachment_list:
			download_file(attachment, directory)
			extract_file(attachment, directory)

if __name__ == "__main__":
	arguments = docopt(__doc__)

	config = ConfigParser.ConfigParser()
	if "~" in arguments['--config']:
		pattern = re.compile('~')
		arguments['--config'] = pattern.sub(os.path.expanduser("~"), arguments['--config'])
	if not os.path.exists(arguments['--config']):
		print "Error: Specified configuration file does not exist!"
		exit(1)
	config.read(arguments['--config'])
	user = config.get('Credentials', 'user')
	password = config.get('Credentials', 'password')
	base_url = config.get('Credentials', 'url')
	download_directory = config.get('Downloader', 'download_directory')
	if "~" in download_directory:
		pattern = re.compile('~')
		download_directory = pattern.sub(os.path.expanduser("~"), download_directory)

	if '{0}'.format(arguments['--case']) == 'None':
		print "No case specified, downloading attachments for all cases with updates in the last {0} hours".format(arguments['--recent'])
		start_time = datetime.datetime.now() - datetime.timedelta(hours=int(arguments['--recent']))
		updated_tickets =  get_updated_tickets(base_url, user, password, start_time)
		for ticket in updated_tickets:
			case_info = get_case_info(base_url, user, password, ticket)
			if not "error" in case_info:
				case_dir = "{0}{1}_{2}_{3}".format(download_directory, case_info['id'], case_info['org_name'], case_info['org_id'])
				download_attachments(base_url, user, password, ticket, case_dir)
			else:
				print "    ERROR: {0}".format(case_info['error'])
	else:
		ticket = arguments['--case']
		case_info = get_case_info(base_url, user, password, ticket)
		if not "error" in case_info:
			case_dir = "{0}{1}_{2}_{3}".format(download_directory, case_info['id'], case_info['org_name'], case_info['org_id'])
			download_attachments(base_url, user, password, ticket, case_dir)
		else:
			print "CS#{0} -- ERROR: {1}".format(ticket, case_info['error'])
	print case_dir
	exit(0)
