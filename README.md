Image Resize Transformation Block (Python)
This transformation block resizes all images in an Edge Impulse project using the same methods as in edge_impulse_linux. 

Requirements
Python 3.x
Edge Impulse Python SDK
OpenCV
NumPy
Requests
Installation
Clone the repository locally
use `edge_impulse_blocks init` to initialise a Standalone block in your org
then `edge_impulse_blocks push` to push this up.
Then run this from a project or from your dashboard.

Install the required Python packages:

Usage
Command Line Arguments/Parameters

--input-project-api-key: Specify a separate project API key to import from, otherwise the current project is used.

--output-project-api-key: Specify a separate project API key to export to, otherwise the current project is used and data is deleted.

--resize-method: Resize method (default: fit-shortest).

--resolution: Resize resolution (required).

--is-grayscale: Is the image grayscale (default: False).

--debug: Debug mode (default: False).


The script performs the following steps:

Fetches samples from the input project.
Resizes and optionally converts images to grayscale based on the same methods as the linux-python-sdk
Uploads the transformed images to the output project.
