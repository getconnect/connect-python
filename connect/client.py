# -*- coding: utf-8 -*-
from collections import defaultdict
from concurrent import futures 

from connect.api import ConnectApi
from connect.event import Event
from connect import exceptions

class ConnectClient(object):
    """
    The ConnectClient is the main object to use to push and query events in
    Connect.
    """

    def __init__(self,
                 project_id,
                 api_key,
                 base_url=None,
                 get_timeout=None,
                 post_timeout=None,
                 max_workers=2
                 ):
        """Initializes a ConnectClient object.

        :param project_id: the Connect project id
        :param api_key: the Connect api key for the project
        :param base_url: alternate url to use for testing purposes
        :param get_timeout: timeout for get requests in seconds
        :param post_timeout: timeout for post requests in seconds
        :param max_workers: maximum number of workers for the ThreadPoolExecutor
        """

        if get_timeout is None:
            get_timeout = 60

        if post_timeout is None:
            post_timeout = 60

        self._api = ConnectApi(project_id=project_id,
                              api_key=api_key,
                              base_url=base_url,
                              post_timeout=post_timeout,
                              get_timeout=get_timeout)
                    
        executor = futures.ThreadPoolExecutor(max_workers=max_workers)    
        self._executor = executor
        
    def push_event(self, collection_name, event):
        """ Validate and process single event
        then push directly to connnect

        :param collection_name: the collection name for the event in the
        project
        :param event: dict with the event data to push to connect
        :param async: boolean push event asynchronously
        
        returns Future object for api call
        """

        try:            
            processed_event = Event(collection_name, event)
        except exceptions.InvalidEventError as e:
            future = futures.Future()                         
            future.set_exception(e)
            return future
        
        return self._executor.submit(self._api.post_event, processed_event)
        
    def push_events(self, events):
        """ Validate and process multiple events
        then push to connect as a batch
       
        :param events: dict keyed by collection nane with a list of dict 
        objects as value

        returns future object
        """
        
        if not isinstance(events, (dict)):
            ex =  exceptions.InvalidEventError(
                "Events must be a list of dict objects")
            future = futures.Future()            
            future.set_exception(ex)
            return future
            
        events_by_collection = defaultdict(list)
        for collection in events:
            if isinstance(events[collection], list):
                for event in events[collection]:
                    try:                
                        e = Event(collection, event)
                    except exceptions.InvalidEventError as ex:
                        future = futures.Future()                    
                        future.set_exception(ex)
                        return future
                    events_by_collection[collection].append(e.body)
            
            else:
                ex =  exceptions.InvalidEventError(
                   "Events must be a list of dict objects")
                future = futures.Future()            
                future.set_exception(ex)
                return future
            
        return self._executor.submit(self._api.post_events, events_by_collection)

    
    def _push_processed_events(self, events):
        """ Push multi processed (validated) events
        :param events: list of Event objects
        
        returns PushBatchResponse object
        
        """
        events_by_collection = defaultdict(list)
        for e in events:
               collection_name = e.collection_name
               events_by_collection[collection_name].append(e.body)
            
        return self._api.post_events(events_by_collection)

    def _export_events(self, collection_name, parameters): # pragma: no cover
        """ Export entire events from connect based on a supplied filter.
        Returns a list of dict objects

        :param collection_name: the name of the collection where the event
        lives
        :param parameters: connect filter to retrieve specific events
        """
        results, status_code = self._api.get_events(collection_name,parameters)
        response = {"http_status_code": status_code,
                    "results": results}
        return response

    def _bulk_export(self, collection_name, parameters): # pragma: no cover
        """ Initiate bulk export from connect to S3
        returns the export_id to track the status of the export
        
        :param collection_name: name of the collection
        :param parameters: dict object of parameters for export as defined in
        the HTTP connect doco: 
        http://docs.getconnect.io/http#exporting-events
        """        
        status_url  = self._api.post_export(collection_name,parameters)
        status_url_split = status_url.replace("https://","").split("/")
        export_id = status_url_split[4]

        return export_id

    def _bulk_export_status(self, collection_name, export_id): # pragma: no cover
        """ Get the correct status of a S3 bulk export
        :param collection_name: name of collection
        :parma export_id: as supplied by bulk_export methid
        """
        results, status_code = self._api.get_export_status(collection_name, 
                                                          export_id)
        response = {"results" : results,
                    "http_status_code" : status_code}
        return response        