## Motion Detection

Build your own low cost security cam!

This is the backend, which is based on the python raspberry pi camera module interface [picamera](https://github.com/waveform80/picamera), for the coming soon iOS-App.
   
Please feel free to change and improve the code, this is my first python project.

### Features
- records in 1080p with low cpu usage
- records also a few seconds before the motion was detected
- creates a thumbnail of the event as preview for the video
- define areas which don't need to checked (e.g. a tree in the wind)
- optional nightmode with lower fps but much brighter videos 
- live view

### Requirements
- Raspberry Pi
- Camera Module

### Installation

Instructions for an installation on Raspbian Jessie Lite 

- **Install dependencies** 

```bash
sudo apt-get install python-imaging gpac libav-tools imagemagick git python-dev python-pip
sudo pip install pyephem numpy picamera
```

- **Clone this repository**

```bash
sudo git clone https://github.com/dneunkirch/motiondetection.git /etc/motiondetection
```

- **Create a symlink for the init script**

```bash
sudo ln -s /etc/motiondetection/scripts/startup.sh /etc/init.d/motiondetection
```

- **Register the init script**

```bash
sudo update-rc.d motiondetection defaults
```

Now you're able to start/stop the motion detection with the command `sudo service motiondetection {start|stop}`. The motion detection starts also automatically at startup.

- **Configuration-File**

`/etc/motiondetection/python/config.ini` 

---

###URLs

####Captured Videos
`http://{host}:8080/events`

Returns an array of all captured videos as following object:

```js
{
  "date": "yyyy-MM-dd_HH-mm-ss",           // date of video
  "video": "/motion/events/video.mp4",     // path to video
  "poster": "/motion/events/preview.jpg",  // path to preview image
  "size": 1000000,                         // size of video in bytes
  "duration": 10                           // duration of video in seconds
}
```
With the request-parameter previewImageSize (default: 640x360) you're able to control the preview image resolution (e.g. /events.php?previewImageSize=320x180).  


####Live MJPEG stream
`http://{host}:8080/live` or `http://{host}:8080/live.mjpeg`

####Delete an event
`http://{host}:8080/delete?file=filename_of_video.mp4`

A GET request to this endpoint deletes the given video including his preview images.

####Exclude areas from motion detection
`http://{host}/blacklist`

On this site you're able to exclude areas from motion detection. After a change of the areas you have to restart the motion detection (`sudo service motiondetection restart`).

---

###For testing and debugging

####Fake Motion
`http://{host}:8080/force_motion`

####Stop Faking Motion
`http://{host}:8080/stop_force_motion`

####Activate Nightmode
`http://{host}:8080/nightmode`

Works only if `night_mode_allowed` in the config is `True`

####Activate Daymode
`http://{host}:8080/daymode`

---

####Todo's
- [ ] submit iOS-App to App-Store
- [ ] create a web-App
- [ ] write tests
