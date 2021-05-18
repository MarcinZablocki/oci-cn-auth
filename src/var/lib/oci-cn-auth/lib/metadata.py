import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_metadata(endpoint): 
    """ Make a request to metadata endpoint """

    retry_strategy = Retry(
        total=3,  
        backoff_factor=30
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )

    adapter = HTTPAdapter(TimeoutHTTPAdapter(max_retries=retry_strategy))
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    headers = { 'Authorization' : 'Bearer Oracle' }
    metadata_url = "http://169.254.169.254/opc/"
    metadata_ver = "2"
    request_url = metadata_url + "v" + metadata_ver + "/" + endpoint
    return http.get(request_url, headers=headers).json()

def get_identity():
    return get_metadata('identity')

def get_instance():
    return get_metadata('instance')
