import os
import cv2
import logging
import numpy as np
import pandas as pd 


def _get_value(lst, row_name, idx):
    """
        Helper function to parse the ics lines using a key to get the corresponding metadata.
        Args:
        ----------
        lst: list
            Ics lines
        row_name: string
            Key
        idx: int
            Index of the metadata
        Returns:
        ----------
        val : string
            Metadata
    """
    val = None
    for l in lst:
        if not l:
            continue
        if l[0] == row_name:
            try:
                val = l[idx]
            except Exception:
                print (row_name, idx)
                print (lst)
                val = None
            break
    return val

def get_ics_info(ics_file_path):
    """
        Parser function to get case metadata from ics file.
        Args:
        ----------
        ics_file_path: string
            Path to the ics file.
        Returns:
        ----------
        ics_dict: dictionary
            A dictionary containing the following metadata:
                patient_id     <-->   patient_id 
                age            <-->   digitizer 
                scanner_type   <-->   scanner_type 
                density        <-->   density 
                sequence       <-->   {height,width,bpp,resolution}
    """
    scanner_map = {
        ('A', 'DBA'): 'MGH',
        ('A', 'HOWTEK'): 'MGH',
        ('B', 'LUMISYS'): 'WFU',
        ('C', 'LUMISYS'): 'WFU',
        ('D', 'HOWTEK'): 'ISMD'
    }
    
    ics_file_name = os.path.basename(ics_file_path)
    letter_code = ics_file_name[0]
    with open(ics_file_path, 'r') as f:
        lines = list(map(lambda s: s.strip().split(), f.readlines()))
    PATIENT_ID = _get_value(lines, 'filename', 1)
    DIGITIZER = _get_value(lines,'DIGITIZER',1)
    AGE = _get_value(lines, 'PATIENT_AGE', 1)
    DENSITY = _get_value(lines, 'DENSITY', 1)    
    ics_dict = {
        'patient_id':PATIENT_ID,
        'age': AGE ,
        'scanner_type': DIGITIZER,
        'scan_institution': scanner_map[(letter_code,DIGITIZER)],
        'density': DENSITY
    }
    for sequence in ['LEFT_CC', 'RIGHT_CC', 'LEFT_MLO', 'RIGHT_MLO']:
        if _get_value(lines, sequence, 0) is None:
            continue
        sequence_dict = {
            'height': int(_get_value(lines, sequence, 2)),
            'width': int(_get_value(lines, sequence, 4)),
            'bpp': int(_get_value(lines, sequence, 6)),
            'resolution': float(_get_value(lines, sequence, 8))
        }
        ics_dict[sequence] = sequence_dict
    return ics_dict

def make_contour(chaincode):
    """
        Convert DDSM chaincode to OpenCV contour.
        Args:
        ----------
        chaincode: list of int
            DDSM chaincode
        Returns:
        ----------
        numpy.array 
            Opencv contour array.
    """
    directions = {
        0 : [0,-1],
        1 : [1,-1],
        2 : [1,0],
        3 : [1,1],
        4 : [0,1],
        5 : [-1,1],
        6 : [-1,0],
        7 : [-1,-1]
    }
    start_X = chaincode.pop(0)
    start_Y = chaincode.pop(0)
    initialPoint = [start_X,start_Y]
    contour = []
    for code in chaincode:
        nextPoint = [x + y for x , y in zip(initialPoint, directions[code])]
        contour.append(nextPoint)
        initialPoint = nextPoint
    return np.array(contour).reshape((-1,1,2)).astype(np.int32)

def optical_density_correction(im,scan_institution,scanner_type):
    """
        Perform optical density mapping and noise correction of the decompressed image.
        Args:
        ----------
        im: numpy.array
            Decompressed .LJPEG image
        scan_institution: string
            Institution of the scanner
        scanner_type: string 
            Type of the scanner
        Returns:
        ----------
        im_od: numpy.array
            Corrected image
    """
    #optical density mapping
    im_od = np.zeros_like(im, dtype=np.float64)
    if (scan_institution == 'MGH') and (scanner_type == 'DBA'):
        im_od = (np.log10(im + 1) - 4.80662) / -1.07553  # add 1 to keep from log(0)
    elif (scan_institution == 'MGH') and (scanner_type == 'HOWTEK'):
        im_od = (-0.00094568 * im) + 3.789
    elif (scan_institution == 'WFU') and (scanner_type == 'LUMISYS'):
        im_od = (im - 4096.99) / -1009.01
    elif (scan_institution == 'ISMD') and (scanner_type == 'HOWTEK'):
        im_od = (-0.00099055807612 * im) + 3.96604095240593
    
    #heath noise correction
    im_od[im_od < 0.05] = 0.05
    im_od[im_od > 3.0] = 3.0
    return im_od

