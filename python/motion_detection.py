#!/usr/bin/python

import BaseHTTPServer
import ConfigParser
import SocketServer
import datetime
import io
import json
import re
import socket
import threading
import time
from base64 import b64encode
from subprocess import call
from threading import Condition

import Image
import ephem
import numpy
import os
import picamera.array


class CameraSettings:
    def __init__(self, framerate, percentage_changed, exposure_mode='auto', shutter_speed=0, iso=0):
        self.percentage_changed = percentage_changed
        self.exposure_mode = exposure_mode
        self.shutter_speed = shutter_speed
        self.framerate = framerate
        self.iso = iso


class StreamingOutput(object):
    def __init__(self):
        self.last_frame = datetime.datetime.now()
        self.condition = Condition()
        self.screen = bytes()

    def write(self, frame):
        now = datetime.datetime.now()
        time_diff = (now - self.last_frame).microseconds
        if time_diff < 500000:
            return
        self.last_frame = now
        size = str(len(frame)).encode('utf-8')
        self.screen = b'Content-Type: image/jpeg\r\n' \
                      b'Content-Length: ' + size + b'\r\n\r\n' \
                      + frame + b'\r\n'
        self.condition.acquire()
        self.condition.notifyAll()
        self.condition.release()


class StreamingHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def is_authenticated(self):
        if not basic_auth:
            return True
        if not ('Authorization' in self.headers):
            return False
        authorization = self.headers['Authorization']
        return authorization in authorities

    def do_HEAD(self):
        self.send_response(200)

    def do_POST(self):
        if not self.is_authenticated():
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Test"')
            return

        self.send_header('Location', '/blacklist.html')
        self.end_headers()
        self.wfile.write(b'HTTP/1.0 200 OK\r\n')

    def do_GET(self):
        global force_motion, camera_settings

        if not self.is_authenticated():
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Test"')
            return

        if self.path == '/live' or self.path == '/live.mjpeg':
            self.stream_mjpeg()

        elif self.path == '/live.jpg':
            self.wfile.write(b'HTTP/1.0 200 OK\r\n')
            self.wfile.write(output.screen)

        elif self.path == '/events':
            self.show_events()

        elif self.path.endswith('.mp4') and os.path.exists(event_folder + self.path):
            self.serve_file(filename=event_folder + self.path, content_type='video/mp4')

        elif self.path.endswith('.jpg') and os.path.exists(event_folder + self.path):
            self.serve_file(filename=event_folder + self.path, content_type='image/jpg')

        elif self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/live.mjpeg')
            self.end_headers()

        elif self.path == '/force_motion':
            force_motion = True
            self.send_response(200)

        elif self.path == '/stop_force_motion':
            force_motion = False
            self.send_response(200)

        elif self.path == '/nightmode':
            if not night_mode_active and night_mode_allowed:
                camera_settings = night_settings
            self.send_response(200)

        elif self.path == '/daymode':
            if night_mode_active:
                camera_settings = day_settings
            self.send_response(200)

        elif self.path == '/blacklist.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(web_folder + '/blacklist.html') as htmlFile:
                content = htmlFile.read()
                data_exists = os.path.exists(roi_file)
                content = content.replace('${data-exists}', str(data_exists))
                if data_exists:
                    with open(roi_file) as roi:
                        content = content.replace('${data-current}', roi.read())
                else:
                    content = content.replace('${data-current}', '')
                self.wfile.write(content)

        elif self.path.endswith('.css'):
            self.serve_file(filename=web_folder + self.path, content_type='text/css')

        elif self.path.endswith('.js'):
            self.serve_file(filename=web_folder + self.path, content_type='application/javascript')

        elif self.path == '/delete':
            # TODO: delete video + preview
            pass

        else:
            self.send_error(404)
            self.end_headers()

    def stream_mjpeg(self):
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
        self.send_header('Cache-Control', 'no-cache, private')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Age', 0)
        self.end_headers()

        while True:
            try:
                self.wfile.write(b'--FRAME\r\n')
                self.wfile.write(output.screen)
                output.condition.acquire()
                output.condition.wait()
                output.condition.release()
            except:
                break

    def show_events(self):
        events = []
        videos = os.listdir(event_folder)
        for video in videos:
            if not video.endswith('.mp4'):
                continue
            video_file = os.path.join(event_folder, video)
            events.append({
                'video': '/' + video,
                'size': os.stat(video_file).st_size,
                'date': video[:19],
                'duration': int(video[20:][:-4]),
                'poster': '/' + video[:19] + '.jpg'
            })
        self.serve_json(payload=events)

    def serve_json(self, payload):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload))

    def serve_file(self, filename, content_type):
        f = open(filename, 'rb')
        range_request = False
        if 'Range' in self.headers:
            self.send_response(206)
            range_request = True
        else:
            self.send_response(200)
        size = os.stat(filename).st_size
        start_range = 0
        end_range = size
        if range_request:
            s, e = self.headers['range'][6:].split('-', 1)
            sl = len(s)
            el = len(e)
            if sl > 0:
                start_range = int(s)
                if el > 0:
                    end_range = int(e) + 1
            elif el > 0:
                ei = int(e)
                if ei < size:
                    start_range = size - ei
            self.send_header('Content-Range', 'bytes ' + str(start_range) + '-' + str(end_range - 1) + '/' + str(size))

        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-type', content_type)
        self.send_header('Content-Length', end_range - start_range)
        self.end_headers()
        f.seek(start_range, 0)
        chunk = end_range - start_range
        try:
            self.wfile.write(f.read(chunk))
        except:
            pass
        f.close()


class StreamingServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    stopped = False

    def serve_forever(self, poll_interval=0.5):
        while not self.stopped:
            self.handle_request()

    def force_stop(self):
        self.stopped = True
        self.server_close()


class MotionDetection(object):
    def __init__(self):
        self.temp_resolution = (192, 108)
        self.seconds_before_event = 2
        self.detect_motion = False
        self.prev_temp_img = None
        self.motion_stream = None
        self.bitrate = 3000000
        self.motion_index = 0
        self.preview_port = 3
        self.motion_port = 1

    def __notify_socket(self, action):
        if not socket_notification_enabled:
            return
        try:
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(2)
            address = (socket_host, socket_port)
            connection.connect(address)
            payload = {'action': action, 'cameraId': socket_id}
            message = json.dumps(payload)
            connection.send(message)
            connection.close()
        except:
            pass

    def capture_temp_image(self):
        stream = io.BytesIO()
        camera.capture(stream, format='jpeg', resize=self.temp_resolution, splitter_port=self.preview_port, use_video_port=True)
        stream.seek(0)
        image = Image.open(stream)
        image_array = numpy.asarray(image)
        if not has_roi:
            return image_array[::, ::, 1]
        return image_array[roi_x, roi_y, 1]

    def has_motion(self):
        global force_motion
        if force_motion:
            return True
        current_temp_img = self.capture_temp_image()
        diff = (numpy.absolute(self.prev_temp_img.astype(numpy.int) - current_temp_img.astype(numpy.int)) > 22).sum()
        self.prev_temp_img = current_temp_img
        motion = diff >= motion_score
        if motion:
            print 'motion detected with score ', diff
        return motion

    def start(self):
        if self.detect_motion:
            return
        motion_thread = threading.Thread(target=self.__start)
        motion_thread.daemon = True
        motion_thread.start()

    def __start(self):
        print 'prepare motion detection ...'
        self.motion_stream = picamera.PiCameraCircularIO(camera, seconds=self.seconds_before_event, bitrate=self.bitrate, splitter_port=self.motion_port)
        camera.start_recording(self.motion_stream, format='h264', splitter_port=self.motion_port, bitrate=self.bitrate)
        self.detect_motion = True
        camera.wait_recording(3, splitter_port=self.motion_port)
        print 'ready for motion detection. start motion detection'
        self.prev_temp_img = self.capture_temp_image()

        while self.detect_motion:
            camera.wait_recording(0.5, splitter_port=self.motion_port)
            if self.has_motion():
                print 'new motion event'
                threading.Thread(target=self.__notify_socket, kwargs={'action': 'motion-started'}).start()
                self.motion_index += 1
                current_framerate = camera.framerate
                filename_before = str(self.motion_index) + '_before_' + str(current_framerate) + '.h264'
                filename_after = str(self.motion_index) + '_after_' + str(current_framerate) + '.h264'
                f1_temp = os.path.join(temp_folder, filename_before)
                f2_temp = os.path.join(temp_folder, filename_after)
                f1 = os.path.join(output_folder, filename_before)
                f2 = os.path.join(output_folder, filename_after)

                camera.split_recording(f2_temp)
                self.motion_stream.copy_to(f1_temp)
                self.motion_stream.clear()

                camera.wait_recording(3, splitter_port=self.motion_port)
                while self.has_motion():
                    camera.wait_recording(5, splitter_port=self.motion_port)

                camera.split_recording(self.motion_stream, splitter_port=self.motion_port)
                os.rename(f1_temp, f1)
                os.rename(f2_temp, f2)
                print 'motion event stopped'
                threading.Thread(target=self.__notify_socket, kwargs={'action': 'motion-stopped'}).start()
                call('bash ' + convert_script, shell=True)
        camera.stop_recording(splitter_port=self.motion_port)

    def stop(self):
        if not self.detect_motion:
            return
        print 'stop motion detection'
        self.detect_motion = False


