# -*- coding: utf-8 -*-
from mock import patch
from datetime import datetime
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor

from connect.api import ConnectApi
from connect.client import ConnectClient
from connect.event import Event
from connect import exceptions, responses

SINGLE_EVENT_DATA = {
    'type': 'cycling',
    'distance': 21255,
    'caloriesBurned': 455,
    'duration': 67,
    'user': {
        'id': '638396',
        'first': 'Bruce'
    },
    'id': 1,
    'timestamp': datetime(2015, 8, 27, 10, 17)
}

MULTI_EVENT_DATA = [{
    'type': 'cycling',
    'distance': 21255,
    'caloriesBurned': 455,
    'duration': 67,
    'user': {
        'id': '638396',
        'name': 'Bruce'
    },
    'id': 2,
    'timestamp': datetime(2015, 8, 27, 10, 17)
}, {
    'type': 'swimming',
    'distance': 21255,
    'caloriesBurned': 455,
    'duration': 67,
    'user': {
        'id': '638396',
        'name': 'Bruce',
    },
    'id': 3,
    'timestamp': datetime(2015, 8, 27, 10, 17)
}]


COLLECTION_NAME = 'my_collection'

PROJECT_ID = "MY_PROJECT_ID"
API_PUSH_KEY = "MY_PUSH_API_KEY"
BASE_URL = "https://api.getconnect.io"
    
class TestConnectClient:
    
    def setup_method(self, method):
        connect = ConnectClient(project_id=PROJECT_ID, 
                 api_key=API_PUSH_KEY)
        self.connect = connect
     
    def test_init(self):
        
        connect_api = self.connect._api      
        assert isinstance(connect_api, ConnectApi)
        assert connect_api._project_id == PROJECT_ID
        assert connect_api._api_key == API_PUSH_KEY
        assert connect_api._get_timeout == 60
        assert connect_api._post_timeout == 60
        assert connect_api._base_url == BASE_URL
        
        assert isinstance(self.connect._executor, ThreadPoolExecutor)
        assert self.connect._executor._max_workers == 2

    @patch("connect.client.ConnectApi.post_event")
    def test_push_event(self, post_event):
        f = self.connect.push_event(COLLECTION_NAME,SINGLE_EVENT_DATA)
        assert isinstance(f, Future)        
        f.result()
        expected_event = Event(COLLECTION_NAME, SINGLE_EVENT_DATA)
        
        args, kwargs = post_event.call_args
        actual_event = args[0]
         
        assert post_event.call_count == 1        
        assert actual_event.body == expected_event.body
        
        bad_future = self.connect.push_event(COLLECTION_NAME,"a string")
        assert isinstance(bad_future, Future)        
        assert isinstance(bad_future.exception(), exceptions.InvalidEventError)
    
    @patch("connect.client.ConnectApi.post_events")
    def test_push_events(self, post_events):
        events_by_collection = {COLLECTION_NAME : MULTI_EVENT_DATA}        

        f = self.connect.push_events(events_by_collection)
        assert isinstance(f, Future) 
        f.result()
        expected_events = defaultdict(list)
        for e in MULTI_EVENT_DATA:            
           e = Event(COLLECTION_NAME, e)
           expected_events[COLLECTION_NAME].append(e.body)        
        
        args, kwargs = post_events.call_args
        actual_events = args[0]
        
        actual_event_details = defaultdict(list)
        
        for a in actual_events:
            actual_event_details[a].append(actual_events[a])

        assert post_events.call_count == 1
        assert set(actual_event_details) == set(expected_events)

        # raise exception if dict is not passed in
        bad_future = self.connect.push_events("a string")
        assert isinstance(bad_future, Future)        
        assert isinstance(bad_future.exception(), exceptions.InvalidEventError)
        
        # raise exception if dict value is passed in but the value is not a list
        bad_batch = {COLLECTION_NAME: SINGLE_EVENT_DATA}
        bad_future = self.connect.push_events(bad_batch)
        assert isinstance(bad_future, Future)        
        assert isinstance(bad_future.exception(), exceptions.InvalidEventError)
        
        # raise exeception if events are not in correct format
        bad_batch =  {COLLECTION_NAME: [1,2]}
        bad_future = self.connect.push_events(bad_batch)
        assert isinstance(bad_future, Future)        
        assert isinstance(bad_future.exception(), exceptions.InvalidEventError)

    @patch("connect.client.ConnectApi.post_events")
    def test_push_processed_events(self, post_events):
        events = []
        expected_events = defaultdict(list)
        for e in MULTI_EVENT_DATA:            
            events.append(Event(COLLECTION_NAME, e))    
            expected_events[COLLECTION_NAME].append(e)
        post_events.return_value = responses.PushBatchResponse(None,None,None)
        result = self.connect._push_processed_events(events)
        
        assert isinstance(result, responses.PushBatchResponse)
        assert post_events.call_count == 1
        args, kwargs = post_events.call_args
        actual_events = args[0]
        assert set(actual_events) == set(expected_events)


    @patch("connect.client.ConnectApi.post_events")
    def test_push_processed_events_multiple_collections(self, post_events):
        events = []
        expected_events = defaultdict(list)
        for e in MULTI_EVENT_DATA:            
           events.append(Event(COLLECTION_NAME, e)) 
           expected_events[COLLECTION_NAME].append(e)        
          
        for e in MULTI_EVENT_DATA:
           events.append(Event("my_collection2", e)) 
           expected_events["my_collection2"].append(e) 
        
        post_events.return_value = responses.PushBatchResponse(None,None,None)
        result = self.connect._push_processed_events(events)
        assert post_events.call_count == 1        
        assert isinstance(result, responses.PushBatchResponse)

        args, kwargs = post_events.call_args
        actual_events = args[0]
        assert set(actual_events) == set(expected_events)