# Simple Python Robot SDK

A simple Python3 library to manage the states of servomotors and sensor in a robot.

Currently, is possible to use websocket to get a real-time JSON dump of robot servomotors and sensors.
There are also webservices to change servomotors goal angle.

A development dashboard is available here to see all servomotors moving: 
[SimplePYBotDashboard](https://github.com/vellons/SimplePYBotDashboard).


### Example:

```python
import simplepybotsdk
from time import sleep

robot = simplepybotsdk.RobotRESTSDK(
    config_path="robot_configuration.json",
    socket_host="localhost",
    socket_port=65432,
    rest_host="localhost",
    rest_port=8000
)
robot.rest_configure()
robot.rest_serve_forever()  # This start an independent thread 

mot1 = robot.get_motor("head_z")
mot2 = robot.get_motor("l_shoulder_x")

print("Try to establish a socket communication to receive updates in real-time")
print("See how in the 'examples/' folder.")
print("Or try the dashboard to see all servomotors moving")

sleep(4)
mot1.set_goal_angle(75)
sleep(2)
mot2.set_goal_angle(-45)
sleep(2)

ptp = {
    "head_z": -45,
    "l_shoulder_x": 170,
    "r_shoulder_x": 150
}
robot.move_point_to_point(ptp, 8, blocking=True) # Move all motors in 8 seconds

robot.go_to_pose("standby", 10) # Go to standby position (defined in json conf file)
```

### Example of robot configuration:

```
{
  "id": "example_robot",
  "version": "1",
  "name": "Example robot",
  "motors": {
    "head_z": {
      "id": "1",
      "offset": 90.0,
      "type": "virtual-servo",
      "angle_limit": [
        -75,
        75
      ],
      "orientation": "direct"
    },
    "l_shoulder_x": {
      "id": "10",
      "offset": 0.0,
      "type": "virtual-servo",
      "angle_limit": [
        -10,
        170
      ],
      "orientation": "direct"
    },
    "r_shoulder_x": {
      "id": "11",
      "offset": 0.0,
      "type": "virtual-servo",
      "angle_limit": [
        -10,
        170
      ],
      "orientation": "indirect"
    }
  },
  "motors_type": {
    "virtual-servo": {
      "angle_speed": 60
    }
  },
  "sensors": {
    "gyroscope_x": {
      "id": "gyroscope_x",
      "offset": 0.0
    },
    "gyroscope_y": {
      "id": "gyroscope_y",
      "offset": 0.0
    },
    "gyroscope_z": {
      "id": "gyroscope_z",
      "offset": 0.0
    }
  },
  "poses": {
    "standby": {
      "head_z": 0,
      "l_shoulder_x": 0,
      "r_shoulder_x": 0
    }
  }
}
```
