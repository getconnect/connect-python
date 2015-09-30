# -*- coding: utf-8 -*-
import json
from mock import patch
from collections import defaultdict

from requests import Session
from connect.api import ConnectApi
from connect.event import Event
from connect import responses

PROJECT_ID = "MY_PROJECT_ID"
API_PUSH_KEY = "MY_PUSH_API_KEY"
BASE_URL = "https://api.getconnect.io"
COLLECTION_NAME = 'my_collection'   

MULTI_EVENT_DATA = [{
          'type': 'cycling',
          'distance': 21255,
          'caloriesBurned': 455,
          'duration': 67,
          'user': {
            'id': '638396',
            'name': 'Bruce'
          }
        },
        {
          'type': 'swimming',
          'distance': 21255,
          'caloriesBurned': 455,
          'duration': 67,
          'user': {
            'id': '638396',
            'name': 'Bruce',
          }
        }
        ]

SINGLE_EVENT_DATA =  {
        'type': 'cycling',
        'distance': 21255,
        'caloriesBurned': 455,
        'duration': 67,
        'user': {
            'id': '638396',
            'first': 'Bruce'
            }
        }

@patch("connect.api.Session.post")
class TestConnectAPI():

    def setup_method(self, method):
       
        batched = defaultdict(list)  
        for e in MULTI_EVENT_DATA:            
             e = Event(COLLECTION_NAME, e)
             batched[COLLECTION_NAME].append(e.body)

        self.multi_events = batched

        self.single_event = Event(COLLECTION_NAME,SINGLE_EVENT_DATA)
        self.connect = ConnectApi(project_id=PROJECT_ID, 
                 api_key=API_PUSH_KEY
                 )        
        
    def test_init(self, post):
        assert PROJECT_ID == self.connect._project_id
        assert API_PUSH_KEY == self.connect._api_key
        assert "https://api.getconnect.io" == self.connect._base_url
        assert 60 == self.connect._get_timeout
        assert 60 == self.connect._post_timeout
        assert isinstance(self.connect._session, Session)
    
        connect = ConnectApi(project_id=PROJECT_ID, 
                 api_key=API_PUSH_KEY,
                 base_url="myurl",
                 post_timeout=10,
                 get_timeout=5
                 )
        assert connect._base_url == "myurl"
        assert connect._post_timeout == 10
        assert connect._get_timeout == 5
        
    
    def test_post_event(self, post ):
        #200 - empty response
        mocked_response = mocked_connect_response(200,None)        
        post.return_value = mocked_response      
        result = self.connect.post_event(self.single_event)       
        assert isinstance(result,responses.PushResponse)
        post.reset_mock()
        
        with patch("connect.api.ConnectApi._build_response") as build_response:
            self.connect.post_event(self.single_event)
            url = "{0}/events/{1}".format(BASE_URL,COLLECTION_NAME)
            data = json.dumps(self.single_event.body)
            post.assert_called_once_with(url=url, data=data, timeout=60)            
            build_response.assert_called_once_with(response_body=None,
                                               raw_event=self.single_event.body,
                                               status_code=200)
            build_response.reset_mock()
            
            # Non-empty response (!= 200)
            body = {"errorMessage": "Maximum event size of 64kb exceeded."}            
            mocked_response = mocked_connect_response(413,body)        
            post.return_value = mocked_response        
            self.connect.post_event(self.single_event)
            build_response.assert_called_once_with(response_body=body,
                                               raw_event=self.single_event.body,
                                               status_code=413)
                                               
    def test_post_events(self,post):

        events = []
        expected_events = defaultdict(list)
        for e in MULTI_EVENT_DATA:            
            events.append(Event(COLLECTION_NAME, e))    
            expected_events[COLLECTION_NAME].append(e)        
            
        body = {
            COLLECTION_NAME: [{
                "event": events[0].body,
                "success": True
            }, {
                "event": events[1].body,
                "success": False,
                "message": "An error occured inserting the event please try again."
            }]
        }
        mocked_response = mocked_connect_response(200,body)        
        post.return_value = mocked_response
        
        result = self.connect.post_events(self.multi_events)
        url = "{0}/events".format(BASE_URL)
        data =  json.dumps(self.multi_events)
        post.assert_called_with(url=url, data=data, timeout=60)
        assert isinstance(result,responses.PushBatchResponse)
        
        with patch("connect.api.ConnectApi._build_batch_response") as build_batch_response:
            self.connect.post_events(self.multi_events)
            build_batch_response.assert_called_once_with(response_body=body,
                                               events_by_collection=self.multi_events,
                                               status_code=200)

        
    def test__build_response(self, post):
        single_event = Event(COLLECTION_NAME,SINGLE_EVENT_DATA)
        
        r = self.connect._build_response(None, single_event.body,200)        
        assert isinstance(r, responses.PushResponse)
        assert r.error_message is None
        assert r.http_status_code == 200
        assert r.event == single_event.body
        
        r = self.connect._build_response(None, single_event.body,401)        
        assert isinstance(r, responses.PushResponse)
        assert r.error_message == "Unauthorised. Please check your Project Id and API Key"
        assert r.event == single_event.body
        assert r.http_status_code == 401
         
        response_body = {
            "errors": [{ 
                "field": "fieldName", 
                "description": "There was an error with this field." 
            }]
        }
        
        r = self.connect._build_response(response_body, single_event.body, 422)
        assert isinstance(r, responses.PushResponse)
        assert r.error_message == [{ 
            "field": "fieldName", 
            "description": "There was an error with this field." 
        }]
        assert r.event == single_event.body
        assert r.http_status_code == 422
        
        response_body = {
            "errorMessage": "Maximum event size of 64kb exceeded."
        }
        
        r = self.connect._build_response(response_body, single_event.body, 413)
        assert isinstance(r, responses.PushResponse)
        assert r.error_message == "Maximum event size of 64kb exceeded."
        assert r.event == single_event.body
        assert r.http_status_code == 413

    def test__build_batch_response(self, post):
        response_body = {
            COLLECTION_NAME: [
                {
                    "success": True
                },
                {
                    "success": False,
                    "message": "An error occurred inserting the event please try again."
                }
            ],
            "my_collection2": [
                {
                    "success": True
                }
            ]
        }
        events = defaultdict(list)
        events["my_collection2"].append(SINGLE_EVENT_DATA)        
        events[COLLECTION_NAME] = [e for e in MULTI_EVENT_DATA]
        r = self.connect._build_batch_response(response_body,
                                               events,
                                               200)
        
        assert isinstance(r, responses.PushBatchResponse)
        assert r.http_status_code == 200
        assert r.error_message is None
        
        #to do: assert event body
        
        for collection in r.results:
            collection_results = r.results[collection]            
            
            for i in range(0, len(collection_results)):
                assert isinstance(collection_results[i], responses.PushResponse)
                assert collection_results[i].http_status_code is None
                
                if i == 1:
                    assert collection_results[i].success == False
                    assert collection_results[i].error_message == "An error occurred inserting the event please try again."
                    assert collection_results[i].event == MULTI_EVENT_DATA[1]
                else:
                    assert collection_results[i].success == True
                    assert collection_results[i].error_message is None 

        response_body = { "errorMessage": "An error occurred while processing your request"}
        r = self.connect._build_batch_response(response_body,
                                               events,
                                               500)
                                               
        assert r.http_status_code == 500
        assert r.error_message == "An error occurred while processing your request"
        assert r.results == {}

    def test_create_session(self, post):
        s = self.connect._create_session()
        assert isinstance(s,Session)
        assert s.headers["Content-Type"] == "application/json"
        assert s.headers["X-Api-Key"] == API_PUSH_KEY
        assert s.headers["X-Project-Id"] == PROJECT_ID 
    

class mocked_connect_response(object):
    """
    An object used to to mock a response from the Connect API. This is used in
    return values for mocked objects so that they can be tested
    """
    def __init__(self,status_code, body):
        self.status_code = status_code
        self._body = body
    
    def json(self):
        if self._body is not None:
            return self._body
        else:
            raise ValueError