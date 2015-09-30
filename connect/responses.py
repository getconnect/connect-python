# -*- coding: utf-8 -*-

class Respsonse(object):
    """
    Base object for storing responses from the Connect API
    """
    def __init__(self, status_code, error_message, success = None):    
        
        if success is not None:
            self.success = success
        else:
            self.success = status_code == 200
            
        self.http_status_code = status_code
        self.error_message =  error_message
        
class PushResponse(Respsonse):
    """
    Response for pushing a single event
    """
    
    def __init__(self, status_code, error_message, raw_event, success = None):
        super(PushResponse, self).__init__(status_code, error_message, success)
        self.event =  raw_event
    
class PushBatchResponse(Respsonse):
    """
    Response for pushing a batch of events
    """
    def __init__(self, status_code, error_message, results):
        super(PushBatchResponse, self).__init__(status_code, error_message, None)
        self.results = results