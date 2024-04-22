import boto3
import requests
import json

from os import environ as env
from base64 import b64decode

from utils.log import Logger


class ObjectStorage:
    """
    Class to interact with Scaleway Object Storage API
    """
    def __init__(self):
        """
        Initialize connection and feature with Scaleway Object storage API
        """
        self.access_key = env['SCALEWAY_ACCESS_KEY']
        self.secret_key = env['SCALEWAY_SECRET_KEY']
        self.region = env['SCALEWAY_REGION']
        self.service = env['SCALEWAY_SERVICE']
        self.domain = env['SCALEWAY_DOMAIN']
        self.bucket_name = env['SCALEWAY_BUCKET_NAME']
        self.api_url = "https://{service}.{region}.{domain}/".format(
            service=self.service,
            region=self.region,
            domain=self.domain)
        self.bucket_url = "https://{bucket}.{service}.{region}.{domain}/".format(
            bucket=self.bucket_name,
            service=self.service,
            region=self.region,
            domain=self.domain)
        self.bucket_directory = env['APP_ENVIRONMENT'] + '/'
        self.connexion = None

    def get_s3_connexion(self):
        """
        Initiate and return a connection to Scaleway object storage
        :return:
        """
        session = boto3.session.Session()
        self.connexion = session.client(service_name=self.service, region_name=self.region, use_ssl=True,
                                        endpoint_url=self.api_url, aws_access_key_id=self.access_key,
                                        aws_secret_access_key=self.secret_key)

    def get_service(self, prefix=None):
        """
        returns a list of all buckets/objects owned by the authenticated user that sent the request.
        :return:
        """
        if prefix is None:
            result = self.connexion.list_objects(Bucket=self.bucket_name)
        else:
            result = self.connexion.list_objects(Bucket=self.bucket_name, Prefix=prefix)
        return result

    def object_exists(self, object_path):
        """
        check if the object already exists on object storage
        :param object_path:
        :return:
        """
        searched_path = self.bucket_directory + object_path
        existing_services = self.list_objects()
        if existing_services is not False:
            for existing_object in existing_services:
                current_object_name = existing_object.get('Key')
                if current_object_name == searched_path:
                    return True
        return False

    def store_object(self, local_path=None, object_path=None, object_content=None, public_read=False):
        """
        Store a new file into bucket
        :param local_path: relative path to the local file
        :param object_path: full path including filename of the object in bucket
        :param object_content: data to be stored
        :param public_read: Define if object must be publicly readable
        :return: True if object successfully stored on bucket
        """

        log = Logger()
        if local_path is None and object_content is None:
            return False

        if local_path is not None:
            # we load object_content with the file stored on local path
            try:
                with open(local_path, 'r') as local_file:
                    object_content = local_file.read()
                    local_file.close()
            except Exception as e:
                log = Logger()
                log.error("Error loading local file, exception = {0}".format(e))
                return False

        storage_path = self.bucket_directory + object_path
        result = self.connexion.put_object(Bucket=self.bucket_name, Body=object_content,
                                           Key=storage_path).get('ResponseMetadata')
        if result is not None:
            if result.get('HTTPStatusCode') == 200:
                if public_read is True:
                    self.connexion.put_object_acl(Bucket=self.bucket_name, Key=storage_path, ACL='public-read')
                return True
            else:
                log.warning("Failed to store object in object storage. Result = {0}".format(result))
                return False
        else:
            log.warning("Something went wrong when putting object, object storage returned None")
            return False

    def delete_object(self, object_path):
        """
        Delete an object from the bucket
        :param object_path:
        :return:
        """
        log = Logger()
        storage_path = self.bucket_directory + object_path
        result = self.connexion.delete_object(Bucket=self.bucket_name, Key=storage_path).get('ResponseMetadata')
        if result is not None:
            if result.get('HTTPStatusCode') == 200 or result.get('HTTPStatusCode') == 204:
                return True
            else:
                log.warning("Failed to delete object from object storage. Result = {0}".format(result))
                return False
        else:
            log.warning("Something went wrong when deleting object. Result = {0}".format(result))
            return False

    def get_object(self, object_path, full_path=False):
        """
        Get an object from the bucket
        Example :
        from utils.scaleway import ObjectStorage
        storage = ObjectStorage()
        storage.get_s3_connexion()
        doc = storage.get_object(object_path="KT1T1tZRqU7DuLf6qsMFxBFFXqLsAG3qhXxY.json")
        if doc is not False:
            with open("test", 'w') as local_file:
                local_file.write(doc)
                local_file.close()
        :param object_path:
        :param full_path: define if we should add bucket directory
        :return:
        """
        log = Logger()
        if full_path is False:
            object_path = self.bucket_directory + object_path
        try:
            result = self.connexion.get_object(Bucket=self.bucket_name, Key=object_path)
        except Exception as e:
            log.warning("Error while retrieving object from Object storage. Error = {0}".format(e))
            return False

        response_metadata = result.get('ResponseMetadata')
        file_metadata = result.get('Metadata')
        file_content = result.get('Body')

        if response_metadata is not None:
            if response_metadata.get('HTTPStatusCode') == 200:
                return file_content.read().decode('latin-1')
            else:
                log.warning("Failed to get object from object storage. Result = {0}".format(result))
                return False
        else:
            log.warning("Something went wrong when getting object. Result = {0}".format(result))
            return False

    def list_objects(self, directory=None):
        """
        List all objects from the given bucket directory
        :param directory: directory of the S3 bucket to retrieve files info from
        :return:
        """
        log = Logger()
        if directory is None:
            storage_directory = self.bucket_directory
        else:
            storage_directory = self.bucket_directory + directory

        try:
            result = self.connexion.list_objects(Bucket=self.bucket_name, Prefix=storage_directory)
        except Exception as e:
            log.warning("Error while retrieving object from Object storage. Error = {0}".format(e))
            return False

        response_metadata = result.get('ResponseMetadata')
        objects_list = result.get('Contents')
        if response_metadata is not None:
            if response_metadata.get('HTTPStatusCode') == 200:
                if objects_list is not None:
                    return objects_list
                else:
                    return []
            else:
                log.warning("Failed to get objects list from object storage. Result = {0}\nDirectory = {1}".format(
                    result, storage_directory))
                return False
        else:
            log.warning("Something went wrong when getting objects list. Result = {0}".format(result))
            return False


