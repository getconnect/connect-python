from connect.client import ConnectClient

connect = ConnectClient(project_id="YOUR_PROJECT_ID", 
                 api_key="YOUR_PUSH_KEY")

event = {
  'type': 'cycling',
  'distance': 21255,
  'caloriesBurned': 455,
  'duration': 67,
  'Paid': 1,
  'user': {
    'id': '638396',
    'name': 'Bruce'
 }
}

events = {
    "dev-collection": [{
        'type': 'cycling',
        'distance': 21255,
        'caloriesBurned': 455,
        'duration': 67,
        'user': {
            'id': '638396',
            'name': 'Bruce'
        }
    }, {
        'type': 'swimming',
        'distance': 21255,
        'caloriesBurned': 455,
        'duration': 67,
        'user': {
            'id': '638396',
            'name': 'Bruce',
        }
    }]
}

future_single = connect.push_event("dev-collection",event)
future_batch = connect.push_events(events)

#single event returns http status and any error messages
r = future_single.result()
print r.success
print r.error_message
print r.http_status_code
print r.event

#batch event push returns list of events push with status
r = future_batch.result()
print r.success
print r.error_message
print r.http_status_code
print r.results