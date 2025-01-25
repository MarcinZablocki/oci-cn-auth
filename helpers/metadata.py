"""
Read and return metadata

"""
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

DEFAULT_TIMEOUT = 5


def get_metadata(endpoint):
    """ Make a request to metadata endpoint """

    session = requests.Session()

    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=30,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    headers = {'Authorization': 'Bearer Oracle'}
    metadata_url = "http://169.254.169.254/opc/"
    metadata_ver = "2"
    request_url = metadata_url + "v" + metadata_ver + "/" + endpoint
    return session.get(request_url, headers=headers, timeout=DEFAULT_TIMEOUT).json()


def get_identity():
    """ return identity metadata """
    return get_metadata('identity')


def get_instance():
    """ return instance metadata """
    return get_metadata('instance')
