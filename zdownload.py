#!/usr/bin/env python

"""
Usage:
    download.py [options]

Options:
    -h, --help                      Show this help message and exit.
    -r HOURS, --recent HOURS        Run downloader for any cases with modifications in last X hours [default: 24].
    -c CASENUM, --case CASENUM      Run downloader for specific cases.
    -l LEVEL, --level LEVEL         Logging level during execution. Available options: DEBUG, INFO, WARNING, ERROR (default), CRITICAL [default: ERROR]
    --config CONFIGFILE             Provide a file containing credentials and settings [default: ~/.zendesk.ini]
"""

import ConfigParser, datetime, json, logging, os, re, requests, subprocess, sys
from docopt import docopt
from zendesk import Zendesk

def main():
    arguments = docopt(__doc__)

    logger.setLevel(arguments['--level'])
    logger.debug(arguments)

    config = ConfigParser.ConfigParser()
    if "~" in arguments['--config']:
        pattern = re.compile('~')
        arguments['--config'] = pattern.sub(os.path.expanduser("~"), arguments['--config'])
    if not os.path.exists(arguments['--config']):
        logger.error("Specified configuration file does not exist!")
        exit(1)
    config.read(arguments['--config'])
    user = config.get('Credentials', 'user')
    password = config.get('Credentials', 'password')
    base_url = config.get('Credentials', 'url')
    download_directory = config.get('Downloader', 'download_directory')
    try:
        run_open = config.get('Downloader', 'run_open')
        if run_open == "True" or run_open == "true" or run_open == "1":
                run_open = True
        else:
            run_open = False
    except:
        run_open = False
    try:
        open_cmd = config.get('Downloader', 'open_cmd')
    except:
        if run_open:
            logger.warning("'run_open' is set, but 'open_cmd' doesn't exist - disabling auto open. Please configure 'open_cmd' in .zendesk.ini.")
            run_open = False
    if "~" in download_directory:
        pattern = re.compile('~')
        download_directory = pattern.sub(os.path.expanduser("~"), download_directory)
    if not download_directory.endswith('/'):
        download_directory += '/'
    logger.debug("download_directory: {}".format(download_directory))

    zendesk = Zendesk(user, password, base_url)

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
                logger.error("{}".format(case_info['error']))
    else:
        ticket = arguments['--case']
        case_info = zendesk.getCaseInfo(ticket)
        case_info['org_name'] = case_info['org_name'].replace("+","")
        if not "error" in case_info:
            case_dir = "{0}{1}_{2}_{3}".format(download_directory, case_info['id'], case_info['org_name'], case_info['org_id'])
            zendesk.downloadAttachments(ticket, case_dir)
        else:
            logger.error("CS#{}: {}".format(ticket, case_info['error']))
    print "Attachments downloaded to: {}".format(case_dir)

    if run_open:
        cmd = "{0} {1}".format(open_cmd, case_dir)
        subprocess.call(cmd,shell=True)

if __name__ == "__main__":
    # configure logger
    logging.basicConfig(level="CRITICAL", format='%(asctime)s %(filename)s:%(funcName)s - [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    logger = logging.getLogger()
    main()
    exit(0)
