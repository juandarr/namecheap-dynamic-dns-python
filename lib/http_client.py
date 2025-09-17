#!/usr/bin/env python
import sys
PYTHON_MAJOR_VERSION = sys.version_info[0]



class HttpClient:

    def __init__(self, host, port=None, user=None, password=None, secure=False, verbose=False):
        self.host = host
        self.port = int(port) if port is not None else 443 if secure else 80
        self.auth_token = HttpClient.encode_up(user, password) if user and password else None
        ## TODO add support for specifying trusted CA certs, and even client TLS auth (uncommon in HTTP)
        self.secure = secure
        self.verbose = verbose

    def get(self, context, headers={}, body=None, params={}):
        return self.request(
            "GET", context,
            additional_headers=headers, body=body, params=params
        )

    def put(self, context, body, content_type="text/plain", headers={}, params={}):
        additional_headers = {'content-type': content_type}
        additional_headers.update(headers)
        return self.request(
            "PUT", context,
            additional_headers=additional_headers, body=body, params=params
        )

    def post(self, context, body, content_type="text/plain", headers={}, params={}):
        additional_headers = {'content-type': content_type}
        additional_headers.update(headers)
        return self.request(
            "POST", context,
            additional_headers=additional_headers, body=body, params=params
        )

    def delete(self, context, headers={}, body=None, params={}):
        return self.request(
            "DELETE", context,
            additional_headers=headers, body=body, params=params
        )

    def request(self, verb, context, additional_headers={}, body=None, params={}):
        url = HttpClient.create_url(context, params)
        headers = HttpClient.create_default_headers()
        headers.update({'Host': self.host})
        if self.auth_token :
            headers.update({'Authorization': 'Basic ' + self.auth_token})
        headers.update(additional_headers)
        
        connection = HttpClient.create_connection(self.host, self.port, self.secure)
        try :
            if self.verbose :
                print("host:    {}".format(self.host))
                print("port:    {}".format(self.port))
                print("verb:    {}".format(verb))
                print("url:     {}".format(url))
                print("headers: {}".format(headers))
                print("body:    {}".format(body))
            connection.request(verb, url, headers=headers, body=body)
            response = connection.getresponse()
            ret = {
                'status': response.status,
                'headers': self.list_to_dict(response.getheaders()),
                'body': response.read()
            }
            if self.verbose :
                print("response: {}".format(ret))
            return ret
        finally :
            connection.close()

    @staticmethod
    def create_default_headers():
        return {
            'content-type': "text/plain"
        }
    
    @staticmethod
    def create_connection(host, port, secure) :
        f = None
        if PYTHON_MAJOR_VERSION < 3 :
            import httplib
            f = httplib.HTTPSConnection if secure else httplib.HTTPConnection
        else :
            import http.client
            f = http.client.HTTPSConnection if secure else http.client.HTTPConnection
        return f(host, port)

    @staticmethod
    def create_url(context, params):
        ret = context
        i = 0
        for k, v in params.items():
            sep = "?" if i == 0 else "&"
            ret += "{}{}={}".format(sep, k, v)
            i += 1
        return ret

    @staticmethod
    def encode_up(user, password) :
        import binascii
        b64 = binascii.b2a_base64("{}:{}".format(user, password).encode('UTF-8'))
        return b64[:len(b64)-1].decode('UTF-8')
    
    @staticmethod
    def escape(path):
        if PYTHON_MAJOR_VERSION < 3 :
            import urllib
            return urllib.quote(path)
        else :
            import urllib.parse
            return urllib.parse.quote(path)

    @staticmethod
    def escape_slash(path):
        return HttpClient.escape(path).replace("/", "%2F")

    @staticmethod
    def pretty_print_response(response, verbose, b64=False):
        if b64:
            import base64
            body = "{}".format(base64.b64encode(response['body']).decode())
        else:
            body = response['body']
        if verbose:
            print("Status: {}".format(response['status']))
            print("Headers:")
            headers = response['headers']
            for k, v in headers.items():
                print("    {}: {}".format(k, v))
            print("Body: {}".format(body))
        elif response['body']:
            print(body.decode('UTF-8'))
    
    @staticmethod
    def list_to_dict(el):
        ret = {}
        for k, v in el:
            ret[k] = v
        return ret
