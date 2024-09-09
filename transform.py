# Imports
from edgeimpulse.experimental.util import fetch_samples
import edgeimpulse as ei
import os, sys
import requests
import argparse
from edge_impulse_linux.image import get_features_from_image_with_studio_mode
import cv2
import numpy as np


# these are the three arguments that we get in
parser = argparse.ArgumentParser(description='Reszie all images in project using a specific method and resolution')
parser.add_argument('--input-project-api-key', type=str, required=False, help="Specify a separate project API key to import from, otherwise current project is used")
parser.add_argument('--output-project-api-key', type=str, required=False, help="Specify a separate project API key to export to, otherwise current project is used and data is deleted")
parser.add_argument('--resize-method', type=str, required=True, help="Resize method", default="fit-shortest")
parser.add_argument('--resolution', type=int, required=True, help="Resize resolution")
parser.add_argument('--is-grayscale', type=str, required=True, help="Is the image grayscale", default="False")
#add debug arg
parser.add_argument('--debug', type=bool, required=False, help="Debug mode", default=False)
args, unknown = parser.parse_known_args()

if args.debug:
    # create output folder
    if not os.path.exists('output'):
        os.makedirs('output')
if args.input_project_api_key:
    INPUT_API_KEY = args.input_project_api_key
else:
    if not os.getenv('EI_PROJECT_API_KEY'):
        print('Missing EI_PROJECT_API_KEY')
        sys.exit(1)
    INPUT_API_KEY = os.environ.get("EI_PROJECT_API_KEY")
if args.output_project_api_key:
    OUT_API_KEY = args.output_project_api_key
else:
    if not os.getenv('EI_PROJECT_API_KEY'):
        print('Missing EI_PROJECT_API_KEY')
        sys.exit(1)
    OUT_API_KEY = os.environ.get("EI_PROJECT_API_KEY")
resize_method = args.resize_method
resolution = args.resolution
is_grayscale = eval(args.is_grayscale)

def get_project_id(api_key):
    response = requests.get(
    "https://studio.edgeimpulse.com/v1/api/projects",
    headers={'x-api-key': api_key},
)
    data = response.json()
    return data['projects'][0]['id']

def scale_bounding_boxes(sample, resolution, width, height, resize_method):
    offset_x=0
    offset_y=0
    if resize_method == 'squash':
        scale_x = resolution / width
        scale_y = resolution / height
    elif resize_method == 'fit-shortest':
        
        if width<height:

            scale_x = resolution / width
            scale_y = resolution / width
            offset_y = ((height - width) // 2)*scale_x
        else:
            scale_y = resolution / height
            scale_x = resolution/ height
            offset_x = ((width-height) // 2)*scale_y
        
    elif resize_method == 'fit-longest':
        if width<height:
            scale_x = resolution / height
            scale_y = resolution / height
            offset_x = ((width - height) // 2)*scale_x
        else:
            scale_y = resolution / width
            scale_x = resolution / width
            offset_y = ((height-width) // 2)*scale_y
    else:   
        raise ValueError(f"Unsupported resize method: {resize_method}")

    scaled_bounding_boxes = []
    for box in sample.bounding_boxes:
        scaled_box = {
            'label': box['label'],
            'x': int(box['x'] * scale_x) - offset_x,
            'y': int(box['y'] * scale_y)-offset_y,
            'width': int(box['width'] * scale_x),
            'height': int(box['height'] * scale_y)
        }
        scaled_bounding_boxes.append(scaled_box)

    return scaled_bounding_boxes

# Get output project info
output_projectId = get_project_id(OUT_API_KEY)
# Get input project info
input_projectId = get_project_id(INPUT_API_KEY)

ei.API_KEY = INPUT_API_KEY
for sample in fetch_samples(category="all"):
    try:
        img_bytes = sample.data.read()
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), -1)
        # get image size
        height, width, _ = img.shape
        # imread returns images in BGR format, so we need to convert to RGB
        # this mode uses the same settings used in studio to crop and resize the input
        features, cropped = get_features_from_image_with_studio_mode(img, resize_method, resolution, resolution,is_grayscale)
        # Encode the image to PNG format in memory
        _, img_encoded = cv2.imencode('.png', cropped)
        img_bytes = img_encoded.tobytes()
        if args.debug:
            cv2.imwrite(f'output/{sample.label}.png', cropped,)
        
        # Upload the image to Edge Impulse
        res = requests.post(url=f'https://ingestion.edgeimpulse.com/api/{sample.category}/files',
            headers={
            'x-label': sample.label,
            'x-api-key': OUT_API_KEY,},
            files={'data': (f'{sample.filename}.png', img_bytes, 'image/png')}
        )
        print(f"Uploaded sample {sample.sample_id} to project {output_projectId}")
        output_sample_id = res.json()['files'][0]["sampleId"]    
        # If the sample has bounding boxes, upload them as well
        if sample.bounding_boxes:
            print(f"Sample {sample.sample_id} has bounding boxes, rescaling and updating")
            # scale all bounding boxes to the new image size
            scaled_bbs = scale_bounding_boxes(sample, resolution, width, height, resize_method)
            response = requests.post(
                f"https://studio.edgeimpulse.com/v1/api/{output_projectId}/raw-data/{output_sample_id}/bounding-boxes",
                headers={"Content-Type":"application/json", 'x-api-key': OUT_API_KEY,},
                json={"boundingBoxes":scaled_bbs}
            )

        if OUT_API_KEY==INPUT_API_KEY:
            # Disable the original sample
            print(f"Disabling sample {sample.sample_id}")
            response = requests.post(
                f"https://studio.edgeimpulse.com/v1/api/{input_projectId}/raw-data/{sample.sample_id}/disable",
                headers={'x-api-key': OUT_API_KEY},
            )
        

    except Exception as e:
        print(f"An error occurred: {e}")


