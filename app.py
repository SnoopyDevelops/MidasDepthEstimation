from pathlib import Path
import os

import gradio as gr
import numpy as np
import torch
from PIL import Image
from transformers import DPTFeatureExtractor, DPTForDepthEstimation

from depth_viewer import depth_viewer2html

feature_extractor = DPTFeatureExtractor.from_pretrained("Intel/dpt-large")
model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")


def process_image(image_path):
    image_path = Path(image_path)
    image = Image.open(image_path)

    # if wider than 512 pixels let's resample to keep it performant on phones etc
    if image.size[0] > 512:
        image = image.resize((512, int(512 * image.size[1] / image.size[0])), Image.Resampling.LANCZOS)

    # prepare image for the model
    encoding = feature_extractor(image, return_tensors="pt")

    # forward pass
    with torch.no_grad():
        outputs = model(**encoding)
        predicted_depth = outputs.predicted_depth

    # interpolate to original size
    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    ).squeeze()
    output = prediction.cpu().numpy()
    depth = (output * 255 / np.max(output)).astype('uint8')

    h = depth_viewer2html(image, depth)
    return [h]


title = "3d Visualization of Depth Maps Generated using MiDaS"
description = """
Improved 3D interactive depth viewer using Three.js embedded in a Gradio app. 
For more details see the 
<a href='https://colab.research.google.com/drive/1l2l8U7Vhq9RnvV2tHyfhrXKNuHfmb4IP?usp=sharing'>Colab Notebook.</a>
"""
examples = [['examples/' + filename] for filename in os.listdir('./examples') if filename.endswith('.jpg')]

iface = gr.Interface(fn=process_image,
                     inputs=[gr.Image(type="filepath", label="Input Image")],
                     outputs=[gr.HTML(label='Depth Viewer', elem_id='depth-viewer')],
                     title=title,
                     description=description,
                     examples=examples,
                     allow_flagging="never",
                     cache_examples=False,
                     css='#depth-viewer: {height:300px;}')

iface.launch(debug=True, enable_queue=False)
