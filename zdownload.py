#!/usr/bin/env python

"""
Usage:
    zdownload.py [options]

Options:
    -h, --help                      Show this help message and exit.
    -r HOURS, --recent HOURS        Run downloader for any cases with modifications in last X hours [default: 24].
    -c CASENUM, --case CASENUM      Run downloader for specific cases.
    -l LEVEL, --level LEVEL         Logging level during execution. Available options: DEBUG, INFO(default), WARNING, ERROR, CRITICAL [default: INFO]
    --config CONFIGFILE             Provide a file containing credentials and settings [default: ~/.zendesk.yml]
"""

import datetime, json, logging, os, re, requests, subprocess, sys, unicodedata, yaml
from docopt import docopt
from zendesk import Zendesk

def getCaseDirectory(case_info, path_config):
    replace_list = ['org_name', 'org_id', 'case_id']
    for string in replace_list:
        insensitive_string = re.compile(re.escape(string), re.IGNORECASE)
        path_config = insensitive_string.sub(str(case_info[string]), path_config)
    logger.debug(path_config)
    return path_config

def processTicket(ticket):
    case_info = zendesk.getCaseInfo(ticket)
    if not "error" in case_info:
        if case_info['org_name'] == "None":
            case_info['org_name'] = u"None"
        case_info['org_name'] = case_info['org_name'].replace("+","")
        case_info['org_name'] = unicodedata.normalize('NFKC', case_info['org_name']).encode('ascii', 'ignore')
        try:
            case_dir = "{}{}".format(cfg['downloader']['directory'], getCaseDirectory(case_info, cfg['downloader']['path']))
        except:
            case_dir = "{0}{1}/{2}".format(cfg['downloader']['directory'], case_info['org_name'], case_info['case_id'])
        logger.debug(case_dir)
        zendesk.downloadAttachments(ticket, case_dir)
        if run_open:
            logger.debug("running open command")
            cmd = "{0} {1}".format(open_cmd, case_dir)
            subprocess.call(cmd,shell=True)
        print "Attachments downloaded to:\n{}".format(case_dir)
    else:
        logger.error("CS#{}: {}".format(ticket, case_info['error']))

def main():
    arguments = docopt(__doc__)

    logger.setLevel(arguments['--level'])
    logger.debug(arguments)

    global cfg
    global run_open
    global open_cmd
    global zendesk

    # read in YAML configuration file
    if "~" in arguments['--config']:
        pattern = re.compile('~')
        arguments['--config'] = pattern.sub(os.path.expanduser("~"), arguments['--config'])
    if not os.path.exists(arguments['--config']):
        logger.error("Specified configuration file does not exist!")
        exit(1)
    with open(arguments['--config'], 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # determine if run_open is defined and enabled
    try:
        run_open = cfg['downloader']['run_open']
        if str(run_open).lower() == "true" or run_open == 1:
            run_open = True
        else:
            run_open = False
    except:
        run_open = False
    # determine if open_command is defined
    try:
        open_cmd = cfg['downloader']['open_command']
    except:
        if run_open:
            logger.warning("'run_open' is set, but 'open_command' doesn't exist - disabling auto open. Please configure 'open_cmd' in .zendesk.yml.")
            run_open = False

    # check directory for downloads, expand '~' and append '/' if necessary
    if "~" in cfg['downloader']['directory']:
        pattern = re.compile('~')
        cfg['downloader']['directory'] = pattern.sub(os.path.expanduser("~"), cfg['downloader']['directory'])
    if not cfg['downloader']['directory'].endswith('/'):
        cfg['downloader']['directory'] += '/'
    logger.debug("download directory: {}".format(cfg['downloader']['directory']))

    options = {}
    if 'extensions' in cfg['downloader']:
        options['extensions'] = cfg['downloader']['extensions']
    if 'exclude' in cfg['downloader']:
        options['exclude'] = cfg['downloader']['exclude']
    if 'rm_after_extract' in cfg['downloader']:
        options['rm_after_extract'] = cfg['downloader']['rm_after_extract']

    zendesk = Zendesk(cfg['credentials']['username'], cfg['credentials']['password'], cfg['credentials']['url'], options=options)

    if '{0}'.format(arguments['--case']) == 'None':
        logger.info("No case specified, downloading attachments for all cases with updates in the last {0} hours".format(arguments['--recent']))
        start_time = datetime.datetime.now() - datetime.timedelta(hours=int(arguments['--recent']))
        updated_tickets =  zendesk.getUpdatedTickets(start_time)
        logger.debug(updated_tickets)
        if not "error" in updated_tickets:
            for ticket in updated_tickets['ids']:
                processTicket(ticket)
        else:
            logger.error(updated_tickets['error'])
    else:
        ticket = arguments['--case']
        processTicket(ticket)

if __name__ == "__main__":
    # configure logger
    logging.basicConfig(level="CRITICAL", format='%(asctime)s %(filename)s:%(funcName)s - [%(levelname)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    logger = logging.getLogger()
    main()
    exit(0)
