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

A .yml file will need to be created with credential, url, and download directory information. By default the script will look for this file at `~/.zendesk.yml`. To specify a configuration file in a different location, use the `--config` argument. Example **.zendesk.yml** contents:
```
credentials:
  username: user@company.com
  password: password
  url: https://company.zendesk.com

downloader:
  directory: ~/zendesk/
  path: org_name_org_id/case_id
  run_open = true
  open_command = atom
```

## Configuration Options
Configuration | Value | Required?
------------- | ----- | ---------
username | Zendesk username | yes
password | Zendesk password | yes
url | Zendesk URL | yes
directory | Base directory path for downloads | yes
path | Customizable path inside base directory | no, default is <org_name\>/\<case_id\>
run_open | Run the open command after downloading and extracting | no, default is False
open_command | Command to run if run_open is True | no

The path can be customized using the following variables:
Name | Description
---- | -----------
case_id | Case number
org_name | Name of organization
ord_id | Organization's unique identifier from Zendesk

_**NOTE:**_ It is recommended to use a token based authentication to Zendesk, and not store the user's password in plain text. See [this page](https://support.zendesk.com/hc/en-us/articles/226022787-Generating-a-new-API-token-) for information on generating API tokens. If using token based authentication, the username will be `user@company.com/token`.


## Known Issues
```
AttributeError: 'X509' object has no attribute '_x509'
```
This has been seen when the pyOpenSSL library needed updating:
```pip install pyOpenSSL --upgrade```
