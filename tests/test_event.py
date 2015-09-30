# -*- coding: utf-8 -*-
from mock import patch
from datetime import datetime

import pytest

from connect import exceptions
from connect.event import Event

COLLECTION_NAME = 'my_collection'
   
def test_init():
    event = {'data' : 'some data'}
    connect_event = Event(COLLECTION_NAME, event)
    
    assert connect_event.body is not None
    assert connect_event.collection_name == COLLECTION_NAME
    assert connect_event.body["id"] is not None
    assert connect_event.body["timestamp"] is not None
    assert connect_event.error is None
 
def test_non_dict_object_raises_exception():
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, "a string")

def test_id_root_event_property_raises_exception():
    bad_event = {'_id' : 1, 'data' : 'some data'}

    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)
 
def test_tp_root_event_property_raises_exception():
    bad_event = {'tp_a' : 1, 'data' : 'some data'}
    
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)

def test_dot_in_root_event_property_raises_exception():
    bad_event = {
    'type': 'cycling',
    'user': {
        'id': '638396',
        'firstname': 'Bruce'
        },
    'my.status':True
    }
    
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)
                       
def test_dot_in_nested_event_property_raises_exception():
    bad_event = {
    'type': 'cycling',
    'user': {
        'id': '638396',
        'first.name': 'Bruce'
        },
    'caloriesBurned': 455,
    }
    
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)

def test_properties_names_greater_than_255_characters_raises_exception():
    bad_event = {
    'Y91easBbi0COyGRyScJAuJ4tfm9TQFUfANcVovhVPEavGZLauTaRV5GFqyqXu6CtFRUREffsEtzv91O9SAmWA6zGoATcnMPsvOiQtz0qmxR2xGC31ggeuNu2oQMwPXx4ouxuN4GBEe6EhRtUsDgEvrALpPO2DVL7k6awhF87VB41XOrFkzS4pDoDzaKhvY063esrY9ymboAY9Tk4n2tC6WqUwsQxqfxlGCkzSr8w6iGjjv6DE7nNuvlYUkpA3xEj': 'cycling',
    'user': {
        'id': '638396',
        'first.name': 'Bruce'
        },
    'caloriesBurned': 455,
    }
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)

def test_root_properties_starting_with_dollar_character_raises_exception():
    bad_event = {
        'type': 'cycling',
        '$user': {
            'id': '638396',
            'first.name': 'Bruce'
            },
        'caloriesBurned': 455,
        }
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)

def test_nested_properties_starting_with_dollar_character_raises_exception():        
    bad_event = {
        'type': 'cycling',
        'user': {
            '$id': '638396',
            'first.name': 'Bruce'
            },
        'caloriesBurned': 455,
        }
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)

def test_non_datetime_type_in_timestamp_property_raises_exception():
    bad_event = {'data' : 'some data',
                 'timestamp': '2015-01-01'}
    with pytest.raises(exceptions.InvalidEventError):
        Event(COLLECTION_NAME, bad_event)          

def test_root_datetime_properties_converted_to_iso_string():
        event = {'data':'some_data',
                 'timestamp' : datetime(2015,8,1)
                }
        e = Event(COLLECTION_NAME, event)
        
        assert isinstance(e.body["timestamp"], str)
        assert e.body["timestamp"] == "2015-08-01T00:00:00"

def test_nested_datetime_properties_converted_to_iso_string():
    event = {
    'type': 'cycling',
    'user': {
        'id': '638396',
        'firstname': 'Bruce',
        'dateOfBirth': datetime(1965,5,9)
        },
    'caloriesBurned': 455,
    }
    e = Event(COLLECTION_NAME, event)       
    actual_value = e.body["user"]["dateOfBirth"]
    expected_value = "1965-05-09T00:00:00"
    assert isinstance(e.body["timestamp"], str)
    assert actual_value == expected_value

def test_generated_timestamp_is_datetime_iso_string():
    with patch("connect.event.datetime") as mock_datetime:
        event = {'data':'some_data'}
        timestamp = datetime(1965,5,9)
        mock_datetime.utcnow.side_effect = [timestamp]        
        e = Event(COLLECTION_NAME, event)
        actual_value = e.body["timestamp"]
        expected_value = timestamp.isoformat()
        
        assert mock_datetime.utcnow.call_count == 1
        assert expected_value == actual_value

def test_id_not_generated_if_supplied():
    with patch("uuid.uuid4") as mock_uuid:
        test_event = {'data':'some_data',
                'id' : 1 }
        Event(COLLECTION_NAME, test_event)
        
        assert not mock_uuid.called

def test_generated_id_is_uuid():
    with patch("uuid.uuid4") as mock_uuid:
       test_event = {'data':'some_data'}
       e = Event(COLLECTION_NAME, test_event)
       assert "id" in e.body
       assert mock_uuid.called

def test_process():
    test_event = {'data':'some_data'}
    e = Event(COLLECTION_NAME, test_event)
    event_data = e._process(test_event)
    assert isinstance(event_data, dict)
    
def test_validate_and_process_nested():
    event_nested_dot = {
        'type': 'cycling',
        'user': {
            'id': '638396',
            'first.name': 'Bruce'
            },
        'caloriesBurned': 455,
    }
    
    good_event = {"data":"some_data"}
    e = Event(COLLECTION_NAME, good_event)
    errors = {}
    event_data, errors = e._validate_and_process_nested(event_nested_dot, errors)
    assert isinstance(event_data, dict)
    assert isinstance(errors, dict)
    assert event_data == event_nested_dot
    assert errors["first.name"] is not None       

def test_int_dict_keys_do_not_raise_execption():
    e = Event(COLLECTION_NAME, {1 : "some data"})
    assert isinstance(e, Event)    