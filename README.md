# zendesk-downloader
Download attachments associated with cases in Zendesk

## Pre-reqs
 - pip via brew (OSX) or another method
 - requests - ```pip install requests```
 - docopts - ```pip install docopt```

## Usage
```
Usage:
    download.py [options]

Options:
    -h, --help                      Show this help message and exit.
    -r HOURS, --recent HOURS        Run downloader for any cases with modifications in last X hours [default: 24].
    -c CASENUM, --case CASENUM      Run downloader for specific cases.
    --config CONFIGFILE             Provide a file containing credentials and settings [default: ~/.zendesk.ini]
```

A .ini file will need to be created with credential, url, and download_directory information, by default the script will look for this file at `~/.zendesk.ini`. To specify a configuration file in a different location, use `--config` argument. Example **.zendesk.ini** contents:
```
[Credentials]
user = user@company.com
password = password
url = https://company.zendesk.com

[Downloader]
download_directory = ~/Zendesk/
```
