import os
import requests
import urllib
import json

from aws_signing import AwsSigningV4
from secret import *

client_id = CLIENT_ID
client_secret = CLIENT_SECRET
api_key = API_KEY


def main():
    openbanking_endpoint = "https://developer-api-sandbox.dnb.no"

    aws_signing_v4 = AwsSigningV4(
        aws_access_key_id=client_id,
        aws_secret_access_key=client_secret,
        aws_host="developer-api-sandbox.dnb.no",
        aws_region="eu-west-1",
        aws_service="execute-api",
    )
    request_handler = RequestHandler(
        endpoint=openbanking_endpoint,
        aws_signing_v4=aws_signing_v4
    )

    # Get API Token
    api_token_params = {"customerId": '{"type":"SSN", "value":"29105573083"}'}
    api_token_path = "/token"
    api_token_response = request_handler.get_request(
        path=api_token_path, params=api_token_params
    )
    api_token = api_token_response.json()["tokenInfo"][0]["jwtToken"]
    print("api_token: " + api_token)

    # Get customer details
    customer_params = {}
    customer_path = "/customers/current"
    customer_response = request_handler.get_request(
        path=customer_path, params=customer_params, api_token=api_token
    )
    customer_response_json = customer_response.json()
    print(json.dumps(customer_response_json, indent=4, sort_keys=True))


class RequestHandler(object):
    def __init__(self, endpoint, aws_signing_v4):
        self.__endpoint = endpoint
        self.__aws_signing_v4 = aws_signing_v4

    def __to_canonical_querystring(self, params):
        canonical_querystring = ""
        # parameters have to be sorted alphabetically for the signing part
        for param_key, param_value in sorted(params.items()):
            if canonical_querystring != "":
                canonical_querystring += "&"
            canonical_querystring += param_key + "=" + urllib.parse.quote(param_value)
        return canonical_querystring

    def get_request(self, path, params, api_token=None):
        canonical_querystring = self.__to_canonical_querystring(params)
        headers = self.__aws_signing_v4.headers_for_get_method(
            path, canonical_querystring
        )

        # 'host' header is added automatically by the Python 'requests' library.
        headers["Accept"] = "application/json"
        headers["Content-type"] = "application/json"
        headers["x-api-key"] = api_key

        # All endpoints require the API token, except the API token endpoint.
        if api_token:
            headers["x-dnbapi-jwt"] = api_token

        request_url = self.__endpoint + path + "?" + canonical_querystring
        # Used for troubleshooting
        #print(f'Request URL: {request_url}')
        #print(f'Request Headers: {headers}')
        return requests.get(request_url, headers=headers)


if __name__ == "__main__":
    main()
