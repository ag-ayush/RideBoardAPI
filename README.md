# RideBoard API
[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Build Status](https://travis-ci.org/ag-ayush/RideBoardAPI.svg?branch=master)](https://travis-ci.org/ag-ayush/RideBoardAPI)

A RESTful API for [CSH Rideboard](https://github.com/ag-ayush/rides) application. An API key is **_required_** to use the API.


## Field Descriptions

### Event:

Field | Description
------|------------
`id` | _The event's unique id._
`name` | _Name of the event_
`creator` | _Username of the person who created the event_
`cars` | _JSON Formatted list of cars in the event_
`start_time` | _Time when the event will start in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`end_time` | _Time when the event will end in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`open_seats` | _Number of available seats in all the cars in the event_

### Cars:

Field | Description
------|------------
`ride_id` | _The car's unique id._
`current_capacity` | _Number of people in the car currently_
`max_capacity` | _Maximum number of seats available _
`departure_time` | _Time when the person will leave in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`return_time` | _Time when the person will return in following python datetime format: '%a, %d %b %Y %H:%M:%S %Z'_
`name` | _Name of the driver_
`username` | _CSH username of the driver_
`driver_comment` | _Comments provided by the driver_
`riders` | _List of usernames currently signed up in the car_


## `/<api_key>/all` : `GET`

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


## `/<api_key>/upcoming` : `GET`

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


## `/<api_key>/join/<car_id>/<username>/<first_name>/<last_name>` : `PUT`

_User joins a provided car and the event in relation to the car is returned as JSON._

**Required Parameters: `car_id`,`username`,`first_name`,`last_name`**


## `/<api_key>/leave/<car_id>/<username>` : `PUT`

_User leaves the car and the event in relation to the car is returned as JSON._

**Required Parameters: `car_id`, `username`**


## `/<api_key>/create/event` : `POST`

_Creates an event, returns the resulting event as JSON._

**Required Parameters: JSON Object, `driver_comment` is optional.**

```json
{
  "name": "Testing 12",
  "address":"NEW ADDRESS",
  "start_time":"Thu, 09 Aug 2018 06:13:00",
  "end_time":"Fri, 10 Aug 2018 06:13:00",
  "creator":"agoel",
  "driver_comment": "None."
 }
```


## `/<api_key>/create/car/<event_id>` : `POST`

_Creates a car in the provided event_id and returns the resulting event as JSON._

**Required Parameters: JSON Object**

```json
{
    "name": "First Last",
    "username":"user",
    "departure_time":"Thu, 02 Aug 2018 06:13:00",
    "return_time":"Thu, 09 Aug 2018 06:13:00",
    "max_capacity":2,
}
```


## `/generatekey/<reason>` : `GET`

_Generates an unique key, each of which has an unique owner/reason pair. This action can only be done by an RTP or myself._

**Required Parameter: `reason`**

Sample Output: 96a2cea9c44c4f699947a3e8e186f036


## `/listapikeys` : `GET`

_Lists all the keys in the database for RTP's and selected users as a JSON list._

Sample Output:

```json
[
  {
    "hash": "96a2cea9c44c4f699947a3e8e186f036", 
    "id": 54, 
    "owner": "agoel", 
    "reason": "For local testing."
  }, 
  {
    "hash": "069db6062ae999d0806baaa9df40d1dd", 
    "id": 55, 
    "owner": "agoel", 
    "reason": "I am testing key sets."
  }
]
```