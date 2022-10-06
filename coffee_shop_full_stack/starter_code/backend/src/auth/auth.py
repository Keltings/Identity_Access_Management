import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen


#initializing/configuring the data to reflect my auth0 account
AUTH0_DOMAIN = 'kelting.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'


## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    '''
    Implementing a get_token_auth_header() method
    that attempts to get the header from the request
        and raises an AuthError if no header is present.
    it also attempts to split bearer and the token
        and raises an AuthError if the header is malformed and finally
    returns the token part of the header

    I.E Obtains the Access Token from the Authorization Header
    '''

    
   
    # check if authorization is not in request
    if 'Authorization' not in request.headers:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    auth_header = request.headers['Authorization']    
    header_parts = auth_header.split(' ')

    # check if token is valid
    if len(header_parts) !=2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    elif header_parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)
    
    

    """elif len(header_parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)"""

    token = header_parts[1]
    return token


def check_permissions(permission, payload):
    '''
Implementing a check_permissions(permission, payload) method
    with INPUTS as
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

   Raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''

    if 'permissions' not in payload:
                        raise AuthError({
                            'code': 'invalid_claims',
                            'description': 'Permissions not included in JWT.'
                        }, 400)                  

    #check if permission exits within that payload array
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)

    return True    

## Auth Header
def verify_decode_jwt(token):
    '''
    Implementing a verify_decode_jwt(token) method that:
    INPUTS:
        token: a json web token (string)

    is an Auth0 token with key id (kid),
    verifies the token using Auth0 /.well-known/jwks.json,
    decodes the payload from the token,
    validates the claims and finally,  
    returns the decoded payload,

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
    '''

    # Get the public key from Auth0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    #get the data in the header to determine if we have the correct key
    unverified_header = jwt.get_unverified_header(token)

    # Choose and format the rsa key
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    #iterate over all of the jwks keyswhich we recieved in our request to auth0
    
    for key in jwks['keys']:
        #if we find a match for key id that matchesthe key id in our header
        if key['kid'] == unverified_header['kid']:
            #then we structure it:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    
    if rsa_key:
        try:
            #use the key to validate/decode the jwt
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)


'''
implement @requires_auth(permission) decorator method
@INPUTS
    permission: string permission (i.e. 'post:drink')

it should uses the get_token_auth_header method to get the token
it should uses the verify_decode_jwt method to decode the jwt
it should uses the check_permissions method validate claims and check the requested permission and
returns the decorator which passes the decoded payload to the decorated method
'''
#default the parameter to single prmision string string
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)  
            # ensure that the permision exist in the required claim in jwt      
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator