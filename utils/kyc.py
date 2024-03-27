#############################################################
# KYC Synaps API
# https://docs.synaps.io/
#############################################################

import requests
import json
from os import environ as env
from utils.log import Logger


class Synaps:
    def __init__(self):
        self.log = Logger()
        self.url = env['SYNAPS_API_URL']
        self.timeout = int(env['SYNAPS_API_TIMEOUT'])
        self.api_key = env['SYNAPS_API_KEY']
        self.headers = {
            'Accepts': 'application/json',
            'Content-Type': 'application/json',
            'Api-Key': self.api_key
        }

    def _http_request(self, method="GET", uri=None, parameters=None):
        """
        Generic http request
        :param method: http request method
        :param uri: endpoint uri
        :param parameters: request parameters
        :return:
        """
        if uri is None:
            return False

        url = self.url + uri

        if method == "GET":
            try:
                if parameters is not None:
                    result = requests.get(url, timeout=self.timeout, headers=self.headers, params=parameters)
                else:
                    result = requests.get(url, timeout=self.timeout, headers=self.headers)
            except Exception as e:
                self.log.error("HTTP request to Synaps API failed\nURL = {0}\nError = {1}".format(url, e))
                return False, 500
        elif method == "POST":
            try:
                result = requests.post(url, timeout=self.timeout, headers=self.headers, data=parameters)
            except Exception as e:
                self.log.error("HTTP request to Synaps API failed\nURL = {0}\nError = {1}".format(url, e))
                return False, 500
        else:
            return False, 405

        try:
            if result.status_code >= 500:
                self.log.error("Synaps API answered with http status {}".format(result.status_code))
                return False, 500
            else:
                json_data = json.loads(result.content.decode())
                return json_data, result.status_code
        except ValueError:
            self.log.error("Synaps API request, failed to load json")
            return False, 500

    def init_session(self):
        """
        Init a new verification session for a user
        :return:
        """
        uri = 'session/init'

        response, http_code = self._http_request(method='POST', uri=uri)
        if response is False:
            return response, http_code, "error_kyc_init", None
        else:
            session_id = response.get('session_id')

        return True, 200, "success_kyc_init", session_id
