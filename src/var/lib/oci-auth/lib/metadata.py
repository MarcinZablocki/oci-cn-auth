import requests

def get_metadata(endpoint): 
    """ Make a request to metadata endpoint """

    headers = { 'Authorization' : 'Bearer Oracle' }
    metadata_url = "http://169.254.169.254/opc/"
    metadata_ver = "2"
    request_url = metadata_url + "v" + metadata_ver + "/" + endpoint
    return requests.get(request_url, headers=headers).json()

def get_identity():
    return get_metadata('identity')

def get_instance():
    return get_metadata('instance')