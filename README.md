# RideBoard API

A RESTful API for [CSH Rideboard](https://github.com/ag-ayush/rides) application.


## Field Descriptions

### Event:
Field | Description
------|------------
`id` | _The event's unique id._
`name` | _name of the event_
`creator` | _username of the person who created the event_
`cars` | _JSON Formatted list of cars in the event_
`start_time` | _Time when the event will start in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`end_time` | _Time when the event will end in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`open_seats` | _number of available seats in all the cars in the event_

### Cars:
Field | Description
------|------------
`ride_id` | _The car's unique id._
`current_capacity` | _Number of people in the car currently_
`max_capacity` | _Maximum number of seats available _
`departure_time` | _Time when the person will leave in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`return_time` | _Time when the person will return in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`name` | _name of the driver_
`username` | _CSH username of the driver_
`driver_comment` | _Comments provided by the driver_
`riders` | _list of usernames currently signed up in the car_


## `/all` : `GET`
_Returns all current events in the following JSON __list__ format:_

```json
[
  {
    "address": "address", 
    "cars": [
      {
        "current_capacity": 0, 
        "departure_time": "Thu, 02 Aug 2018 06:13:00 GMT", 
        "driver_comment": "", 
        "id": 80, 
        "max_capacity": 0, 
        "name": "Need a Ride", 
        "return_time": "Thu, 09 Aug 2018 06:13:00 GMT", 
        "ride_id": 43, 
        "riders": ["agoel", "red"], 
        "username": "∞"
      }
    ], 
    "creator": "creator", 
    "end_time": "Thu, 09 Aug 2018 06:13:00 GMT", 
    "id": 43, 
    "name": "Event Name", 
    "open_seats": 2, 
    "start_time": "Thu, 02 Aug 2018 06:13:00 GMT"
  }
]
```

**Allowed Parameters: `id`**

Example request: `/all?id=41`


## `/upcoming` : `GET`
_Returns the event with the earliest start date in the following format:_

```json
{
  "address": "Addresss", 
  "cars": [
    {
      "current_capacity": 0, 
      "departure_time": "Tue, 31 Jul 2018 08:06:00 GMT", 
      "driver_comment": "", 
      "id": 84, 
      "max_capacity": 0, 
      "name": "Need a Ride", 
      "return_time": "Thu, 09 Aug 2018 08:06:00 GMT", 
      "ride_id": 46, 
      "riders": ["agoel", "red"], 
      "username": "∞"
    }
  ], 
  "creator": "agoel", 
  "end_time": "Thu, 09 Aug 2018 08:06:00 GMT", 
  "id": 46, 
  "name": "Event 3", 
  "open_seats": 0, 
  "start_time": "Tue, 31 Jul 2018 08:06:00 GMT"
}
```


## `/join/<car_id>/<username>/<first_name>/<last_name>/` : `GET`
_User joins a provided car and the event in relation to the car is returned._

**Required Parameters: `car_id`,`username`,`first_name`,`last_name`**