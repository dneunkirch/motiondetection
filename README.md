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
sudo apt-get install python-picamera python-imaging gpac libav-tools imagemagick git python-dev python-pip
sudo pip install pyephem numpy
```

- **If you don't have a webserver with PHP** *(optional)* **:**

```bash
sudo apt-get install nginx php5-fpm
```

Edit the file `/etc/nginx/sites-available/default` and paste the following snippet in the section `location / { ... }`

```json:
location ~ .php$ {
  fastcgi_split_path_info ^(.+\.php)(/.+)$;
  fastcgi_pass unix:/var/run/php5-fpm.sock;
  fastcgi_index index.php;
  include fastcgi.conf;
}
```

- **Clone this repository**

```bash
sudo git clone https://github.com/dneunkirch/motiondetection.git /etc/motiondetection
```

- **Check if the folders in the file `/etc/motiondetection/scripts/setup.sh` matches to yours**

- **Create a symlink for the init script**

```bash
sudo ln -s /etc/motiondetection/scripts/startup.sh /etc/init.d/motiondetection
```

- **Register the init script**

```bash
sudo update-rc.d motiondetection defaults
```

Now you're able to start/stop the motion detection with the command `sudo service motiondetection {start|stop}`. The motion detection starts also automatically at startup.

---

###URLs

####Captured Videos
`http://{host}/motion/events.php`

Returns an array of all captured videos as following object:

```js
{
  "date": "dd.MM.yyyy - HH:mm:ss",        // date of video
  "video": "/motion/events/video.mp4",    // path to video
  "image": "/motion/events/preview.jpg",  // path to preview image
  "size": 1000000,                        // size of video in bytes
  "duration": 10                          // duration of video in seconds
}
```
With the request-parameter previewImageSize (default: 640x360) you're able to control the preview image resolution (e.g. /events.php?previewImageSize=320x180).  


####Current live picture
`http://{host}/motion/live.php`

Returns the newest image as following object: 

```js
{
  "url": "/motion/live/image.jpg", // path to image
  "date": "dd.MM.yyyy - HH:mm:ss"  // date of image
}
```

####Delete an event
`http://{host}/motion/delete.php?file=filename_of_video.mp4`

A GET request to this endpoint deletes the given video including his preview images.

####Exclude areas from motion detection
`http://{host}/motion/blacklist.php`

On this site you're able to exclude areas from motion detection. After a change of the areas you have to restart the motion detection (`sudo service motiondetection restart`).

---

####Todo's
- [ ] submit iOS-App to App-Store
- [ ] create a web-App
- [ ] write tests
