# -*- coding: utf-8 -*-
import uuid
import copy
from datetime import datetime

from connect import exceptions


class Event(object):
    """
    Event is the object used to validate and process event data before
    sending it to the Connect API
    """    
    
    def __init__ (self,collection_name,event_data):
        if not isinstance(event_data,dict):
            raise exceptions.InvalidEventError("Event must be a dict object")
        
        if not "id" in event_data:
            event_data["id"] = str(uuid.uuid4())
        
        if not "timestamp" in event_data:
            event_data["timestamp"] = datetime.utcnow()
            
        self.body = self._process(event_data)
        self.collection_name = collection_name
        self.error = None

    def _process(self, event_data):
        """ 
        Checks if an event is valid for Connect and returns processed event
        that is safe to send to connect.
        Raises InvalidEventError if the event is invalid 
           
        :param event_data: dictionary with data for the event
        """
        errors = dict()        
        for k in list(event_data.keys()):
            try:
                if k.lower().startswith("tp_"): 
                    errors[k] = ("Property names cannot start with the" + 
                                 "reserved prefix 'tp_'")
                elif k.lower() == '_id': 
                    errors[k] = "Top level properties cannot be named '_id'"
            except AttributeError:
                pass # non string value being used for key value
        event_copy = copy.deepcopy(event_data)        
        processed_event, errors = self._validate_and_process_nested(
                                    event_copy, errors)
        if not hasattr(event_data["timestamp"], "date"):
            errors["timestamp"] = "timestamp property must be a datetime"
        if len(errors) > 0:
            raise exceptions.InvalidEventError(errors) 
            
        return processed_event
       
    def _validate_and_process_nested(self, event_data, errors):
        """
        Recursively searches the dictionary for bad property names and converts
        dates to isoformated strings
        
        returns 
            errors dict appended with new errors
            eventdata dict with dates converted to iso strings
        
        :param event_data: dict with data for the event
        :param errors: dict of errors found so far
        """
        for k,v in event_data.items():
            try:            
                if "." in k:
                    errors[k] = "Property names cannot contain a period (.)"
                elif k.startswith("$"):
                    errors[k] = "Property names cannot start with $"
                elif len(k) > 255:
                    errors[k] = "Property names cannot exceed 255 characters"
            except TypeError:
                pass
                
            if hasattr(v, "isoformat"):
                event_data[k] = v.isoformat()                                
            if isinstance(v, (dict)):
                self._validate_and_process_nested(v, errors)

        return event_data, errors 