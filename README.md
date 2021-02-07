# Simple Python Robot SDK

A simple Python3 library to manage the states of servomotors and sensor in a robot. Currently, is possible to use socket
to get a real-time JSON dump of robot servomotors and sensor.

### Example:

```python
import simplepybotsdk
from time import sleep

robot = simplepybotsdk.RobotSocketSDK(
    config_path="robot_configuration.json",
    socket_host="127.0.0.1",
    socket_port=8090
)

mot1 = robot.get_motor("head_z")
mot2 = robot.get_motor("l_elbow_y")

print("Try to establish a socket communication to receive updates in real-time")
print("See how in the 'examples/' folder.")

sleep(4)
mot1.set_goal_angle(75)
sleep(2)
mot2.set_goal_angle(-45)

```

### Example of robot configuration:

```
{
  "id": "Readme_robot",
  "version": "0.1",
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
    "l_elbow_y": {
      "id": "10",
      "offset": 0.0,
      "type": "virtual-servo",
      "angle_limit": [
        -10,
        125
      ],
      "orientation": "direct"
    },
    "r_elbow_y": {
      "id": "11",
      "offset": 0.0,
      "type": "virtual-servo",
      "angle_limit": [
        -10,
        125
      ],
      "orientation": "indirect"
    }
  }
}
```