class Server(object):
    def __init__(self):
        self.server = StreamingServer(('', webserver_port), StreamingHandler)
        self.start()

    def start(self):
        print 'start server'
        thread = threading.Thread(target=self.__start)
        thread.daemon = True
        thread.start()

    def __start(self):
        self.server.serve_forever()

    def stop(self):
        print 'stop server'
        self.server.force_stop()


class MjpegStreamer(object):
    def __init__(self):
        self.streaming_port = 2
        self.streaming = False

    def start(self):
        mjpeg_thread = threading.Thread(target=self.__start)
        mjpeg_thread.daemon = True
        mjpeg_thread.start()

    def __start(self):
        if self.streaming:
            return
        print 'start mjpeg streamer'
        self.streaming = True
        camera.start_recording(output, format='mjpeg', splitter_port=self.streaming_port)

    def stop(self):
        if not self.streaming:
            return
        print 'stop mjpeg streamer'
        camera.stop_recording(splitter_port=self.streaming_port)


def check_for_camera_settings_switch():
    global last_mode_check, night_mode_active, camera_settings
    if not night_mode_allowed:
        return
    now = datetime.datetime.now()
    if (now - last_mode_check).seconds < 300:
        return
    print 'check for camera settings switch'
    last_mode_check = now
    sunrise = location.next_rising(ephem.Sun())
    sunset = location.next_setting(ephem.Sun())
    if sunset < sunrise:
        if night_mode_active:
            print 'activate day mode'
            night_mode_active = False
            camera_settings = day_settings
    elif not night_mode_active:
        print 'activate night mode'
        night_mode_active = True
        camera_settings = night_settings


def change_camera_settings():
    global camera_settings, motion_score
    print 'change camera settings'

    motion_detection.stop()
    mjpeg_streamer.stop()

    while camera.recording:
        time.sleep(2)

    camera.exposure_mode = camera_settings.exposure_mode
    camera.shutter_speed = camera_settings.shutter_speed
    camera.framerate = camera_settings.framerate
    camera.iso = camera_settings.iso

    if has_roi:
        total_pixels = len(roi_x)
    else:
        total_pixels = motion_detection.temp_resolution[0] * motion_detection.temp_resolution[1]

    motion_score = int(total_pixels / 100 * camera_settings.percentage_changed)
    print 'detect motion with motion_score ', motion_score

    camera_settings = None

    motion_detection.start()
    mjpeg_streamer.start()


def fetch_region_of_interest():
    global roi_x, roi_y, has_roi

    print 'fetch region of interest.'
    if not os.path.exists(roi_file):
        print 'no region of interest defined. detect motion on whole area.'
        return

    roi = open(roi_file, mode='r')
    roi_content = roi.readline()
    roi.close()

    x = []
    y = []

    for element in roi_content.split(', '):
        match = re.search("(\d*),(\d*)", element)
        x.append(int(match.group(1)))
        y.append(int(match.group(2)))

    if len(x) == 0:
        return

    has_roi = True
    roi_x = numpy.asarray(x)
    roi_y = numpy.asarray(y)


