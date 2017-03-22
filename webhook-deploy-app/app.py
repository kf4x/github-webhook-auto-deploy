__version__ = '0.1'
__author__ = 'Javier Chavez'

from wsgiref.util import setup_testing_defaults
from hashlib import sha1
from subprocess import call

import json
import hmac
import os


def _verify(body, secret, sig):
    """Verifies the signature is reproducable.
    
    hashes body arg with secret and compares it to sig.
    
    Args:
        body: bytes to hash(sign)
        secret: secret key that was used by github to sign the data
        sig: signature recieved. This is was we are verifing is valid.
        
    Returns:
       True if the sig is valid, False otherwise.
    """
    _hmac = hmac.new(secret, msg=body, digestmod=sha1)
    return hmac.compare_digest(_hmac.hexdigest(), sig)


def application(environ, start_response):
    """Intercept webhooks generated by GitHub
    
    When hit, it verifies signature in header, and 
    if the push is to a specific branch it will initiate a code update via
    a shell script. 
    """
    
    setup_testing_defaults(environ)
    status = '404 Not Found'
    message = ''
    headers = [('Content-type', 'application/json; charset=utf-8')]

    ret = [("%s: %s\n" % (key, value)).encode("utf-8") for key, value in environ.items()]
    # Get the sig and content length 
    _sig = environ.get('HTTP_X_HUB_SIGNATURE')
    length = environ.get('CONTENT_LENGTH')

    if _sig and length:
        length = int(length)
        body = environ['wsgi.input'].read(length)

        secret = bytes(os.environ['SECRET_KEY'], 'UTF-8')
        _sig = str(_sig).rstrip('\n')

        if _verify(body, secret, _sig.split('=')[1]):
            # We are expecting json
            content = json.loads(body.decode('utf-8'))
            # Get the name of the repo and branch
            repository = content.get('repository','').get('name', '')
            ref =  content.get('ref', '')
            # check if we need to run the script 
            if ref == 'refs/heads/dev' and respository:

                status = '200 OK'
                call(['bash', 'deploy.sh'])
                message = 'Update started.'
    # Create the response
    start_response(status, headers)
    return json.dumps({'status': status, 'message': message})



