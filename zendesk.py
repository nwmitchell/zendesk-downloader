import inspect, logging, os, re, requests, subprocess
from pprint import pprint

class Zendesk:
    def __init__(self, username, password, baseurl):
        self.username = username
        self.password = password
        self.baseurl = baseurl
        self.logger = logging.getLogger()

    def getState(self, ticket_id):
        url = "{0}/api/v2/tickets/{1}.json".format(self.baseurl, caseid)
        self.logger.debug(url)
        status = requests.get(url, auth=(self.username, self.password)).json()["ticket"]["status"]
        self.logger.debug("case state: {}".format(status))
        return status

    def getCaseInfo(self, ticket_id):
        case_info = {}
        url = "{0}/api/v2/tickets/{1}.json".format(self.baseurl, ticket_id)
        result = requests.get(url, auth=(self.username, self.password)).json()
        if "error" in result:
            case_info['error'] = result['error']
        else:
            case_info['case_id'] = result['ticket']['id']
            case_info['org_id'] = result['ticket']['organization_id']

            if case_info['org_id'] != "None":
                url = "{0}/api/v2/organizations/{1}.json".format(self.baseurl, case_info['org_id'])
                result = requests.get(url, auth=(self.username, self.password)).json()
                if "error" in result:
                    case_info['org_name'] = "None"
                else:
                    org_name = result['organization']['name']
                    #print org_name
                    # TODO: replace search and replace with regex pattern replace
                    #pattern = re.compile['[ .,()\{\}[]!@#$%^&+*=~<>?]']
                    #org_name = pattern.sub('', result['organization']['name'])
                    for ch in [' ','.',',','(',')','!','@','#','$','%','^','&','*',';',':','?','<','>','=','{','}','[',']','/']:
                        if ch in org_name:
                            org_name=org_name.replace(ch,"")
                    case_info['org_name'] = org_name
        return case_info

    def getAttachmentList(self, ticket_id):
        attachment_list = []
        url = "{0}/api/v2/tickets/{1}/comments.json".format(self.baseurl, ticket_id)
        result = requests.get(url, auth=(self.username, self.password)).json()
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

    def getUpdatedTickets(self, start_time):
        ticket_list = {}
        url = "{0}/api/v2/incremental/tickets.json?start_time={1}".format(self.baseurl, start_time.strftime("%s"))
        result = requests.get(url, auth=(self.username, self.password)).json()
        if "error" in result:
            ticket_list['error'] = result['error']
        else:
            ticket_list['ids'] = []
            for ticket in result['tickets']:
                ticket_list['ids'].append(ticket['id'])
        return ticket_list

    def downloadAttachments(self, ticket_id, directory):
        self.logger.info("CS#{0}".format(ticket_id))
        attachment_list = self.getAttachmentList(ticket_id)
        if attachment_list:
            for attachment in attachment_list:
                self.__downloadFile(attachment, directory)
                self.__extractFile(attachment, directory)

    def getSolveClassification(self, ticket_id):
        url = "{0}/api/v2/tickets/{1}.json".format(self.baseurl, caseid)
        self.logger.debug(url)
        result = requests.get(url, auth=(self.username, self.password)).json()
        return filter(lambda field: field['id'] == 30052568, result["ticket"]["fields"])[0]["value"]

    def getStateAndBuckets(self, ticket_id):
        # Bucket : 24016816
        # Optic/Cable/NIC 1 : 45399648
        # Bucket II : 26909388
        # Optic/Cable/NIC 2 : 45399668
        url = "{0}/api/v2/tickets/{1}.json".format(self.baseurl, caseid)
        self.logger.debug(url)
        result = requests.get(url, auth=(self.username, self.password)).json()
        casedata = {}
        casedata["status"] = result["ticket"]["status"]
        buckets = []
        b1 = {}
        b2 = {}
        b1["bucket"] = filter(lambda field: field['id'] == 24016816, result["ticket"]["fields"])[0]["value"]
        b1["optic"] = filter(lambda field: field['id'] == 45399648, result["ticket"]["fields"])[0]["value"]
        buckets.append(b1)
        b2["bucket"] = filter(lambda field: field['id'] == 26909388, result["ticket"]["fields"])[0]["value"]
        b2["optic"] = filter(lambda field: field['id'] == 45399668, result["ticket"]["fields"])[0]["value"]
        buckets.append(b2)
        casedata["buckets"] = buckets
        self.logger.debug(casedata)
        return casedata

    # Private Functions
    def __downloadFile(self, attachment, directory="."):
        pattern = re.compile('[^\w.-]+')
        attachment['name'] = pattern.sub('', attachment['name'])
        filename, file_extension = self.__splitext(attachment['name'])
        if "." in filename:
            local_filename = "{0}_{1}.{2}.{3}".format(filename.split(".", 1)[0], attachment['id'], filename.split(".", 1)[1], file_extension)
        else:
            local_filename = "{0}_{1}.{2}".format(filename.split(".", 1)[0], attachment['id'], file_extension)
        self.logger.info("{}".format(local_filename))
        if not os.path.exists("{0}/{1}".format(directory, local_filename)):
            self.logger.info("Downloading...")
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
            self.logger.info("Already downloaded")
        return local_filename

    def __extractFile(self, attachment, directory="."):
        filename, file_extension = self.__splitext(attachment['name'])
        if "cl_support" in filename and file_extension == "tar.xz":
            if not os.path.exists("{0}/{1}".format(directory, filename)):
                self.logger.info("Extracting...")
                local_filename = "{0}_{1}.{2}".format(attachment['name'].split(".", 1)[0], attachment['id'], attachment['name'].split(".", 1)[-1])
                cmd = "tar xf {0}/{1} -C {2} --exclude 'lastlog'".format(directory, local_filename, directory)
                subprocess.call(cmd,shell=True)
                cmd = "gunzip -qrf {0}/{1}/var/log".format(directory, filename)
                subprocess.call(cmd,shell=True)
            else:
                self.logger.info("Already extracted")
        elif file_extension == "tar":
            if not os.path.exists("{0}/{1}".format(directory, filename)):
                self.logger.info("Extracting...")
                local_filename = "{0}_{1}.{2}".format(attachment['name'].split(".", 1)[0], attachment['id'], attachment['name'].split(".", 1)[-1])
                cmd = "tar xf {0}/{1} -C {2} --exclude 'lastlog'".format(directory, local_filename, directory)
                subprocess.call(cmd,shell=True)
        else:
            self.logger.info("Not a cl_support, will not extract")

    def __splitext(self, path):
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