def write_default_value(section, option, value):
    if not config.has_section(section):
        config.add_section(section)

    if not config.has_option(section, option):
        config.set(section, option, value)


def setup_default_configuration():
    write_default_value(section='motion_detection', option='night_mode_allowed', value='False')
    write_default_value(section='location', option='latitude', value='0.0')
    write_default_value(section='location', option='longitude', value='0.0')
    write_default_value(section='camera', option='saturation', value='20')
    write_default_value(section='camera', option='sharpness', value='20')
    write_default_value(section='camera', option='rotation', value='0')
    write_default_value(section='webserver', option='port', value='8080')
    write_default_value(section='basic_auth', option='enabled', value='True')
    write_default_value(section='socket_notification', option='enabled', value='False')
    write_default_value(section='socket_notification', option='host', value='127.0.0.1')
    write_default_value(section='socket_notification', option='port', value='25000')
    write_default_value(section='socket_notification', option='id', value='motiondetection')

    if not config.has_section('users'):
        write_default_value(section='users', option='username', value='password')

    with open(config_file, mode='w') as configfile:
        config.write(configfile)


def setup_users():
    for username in config.options('users'):
        password = config.get('users', username)
        authorities.append('Basic ' + b64encode(username + ':' + password))


if __name__ == '__main__':
    print 'started'
    directory = os.path.dirname(__file__)

    config_file = os.path.join(directory, 'config.ini')
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    authorities = []
    setup_default_configuration()
    setup_users()
    night_mode_allowed = config.getboolean(section='motion_detection', option='night_mode_allowed')
    latitude = config.getfloat(section='location', option='latitude')
    longitude = config.getfloat(section='location', option='longitude')
    day_settings = CameraSettings(framerate=15, percentage_changed=0.4)
    night_settings = CameraSettings(framerate=5, percentage_changed=1, exposure_mode='off', shutter_speed=200000, iso=1600)
    webserver_port = config.getint(section='webserver', option='port')
    basic_auth = config.getboolean(section='basic_auth', option='enabled')

    socket_notification_enabled = config.getboolean(section='socket_notification', option='enabled')
    socket_host = config.get(section='socket_notification', option='host')
    socket_port = config.getint(section='socket_notification', option='port')
    socket_id = config.get(section='socket_notification', option='id')

    last_mode_check = datetime.datetime.min
    night_mode_active = False
    location = ephem.Observer()
    location.lat, location.long = latitude, longitude
    location.horizon = '-6'
    force_motion = False
    camera_settings = day_settings
    output = StreamingOutput()
    has_roi = False
    roi_x = None
    roi_y = None
    motion_score = None

    roi_file = os.path.join(directory, 'roi.txt')
    output_folder = os.path.join(directory, 'unconverted')
    fail_folder = os.path.join(directory, 'unconverted_fail')
    event_folder = os.path.join(directory, 'events')
    web_folder = os.path.join(directory, '../web')
    temp_folder = os.path.join(directory, 'temp')
    convert_script = os.path.join(directory, '../scripts', 'convert_cron.sh')

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    if not os.path.exists(event_folder):
        os.mkdir(event_folder)
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)
    if not os.path.exists(fail_folder):
        os.mkdir(fail_folder)

    camera = picamera.PiCamera(framerate=day_settings.framerate, sensor_mode=2, resolution=(1920, 1080))
    camera.saturation = config.getint(section='camera', option='saturation')
    camera.sharpness = config.getint(section='camera', option='sharpness')
    camera.rotation = config.getint(section='camera', option='rotation')

    fetch_region_of_interest()

    mjpeg_streamer = MjpegStreamer()
    motion_detection = MotionDetection()
    server = Server()

    try:
        while threading.active_count > 0:
            time.sleep(1)
            check_for_camera_settings_switch()
            if camera_settings:
                change_camera_settings()
    except:
        pass
    finally:
        motion_detection.stop()
        mjpeg_streamer.stop()
        server.stop()
        camera.close()
        print 'stopped'