def parse_abnormality(abnormality_content):
    """
        Parser to get abnormality content.
        Args:
        ----------
        abnormality_content: list of string
            Abnormality annotation contained in overlay file.
        Returns:
        ----------
        abnormality: dictionary
            A dictionary containing the following abnormality content:
            lesion_type      <-->    mass or calcifications
            pathology_type   <-->    malignancy
            birads_type      <-->    birads level: 1,2,3,...5
            total_outlines   <-->    n total of chaincode outlines 
            boundary         <-->    opencv contour of the boundary
            core             <-->    [opencv contour of the core]
    """
    lesion_type = list(filter(lambda line: line.find("LESION_TYPE")==0,abnormality_content))
    if lesion_type:
        lesion_type = list(map(lambda line: line.split()[1],lesion_type))
    pathology_type = list(filter(lambda line: line.find("PATHOLOGY")==0,abnormality_content))
    if pathology_type:
        pathology_type = list(map(lambda line: line.split()[1],pathology_type))
    birads_type = list(filter(lambda line: line.find("ASSESSMENT")==0,abnormality_content))
    if birads_type:
        birads_type = int(birads_type[0].split()[1]) 
    else:
        birads_type = None
    total_outlines = list(filter(lambda line : line.find("TOTAL_OUTLINES")==0,abnormality_content))
    if total_outlines:
        total_outlines = int(total_outlines[0].split()[1])
    else:
        total_outlines = 0
        return {}
    
    #find 'boundary' index, chaincode index, chaincode content, filter empty string
    boundary_index = [index for index,line in enumerate(abnormality_content) if line.find("BOUNDARY")==0]
    boundary_index = [index+1 for index in boundary_index]
    boundary_content = [abnormality_content[idx] for idx in boundary_index]
    boundary_content = list(filter(lambda px: px!='',boundary_content))

    #find 'core' index, chaincode index, chaincode content, filter empty string
    core_index = [index for index,line in enumerate(abnormality_content) if line.find("CORE")==0]
    core_index = [index+1 for index in core_index]
    core_content = [abnormality_content[idx] for idx in core_index]
    core_content = list(filter(lambda px: px!='',core_content))

    #convert boundary chaincode to opencv contour 
    chaincode = [int(px) for px in boundary_content[0].split()[:-1]]
    contour = make_contour(chaincode)
    boundary_contour = contour

    #convert every core chaincode to opencv contour
    core_contour = []
    for core in core_content:
        chaincode = [int(px) for px in core.split()[:-1]]
        contour = make_contour(chaincode)
        core_contour.append(contour)

    abnormality = {
        'lesion_type':lesion_type,
        'pathology_type':pathology_type,
        'birads_type':birads_type,
        'total_outines':total_outlines,
        'boundary':boundary_contour,
        'core':core_contour
    }
    return abnormality

def get_overlay_info(overlay_path):
    """
        Parser to get the abnormality annotation of an image from overlay file.
        Args:
        ----------
        overlay_path: string
            Path to the overlay file.
        Returns:
        ----------
        overlay_dict: dictionary
            A dictionary containing the following overlay content:
            name                    <-->    overlay/image stem_name
            total_abnormalities     <-->    total abnormalities / objects in image
            abnormality             <-->    {lesion_type,pathology_type,birads_type,total_outines,boundary,core}
    """
    overlay = {}
    overlay_filename = os.path.basename(overlay_path)
    overlay['name'] = os.path.splitext(overlay_filename)[0]
    
    with open(overlay_path,'r') as f:
        contents = list(map(lambda line: line.strip(),f.readlines()))
        contents = list(filter(lambda line: line!= "",contents))
    
    try:
        total_abnormalities = int(contents[0].split()[1])
    except:
        total_abnormalities = 0 
    overlay['total_abnormalities'] = total_abnormalities
    if total_abnormalities == 0:
        return {}
    
    try:
        abnormal_index = [index for index,line in enumerate(contents) if line.find('ABNORMALITY')==0]
        abnormal_index.append(len(contents))
    except:
        return {}
    
    i = 1
    for index in range(len(abnormal_index)-1):
        abnormality_content = contents[abnormal_index[index]:abnormal_index[index+1]]
        overlay[i] = parse_abnormality(abnormality_content)
        i += 1
    return overlay

def generate_annotation(overlay_path,img_dim,ext):
    """
        Generate custom annotation for one image from its DDSM overlay.
        Args:
        ----------
        overlay_path: string
            Overlay file path
        img_dim: tuple
            (img_height,img_width) 
        ext: string
            Image file format
        Returns:
        ----------
        pandas.dataframe
            columns: ['NAME','FEATURE','SEVERITY','X1','Y1','X2','Y2','HEIGHT','WIDTH']
            NAME            <-->    image filename with extension
            FEATURE         <-->    lesion_type: mass or calcifications
            X1,Y1,X2,Y2     <-->    xyrb bounding box
            HEIGHT          <-->    image height
            WIDTH           <-->    image width
    """
    myColumns = ["NAME","FEATURE","SEVERITY","X1","Y1","X2","Y2","HEIGHT","WIDTH"]
    sdf = pd.DataFrame(columns=myColumns) 

    H,W = img_dim
    overlay = get_overlay_info(overlay_path)
    total_abnormalities = overlay["total_abnormalities"]
    name = overlay["name"]
    name = str(name) + ext

    for i in range(1,total_abnormalities+1):        
        abnormality = overlay[i]
        lesion_type = abnormality["lesion_type"]
        lesion_type = '_'.join(lesion_type)
        pathology_type = abnormality["pathology_type"][0]
        boundary = abnormality["boundary"] 
        x,y,w,h = cv2.boundingRect(boundary)
        X1 = int(x)
        Y1 = int(y)
        X2 = int(x+w)
        Y2 = int(y+h)
        data = [str(name),str(lesion_type),str(pathology_type),X1,Y1,X2,Y2,H,W]
        label = pd.DataFrame([data],columns=myColumns)
        sdf = sdf.append(label,ignore_index=True)
    return sdf