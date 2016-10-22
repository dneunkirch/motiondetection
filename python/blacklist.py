import logging
import os
import re
import time

import numpy


class Blacklist(object):
    logging.basicConfig(filename='/var/log/motiondetection.log', level=logging.INFO,
                        format='%(asctime)s.%(msecs)d %(levelname)s - %(message)s',
                        datefmt="%Y-%m-%d %H:%M:%S")
    motion_score = 0
    motion_blocks = None
    last_motion_check = time.time()

    def __init__(self):
        blacklist_file = os.environ['MOTION_WEB'] + 'whitelist.txt'
        if os.path.exists(blacklist_file):
            whitelist = open(blacklist_file, mode='r')
            whitelist_content = whitelist.readline()
            whitelist.close()
            motion_blocks = []
            for element in whitelist_content.split(', '):
                match = re.search("(\d*),(\d*)", element)
                x = int(match.group(1))
                y = int(match.group(2))
                point = tuple([x, y])
                motion_blocks.append(point)
            self.motion_blocks = motion_blocks

    @staticmethod
    def motion_block_count(array, threshold):
        return (numpy.sqrt(
            numpy.square(array['x'].astype(numpy.float)) +
            numpy.square(array['y'].astype(numpy.float))).clip(0, 255).astype(numpy.uint8) > threshold).sum()

    def filter_array(self, array):
        if not self.motion_blocks:
            return array
        filtered_array = []
        for motion_block in self.motion_blocks:
            filtered_array.append(array[motion_block])
        return numpy.array(filtered_array)

    def has_motion(self, array, threshold):
        now = time.time()
        if (now - self.last_motion_check) < 0.5:
            return False
        self.last_motion_check = now

        filtered_array = self.filter_array(array)
        count = self.motion_block_count(filtered_array, threshold)

        if count < self.motion_score:
            logging.debug('actual motion score %d', count)
            return False

        logging.info('motion detected. motion score: %d', count)
        return True
