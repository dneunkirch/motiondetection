#!/usr/bin/python

import datetime
import io
import logging
import os
import re
import threading
import time
from subprocess import call

import Image
import ephem
import numpy
import picamera.array


class CameraSettings:
    def __init__(self, framerate, percentage_changed, exposure_mode='auto', shutter_speed=0, iso=0):
        self.framerate = framerate
        self.exposure_mode = exposure_mode
        self.shutter_speed = shutter_speed
        self.iso = iso
        self.percentage_changed = percentage_changed


night_settings = CameraSettings(framerate=2,
                                percentage_changed=float(os.getenv('MOTION_SCORE_NIGHT', '1')),
                                exposure_mode='off',
                                shutter_speed=500000,
                                iso=1600)

day_settings = CameraSettings(framerate=15,
                              percentage_changed=float(os.getenv('MOTION_SCORE_DAY', '0.4')))

width = 1920
height = 1080

roi_x = None
roi_y = None
motion_score = None
prev_temp_img = None
sensor_mode = 2
seconds_before_event = 3
bitrate = 3000000
live_quality = 5
motion_timeout = 0.5
night_mode_active = False
resolution = (width, height)

temp_width = 192
temp_height = 108
temp_resolution = (temp_width, temp_height)

temp_folder = os.environ['MOTION_TEMP']
output_folder = os.environ['MOTION_OUTPUT']
live_folder = os.environ['MOTION_LIVE']
script_folder = os.environ['MOTION_SCRIPTS']

night_mode_allowed = os.getenv('MOTION_NIGHT_MODE_ALLOWED', 'True') == 'True'
last_mode_check = datetime.datetime.min
latitude = os.getenv('MOTION_LOCATION_LATITUDE', '0.0')
longitude = os.getenv('MOTION_LOCATION_LONGITUDE', '0.0')

live_timeout = int(os.getenv('MOTION_LIVE_REFRESH_INTERVAL_SECONDS', '5'))

roi_file = blacklist_file = os.environ['MOTION_WEB'] + 'roi.txt'
has_roi = False

trigger_convert_cmd = 'bash ' + script_folder + 'convert_cron.sh'

camera = picamera.PiCamera(framerate=day_settings.framerate, sensor_mode=sensor_mode, resolution=resolution)

logging.basicConfig(filename='/var/log/motiondetection.log', level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s - %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")


def update_live_pic():
    base = live_folder + time.strftime('%Y-%m-%d_%H-%M-%S')
    picture_temp = base + ".temp"
    picture = base + ".jpg"
    camera.capture(picture_temp, format='jpeg', quality=live_quality, splitter_port=2, use_video_port=True)
    os.rename(picture_temp, picture)
    threading.Timer(live_timeout, update_live_pic).start()


def change_camera_settings(settings):
    global motion_score
    if camera.recording:
        camera.stop_recording()
    camera.framerate = settings.framerate
    camera.exposure_mode = settings.exposure_mode
    camera.shutter_speed = settings.shutter_speed
    camera.iso = settings.iso
    new_stream = picamera.PiCameraCircularIO(camera, seconds=seconds_before_event, bitrate=bitrate, splitter_port=1)
    camera.start_recording(new_stream, format='h264', splitter_port=1, bitrate=bitrate)
    camera.wait_recording(2)

    if has_roi:
        total_pixels = len(roi_x)
    else:
        total_pixels = temp_width * temp_height

    motion_score = int(total_pixels / 100 * settings.percentage_changed)
    logging.info('detect motion with motion_score %d', motion_score)
    return new_stream


def check_for_camera_settings_switch(stream):
    if not night_mode_allowed:
        return stream

    global night_mode_active, last_mode_check

    now = datetime.datetime.now()
    if (now - last_mode_check).seconds < 300:
        return stream

    last_mode_check = now

    location = ephem.Observer()
    location.horizon = '-6'
    location.lat, location.long = latitude, longitude

    sunrise = location.next_rising(ephem.Sun())
    sunset = location.next_setting(ephem.Sun())

    if sunset < sunrise:
        if night_mode_active:
            logging.info('activate day mode')
            night_mode_active = False
            return change_camera_settings(day_settings)
    elif not night_mode_active:
        logging.info('activate night mode')
        night_mode_active = True
        return change_camera_settings(night_settings)

    return stream


def fetch_region_of_interest():
    global roi_x, roi_y, has_roi
    logging.debug('fetch region of interest')

    if not os.path.exists(roi_file):
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


def configure_camera():
    logging.debug('configure camera...')
    fetch_region_of_interest()
    camera.sharpness = int(os.getenv('MOTION_CAMERA_SHARPNESS', 20))
    camera.saturation = int(os.getenv('MOTION_CAMERA_SATURATION', 20))
    camera.rotation = int(os.getenv('MOTION_CAMERA_ROTATION', 0))


def capture_temp_image():
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg', resize=temp_resolution, splitter_port=3, use_video_port=True)
    stream.seek(0)
    image = Image.open(stream)
    image_array = numpy.asarray(image)
    if not has_roi:
        return image_array[::, ::, 1]
    return image_array[roi_x, roi_y, 1]


def has_motion():
    global prev_temp_img
    current_temp_img = capture_temp_image()
    diff = (numpy.absolute(prev_temp_img.astype(numpy.int) - current_temp_img.astype(numpy.int)) > 22).sum()
    prev_temp_img = current_temp_img
    motion = diff >= motion_score
    if motion:
        logging.info('motion detected with score %d', diff)
    else:
        logging.debug('actual motion score %d', diff)
    return motion


def main():
    try:
        global prev_temp_img

        configure_camera()
        stream = change_camera_settings(day_settings)
        update_live_pic()
        motion_index = 0

        logging.info('start motion detection')
        prev_temp_img = capture_temp_image()
        while True:
            stream = check_for_camera_settings_switch(stream)
            camera.wait_recording(motion_timeout)

            if has_motion():
                motion_index += 1
                logging.debug('new motion event')
                current_framerate = camera.framerate
                filename_before = str(motion_index) + '_before_' + str(current_framerate) + '.h264'
                filename_after = str(motion_index) + '_after_' + str(current_framerate) + '.h264'
                f1_temp = temp_folder + filename_before
                f2_temp = temp_folder + filename_after
                f1 = output_folder + filename_before
                f2 = output_folder + filename_after

                camera.split_recording(f2_temp)
                stream.copy_to(f1_temp)
                stream.clear()

                camera.wait_recording(3)
                while has_motion():
                    camera.wait_recording(5)

                camera.split_recording(stream)
                os.rename(f1_temp, f1)
                os.rename(f2_temp, f2)
                logging.debug('trigger convert shell script')
                call(trigger_convert_cmd, shell=True)
    except Exception:
        logging.exception('caught exception')
    finally:
        logging.info('motion detection stopped')
        camera.stop_recording()


if __name__ == '__main__':
    main()
