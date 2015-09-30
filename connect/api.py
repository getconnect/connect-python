# -*- coding: utf-8 -*-
import json

from requests import Session

from connect import responses

class ConnectApi(object):
    """
    Used by the client to communicate to the connect API.
    """
    
    def __init__(self,
                 project_id, 
                 api_key, 
                 base_url=None,
                 post_timeout=None,
                 get_timeout=None):
        
        """ Initializes a ConnectAPI object
        
        :param project_id: the Connect project id
        :param api_key: the Connect api key for the project
        :param base_url: alternate url to use for testing purposes
        :param post_timeout: timeout in seconds for post requests
        :param get_timeout: timeout in seconds for get requests
        """
        self._project_id = project_id
        self._api_key = api_key
        self._session = self._create_session()
        
        if post_timeout is not None:
            self._post_timeout = post_timeout
        else:
            self._post_timeout = 60
            
        if get_timeout is not None:
            self._get_timeout = get_timeout
        else:
            self._get_timeout = 60
        
        if base_url is not None:
            self._base_url = base_url
        else:
            self._base_url = "https://api.getconnect.io"

    def _create_session(self):
        s = Session()
        s.headers.update({"Content-Type": "application/json", 
                          "X-Api-Key": self._api_key, 
                          "X-Project-Id": self._project_id})
        return s
        
    def post_event(self,event):
        """ Post a single event to Connect API
       
        :param event: Event object with the event data to push to connect
        """
        collection_name = event.collection_name
        url = "{0}/events/{1}".format(self._base_url, collection_name)
        payload = json.dumps(event.body)
        r = self._session.post(url=url,
                              data=payload, 
                              timeout=self._post_timeout)       

        try:
            results = r.json()
        except ValueError:
            results = None # 200 has an empty response
        
        return self._build_response(response_body=results, 
                                    raw_event=event.body, 
                                    status_code=r.status_code)
        
        
    
    def post_events(self,event_batch):
        """ Post multiple events to the Connect API as a batch
    
        :param event_batch: list of events as dicts grouped by collection
        """
        url = "{0}/events".format(self._base_url)
        payload = json.dumps(event_batch)
        
        r = self._session.post(url=url, 
                               data=payload, 
                               timeout=self._post_timeout)
        
        results = r.json()
        return self._build_batch_response(response_body=results, 
                                          events_by_collection=event_batch, 
                                          status_code=r.status_code)

    def _get_export(self,collection_name,parameters): # pragma: no cover
        """ Export entire events from connect based on a supplied filter.
        Returns a list of dict objects
            
        :param collection_name: the name of the collection where the event 
        lives
        :param parameters: connect filter to retrieve specific events

        """        
        payload = json.dumps(parameters)
        url = "{0}/events/{1}/export".format(self._base_url,collection_name)
        r = self._session.get(url=url, 
                             params={"query":payload}, 
                             timeout=self._get_timeout)
        
        try:
            results = r.json()
        except ValueError:
            results = None
        
        return results, r.status_code
        
    def _post_export(self, collection_name, parameters): # pragma: no cover
        """Export data from Connect to a json file on Amazon S3
        
        returns an id string to track the status using get_export_status        
        
        :param collection_name: the name of the collection exporting from
        :param parameters connect specific dict object with options
        """        
        url = "{0}/events/{1}/export".format(self._base_url,collection_name)

        payload = json.dumps(parameters)
        request = self._session.post(url=url, 
                                    data=payload, 
                                    timeout=self._get_timeout)
        try:
            results = request.headers["location"]
        except ValueError:
            results = None
        
        response = {"http_status_code": request.status_code,
                    "results": results}        
        
        return response
    
    def _get_export_status(self, collection_name, export_id): # pragma: no cover
        """ Retrieve the status of a post_export 
        
        :param collection_name: the name of the collection exproting from
        :parma export_id: the export id from post_export
        
        """
        url = "{0}/events/{1}/export/{2}".format(self._base_url,
                                                collection_name,
                                                export_id)
        r = self._session.get(url=url, 
                             timeout=self._get_timeout)
        try:
            result = r.json()
        except ValueError:
            result = None
            
        return result, r.status_code
        
    def _build_response(self, response_body, raw_event, status_code):
        error_message = None
        if status_code == 401:
            error_message = "Unauthorised. Please check your Project Id and API Key"
        else:
            if response_body is not None and "errorMessage" in response_body:
                error_message = response_body["errorMessage"]
            elif response_body is not None and "errors" in response_body:
                error_message = response_body["errors"]
        
        return responses.PushResponse(status_code, 
                                     error_message, 
                                     raw_event)
    def _build_batch_response(self, 
                              response_body, 
                              events_by_collection, 
                              status_code):
        results = {}
        error_message = None

        if "errorMessage" in response_body:
            error_message = response_body["errorMessage"]
        else:
            for collection in response_body:
                index = 0
                batch_response = []            
                for r in response_body[collection]:
                    event = events_by_collection[collection][index]

                    if "message" in r:
                        message = r["message"]
                    else:
                        message = None
                        
                    event_response = responses.PushResponse(None,
                                                           message,
                                                           event,
                                                           r["success"])                    
                         
                    batch_response.append(event_response)
                    index += 1
                results[collection] = batch_response

        return responses.PushBatchResponse(status_code, error_message, results)
    