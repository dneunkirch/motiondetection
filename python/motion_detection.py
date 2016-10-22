#!/usr/bin/python

import datetime
import logging
import os
import threading
import time
from subprocess import call

import picamera.array

import blacklist


class CameraSettings:
    def __init__(self, framerate, exposure_mode='auto', shutter_speed=0, iso=0):
        self.framerate = framerate
        self.exposure_mode = exposure_mode
        self.shutter_speed = shutter_speed
        self.iso = iso


night_settings = CameraSettings(framerate=2, exposure_mode='off', shutter_speed=500000, iso=1600)
day_settings = CameraSettings(framerate=15)

widht = 1920
height = 1080

sensor_mode = 2
seconds_before_event = 3
bitrate = 3000000
live_quality = 10
motion_timeout = 0.5
night_mode_active = False
motion_detected = False
waiting_for_motion_end = False
resolution = (widht, height)

temp_folder = os.environ['MOTION_TEMP']
output_folder = os.environ['MOTION_OUTPUT']
live_folder = os.environ['MOTION_LIVE']
script_folder = os.environ['MOTION_SCRIPTS']

night_mode_allowed = os.getenv('MOTION_NIGHT_MODE_ALLOWED', 'True') == 'True'
night_mode_start_h = int(os.getenv('MOTION_NIGHT_MODE_START_H', '19'))
night_mode_start_m = int(os.getenv('MOTION_NIGHT_MODE_START_M', '30'))
night_mode_end_h = int(os.getenv('MOTION_NIGHT_MODE_END_H', '5'))
night_mode_end_m = int(os.getenv('MOTION_NIGHT_MODE_END_M', '30'))

live_timeout = int(os.getenv('MOTION_LIVE_REFRESH_INTERVAL_SECONDS', '5'))

trigger_convert_cmd = 'bash ' + script_folder + 'convert_cron.sh'

camera = picamera.PiCamera(framerate=day_settings.framerate, sensor_mode=sensor_mode, resolution=resolution)
motion_blacklist = blacklist.Blacklist()

logging.basicConfig(filename='/var/log/motiondetection.log', level=logging.INFO,
                    format='%(asctime)s.%(msecs)d %(levelname)s - %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S")


class MotionDection(picamera.array.PiMotionAnalysis):
    def analyse(self, array):
        global motion_detected, waiting_for_motion_end

        if motion_detected:
            return

        threshold = 30 if waiting_for_motion_end else 50
        if motion_blacklist.has_motion(array=array, threshold=threshold):
            motion_detected = True


def update_live_pic():
    base = live_folder + time.strftime('%Y-%m-%d_%H-%M-%S')
    picture_temp = base + ".temp"
    picture = base + ".jpg"
    camera.capture(picture_temp, format='jpeg', quality=live_quality, splitter_port=2, use_video_port=True)
    os.rename(picture_temp, picture)
    threading.Timer(live_timeout, update_live_pic).start()


def change_camera_settings(output, settings):
    if camera.recording:
        camera.stop_recording()
    camera.framerate = settings.framerate
    camera.exposure_mode = settings.exposure_mode
    camera.shutter_speed = settings.shutter_speed
    camera.iso = settings.iso
    new_stream = picamera.PiCameraCircularIO(camera, seconds=seconds_before_event, bitrate=bitrate, splitter_port=1)
    camera.start_recording(new_stream, format='h264', splitter_port=1, motion_output=output, bitrate=bitrate)
    camera.wait_recording(2)
    return new_stream


def check_for_camera_settings_switch(stream, output):
    if not night_mode_allowed:
        return stream

    global night_mode_active

    now = datetime.datetime.now()
    start = now.replace(hour=night_mode_start_h, minute=night_mode_start_m)
    end = now.replace(hour=night_mode_end_h, minute=night_mode_end_m)

    if night_mode_start_h > night_mode_end_h:
        if now.hour < night_mode_start_h:
            start = start - datetime.timedelta(days=1)
        else:
            end = end + datetime.timedelta(days=1)

    if start < now < end:
        if not night_mode_active:
            logging.info('activate night mode')
            night_mode_active = True
            return change_camera_settings(output, night_settings)
    elif night_mode_active:
        logging.info('activate day mode')
        night_mode_active = False
        return change_camera_settings(output, day_settings)

    return stream


def main():
    try:
        logging.debug('configure camera...')
        camera.sharpness = int(os.getenv('MOTION_CAMERA_SHARPNESS', 20))
        camera.saturation = int(os.getenv('MOTION_CAMERA_SATURATION', 20))
        camera.rotation = int(os.getenv('MOTION_CAMERA_ROTATION', 0))
        global motion_detected, waiting_for_motion_end
        with MotionDection(camera) as output:
            stream = change_camera_settings(output, day_settings)
            update_live_pic()
            motion_index = 0

            logging.info('start motion detection')
            motion_detected = False

            while True:
                stream = check_for_camera_settings_switch(stream, output)
                camera.wait_recording(motion_timeout)
                if motion_detected:
                    waiting_for_motion_end = True
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

                    while motion_detected:
                        motion_detected = False
                        camera.wait_recording(5)

                    waiting_for_motion_end = False
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
