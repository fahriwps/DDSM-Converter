#!/usr/bin/env python
import os
import re
import cv2
import sys
import logging
import argparse
import subprocess
import numpy as np
from utils import *


def read(path):
    """
        Unpack the .LJPEG image using the jpegdir library.
        Sample output:
            GW:1979  GH:4349  R:0
            C:1  N:xx.ljpeg.1  W:1979  H:4349  hf:1  vf:1
        Code borrowed from: https://github.com/nicholaslocascio/ljpeg-ddsm
    """
    PATTERN = re.compile('\sC:(\d+)\s+N:(\S+)\s+W:(\d+)\s+H:(\d+)\s')
    cmd = '%s -d -s %s' % (BIN, path)
    l = subprocess.check_output(cmd, shell=True)
    ll = l.decode()
    m = PATTERN.search(ll)
    C = int(m.group(1)) # I suppose this is # channels
    F = m.group(2)
    W = int(m.group(3))
    H = int(m.group(4))
    assert C == 1
    im = np.fromfile(F, dtype='uint16').reshape(H, W)
    L = im >> 8
    H = im & 0xFF
    im = (H << 8) | L
    os.remove(F)
    return im

if __name__ == '__main__':
    BIN = os.path.join(os.path.dirname(__file__), "jpegdir", "jpeg")
    if not os.path.exists(BIN):
        print("jpeg library is not built yet; use 'cd jpegdir; make' first")
        sys.exit(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("ljpeg", nargs=1)
    parser.add_argument("output", nargs=1)
    parser.add_argument("--ics", type=str)
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--correction",action="store_true")
    args = parser.parse_args()
    
    input_path = args.ljpeg[0]
    output_path = args.output[0]
    assert 'LJPEG' in input_path
    root = os.path.dirname(input_path)
    stem = os.path.splitext(input_path)[0]
    fname = os.path.basename(input_path)
    case_id,sequence,ext = fname.split('.')

    # read ICS
    ics_file_path = args.ics
    ics_dict = get_ics_info(ics_file_path)    
    img_height = ics_dict[sequence]['height']
    img_width = ics_dict[sequence]['width']
    img_bpp = ics_dict[sequence]['bpp']
    resolution = ics_dict[sequence]['resolution']
    scanner_type = ics_dict['scanner_type']
    scan_institution = ics_dict['scan_institution']
    
    try:
        raw_image = read(input_path)
    except:
        print("Cant open %s ... exiting" %fname)
        sys.exit(0)
    if img_width != raw_image.shape[1]:
        logging.warn('reshape: %s' %fname)
        raw_image = raw_image.reshape((img_height, img_width))
    if args.normalize:
        logging.warn("normalizing color, will lose information")
        image = cv2.normalize(raw_image, None, 0, 255, cv2.NORM_MINMAX)
        image = np.uint8(image)
    if args.correction:
        logging.warn("od correction: %s" %fname)
        image = optical_density_correction(raw_image,scan_institution,scanner_type)
        image = np.interp(image,(0.0,4.0),(255,0))
        norm_img = cv2.normalize(image,None,0,1,cv2.NORM_MINMAX,dtype=cv2.CV_32F)
        norm_img *= 255
        image = np.uint8(norm_img)        
    cv2.imwrite(output_path, image)
    

