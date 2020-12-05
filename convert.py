#runnable script
import os
import sys
import cv2
import logging
import argparse
import numpy as np
import pandas as pd
from utils import *


def main(opt):
    """
        Main function of the convert.py.
        Convert all the LJPEG files and store its overlay annotation in CSV file.
    """
    input = opt.input
    output = opt.output
    format = opt.format
    format = '.' + format

    if not os.path.exists(output): os.makedirs(output)
    log_file = os.path.join(output,"convert.log")
    logging.basicConfig(filename=log_file,level=logging.INFO)

    cols = ['NAME','FEATURE','SEVERITY','X1','Y1','X2','Y2','HEIGHT','WIDTH']
    benigns_df = pd.DataFrame(columns=cols)
    cancers_df = pd.DataFrame(columns=cols)

    for root, subFolders, filenames in os.walk(input):
        for filename in filenames:
            stem,ext = os.path.splitext(filename)
            if ext == ".LJPEG":
                #ljpeg
                ljpeg_path = os.path.join(root,filename)
                ljpeg_filename = os.path.basename(ljpeg_path)
                ljpeg_filestem = os.path.splitext(ljpeg_filename)[0]
                case_id,sequence,ext = ljpeg_filename.split('.')
                #ics
                ics_filestem = '-'.join(case_id.split('_'))
                ics_filename = ics_filestem + ".ics"
                ics_path = os.path.join(root,ics_filename)
                if os.path.isfile(ics_file_path):
                    ics_dict = get_ics_info(ics_path)
                    img_height = ics_dict[sequence]["height"]
                    img_width = ics_dict[sequence]["width"]
                    img_dim = (img_height,img_width)
                else:
                    log.warn("No ICS file for case with case_id = %s" %case_id)
                    continue
                #overlay
                overlay_filename = ljpeg_filestem + ".OVERLAY"
                overlay_path = os.path.join(root,overlay_filename)
                if os.path.isfile(overlay_path):
                    sdf = generate_annotation(overlay_path,img_dim,format)
                    if case_type == "benigns":
                        benigns_df = benigns_df.append(sdf,ignore_index=True)
                    elif cancers_df == "cancers:
                        cancers_df = cancers_df.append(sdf,ignore_index=True)
                #case name
                case_type = os.path.abspath(os.path.join(root,"../.."))
                case_type = os.path.basename(case_type)
                case_diretory = os.path.join(output,case_type)
                if not os.path.exists(case_diretory): os.mkdir(case_diretory)
                #output filepath 
                output_filepath = os.path.join(case_diretory,ljpeg_filestem)
                output_filepath = output_filepath + format
                #call ljpeg.py
                if opt.correction:
                    cmd = './ljpeg.py "{0}" "{1}" --ics {2} --correction'.format(ljpeg_path,output_filepath,ics_path)        
                elif opt.normalize:
                    cmd = './ljpeg.py "{0}" "{1}" --ics {2} --visual'.format(ljpeg_path,output_filepath,ics_path)        
                os.system(cmd)
    #save df
    benigns_csv = os.path.join(output,"benigns.csv")
    cancers_df = os.path.join(output,"cancers.csv")
    benigns_df.to_csv(benigns_csv,index=False)
    cancers_df.to_csv(cancers_csv,index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",type=str,help="input folder path")
    parser.add_argument("--output",type=str,help="output folder path")
    parser.add_argument("--format",type=str,default="png",help="image format")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--normalize",action="store_true",help="apply opencv normalization")
    group.add_argument("--correction",action="store_true",help="apply correction")
    opt = parser.parse_args()
    main(opt)

    
    