class SecretManager:
    """
    Class to interact with Scaleway Secret Manager API
    """
    def __init__(self):
        """
        Initialize connection and feature with Scaleway Secret Manager API
        """
        self.secret_key = env['SCALEWAY_SECRET_KEY']
        self.base_url = env['SCALEWAY_SM_URL']
        self.region = env['SCALEWAY_REGION']
        self.timeout = int(env['SCALEWAY_TIMEOUT'])
        self.api_url = "{base_url}{region}/secrets".format(
            base_url=self.base_url,
            region=self.region)
        self.headers = {
            'Content-Type': 'application/json',
            'X-Auth-Token': self.secret_key
        }
        self.log = Logger()

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

        url = self.api_url + uri

        if method == "GET":
            try:
                if parameters is not None:
                    result = requests.get(url, timeout=self.timeout, headers=self.headers, params=parameters)
                else:
                    result = requests.get(url, timeout=self.timeout, headers=self.headers)
            except Exception as e:
                self.log.error("HTTP request to Scaleway secrets API failed\nURL = {0}\nError = {1}".format(url, e))
                return False, 500
        elif method == "POST":
            try:
                result = requests.post(url, timeout=self.timeout, headers=self.headers, data=parameters)
            except Exception as e:
                self.log.error("HTTP request to Scaleway secrets API failed\nURL = {0}\nError = {1}".format(url, e))
                return False, 500
        else:
            return False, 405

        try:
            if result.status_code >= 500:
                self.log.error("Scaleway secrets API answered with http status {}".format(result.status_code))
                return False, 500
            else:
                json_data = json.loads(result.content.decode())
                return json_data, result.status_code
        except ValueError:
            self.log.error("Scaleway secrets API request, failed to load json")
            return False, 500

    def get_secrets(self, secret_id):
        """
        Load secrets from Secret Manager
        :return:
        """
        uri = "/{secret_id}/versions/latest/access".format(secret_id=secret_id)
        response, http_code = self._http_request(method='GET', uri=uri)
        if response is False:
            return False
        data = b64decode(response.get('data'))
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            return data
