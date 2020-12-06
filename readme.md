# DDSM Converter
> Convert DDSM LJPEG and generate CSV annotation file.

## DDSM (Digital Database of Screening Mammogram)
Source: http://www.eng.usf.edu/cvprg/Mammography/Database.html

## Dependencies
* Python 3+
* OpenCV-Python 
* Pandas
* Numpy
```
pip install -r requirements.txt
```

## How to use
### 1.Build jpeg
```
cd jpegdir; make
```
### 2.Run `convert.py`:
```
python3 convert.py --input path/to/ddsm/folder --output folder/path/to/store/output --format png --correction
```
Argparse: <br/>
`--correction` apply correction to avoid black images and noisy image **(recommended)**.<br/>
`--normalization` apply opencv normalization.<br/>
`--format` file extension (opencv supported format only).<br/>
### Example I/O
Input directory (tree):
```
path/to/ddsm/folder
└── cases
    ├── benigns
    │   └── benign_01
    │       └── case0029
    │           ├── C-0029-1.ics
    │           ├── C_0029_1.LEFT_CC.LJPEG
    │           ├── C_0029_1.LEFT_CC.OVERLAY
    │           ├── C_0029_1.LEFT_MLO.LJPEG
    │           ├── C_0029_1.LEFT_MLO.OVERLAY
    │           ├── C_0029_1.RIGHT_CC.LJPEG
    │           ├── C_0029_1.RIGHT_MLO.LJPEG
    │           └── TAPE_C_0029_1.COMB.16_PGM
    ├── cancers
    │   └── cancer_01
    │       └── case3086
    │           ├── B-3086-1.ics
    │           ├── B_3086_1.LEFT_CC.LJPEG
    │           ├── B_3086_1.LEFT_CC.OVERLAY
    │           ├── B_3086_1.LEFT_MLO.LJPEG
    │           ├── B_3086_1.LEFT_MLO.OVERLAY
    │           ├── B_3086_1.RIGHT_CC.LJPEG
    │           ├── B_3086_1.RIGHT_MLO.LJPEG
    │           └── TAPE_B_3086_1.COMB.16_PGM
    └── normals
        └── normal_10
            └── case3660
                ├── B-3660-1.ics
                ├── B_3660_1.LEFT_CC.LJPEG
                ├── B_3660_1.LEFT_MLO.LJPEG
                ├── B_3660_1.RIGHT_CC.LJPEG
                ├── B_3660_1.RIGHT_MLO.LJPEG
                └── TAPE_B_3660_1.COMB.16_PGM
```
Output directory (tree):
```
folder/path/to/store/output
├── benigns
│   ├── C_0029_1.LEFT_CC.jpg
│   └── C_0029_1.LEFT_MLO.jpg
├── benigns.csv
├── cancers
│   ├── B_3086_1.LEFT_CC.jpg
│   └── B_3086_1.LEFT_MLO.jpg
├── cancers.csv
└── normals
    ├── B_3660_1.LEFT_CC.jpg
    ├── B_3660_1.LEFT_MLO.jpg
    ├── B_3660_1.RIGHT_CC.jpg
    └── B_3660_1.RIGHT_MLO.jpg
```
CSV:
```
NAME,FEATURE,SEVERITY,X1,Y1,X2,Y2,HEIGHT,WIDTH
```
## Reference
* [nicholaslocascio/ljpeg-ddsm](https://github.com/nicholaslocascio/ljpeg-ddsm)
* [fjeg/ddsm_tools](https://github.com/fjeg/ddsm_tools)


