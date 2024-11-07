import json
import cv2
import torch
import numpy as np

from pathlib import Path
from ultralytics import YOLO
from PIL import ImageFont, ImageDraw, Image
from diffusers import AutoPipelineForInpainting

# Get the relative path of this file
REL_PATH = Path(__file__).parent

SEGMENT_MODEL_PATH = REL_PATH / "static/yolov9c-seg.pt"
UKR_LABELS_PATH = REL_PATH / "static/coco_classes_ukr.json"
ENG_LABELS_PATH = REL_PATH / "static/coco_classes_eng.json"
FONT_PATH = REL_PATH / "static/ttNormPro.ttc"
INPAINING_MODEL_NAME = "runwayml/stable-diffusion-inpainting"

color_codes = [
    "#B52CFF",
    "#348F00",
    "#6B2CFF",
    "#FFFF2C",
    "#FF3535",
    "#FF7A00",
    "#0DA3FF",
    "#FFD700",
    "#20C9A5",
    "#E91E63",
    "#D4AC2B",
    "#8CFF00",
    "#FF007A",
    "#2E91E5",
    "#AFFF3C",
    "#C71585",
    "#FF6F00",
    "#009688",
    "#FFCC00",
    "#4A90E2",
    "#00BCD4",
    "#CDDC39",
    "#FF4081",
    "#795548",
    "#FFC400",
]


class Dependencies:
    def __init__(self):
        with open(ENG_LABELS_PATH) as f:
            self.eng_labels = json.load(f)

        with open(UKR_LABELS_PATH) as f:
            self.ukr_labels = json.load(f)

        # Determine the device to use
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Build a YOLOv9c model from pretrained weight
        self.seg_model = YOLO(SEGMENT_MODEL_PATH)
        self.seg_model.to(self.device)

        # Load the inpainting model
        self.inpaint_model = AutoPipelineForInpainting.from_pretrained("runwayml/stable-diffusion-inpainting")
        self.inpaint_model.to(self.device)

        # Load font
        self.labels_font = ImageFont.truetype(FONT_PATH, 14)

        # Load the color codes
        self.colors = [
            np.array([int(c[i : i + 2], 16) for i in (1, 3, 5)])
            for c in color_codes
            if c
        ]

    def get_predictions_dict(self, results, lang="eng"):
        local_results = results[0].cpu()

        orig_shape = local_results.orig_shape
        det_classes = local_results.boxes.cls.type(torch.int).numpy()
        det_masks = local_results.masks.xy
        det_bboxes = local_results.boxes.xyxy

        objects, counters = {}, {}

        for c, mask_obj, bbox_obj in zip(det_classes, det_masks, det_bboxes):
            # Convert the polygon coordinates to integer
            polygon = np.array(mask_obj, dtype=np.int32)
            # Create a mask for the polygon
            mask = np.zeros(orig_shape, dtype=np.uint8)
            cv2.fillPoly(mask, [polygon], 1)

            class_name = self.ukr_labels[str(c)] if lang == "ukr" else self.eng_labels[str(c)]

            # Get the color for the current class
            color = self.colors[c % len(self.colors)]

            num = counters.get(class_name, 0)
            if num == 0:    
                counters[class_name] = 1
                obj_text = class_name
            else:
                counters[class_name] += 1
                obj_text = f"{class_name} {num}"
            objects[obj_text] = {}
            objects[obj_text]["mask"] = mask
            objects[obj_text]["bbox"] = bbox_obj
            objects[obj_text]["color"] = color
            objects[obj_text]["outline_poligon"] = polygon

        return objects

    def overlay_masks_on_image(self, image, objects):
        for obj_text, obj_data in objects.items():
            mask = obj_data["mask"]
            bbox = obj_data["bbox"]
            color = obj_data["color"]
            polygon = obj_data["outline_poligon"]

            # Create a color mask (with the same shape as the image)
            color_mask = np.zeros_like(image)
            color_mask[mask == 1] = color

            # Overlay the mask on the image using the transparency factor
            image = cv2.addWeighted(np.array(image), 1, color_mask, 0.2, 0)

            # Draw the polygon outline on the image
            image = cv2.polylines(
                image,
                [polygon],
                isClosed=True,
                color=color.tolist(),
                thickness=2,
                lineType=cv2.LINE_AA,
            )

            # Find the centroid of the mask to place the label
            moments = cv2.moments(mask)
            if moments["m00"] != 0:
                cX = int(moments["m10"] / moments["m00"])
                cY = int(moments["m01"] / moments["m00"])
                position = (cX, cY)

                # Put the text on the image
                img_pil = Image.fromarray(image)
                draw = ImageDraw.Draw(img_pil)

                bbox = draw.textbbox(position, obj_text, font=self.labels_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                centered_position = (
                    position[0] - text_width // 2,
                    position[1] - text_height // 2,
                )

                x1, y1, x2, y2 = draw.textbbox(
                    centered_position, obj_text, font=self.labels_font
                )
                draw.rounded_rectangle(
                    (x1 - 5, y1 - 5, x2 + 5, y2 + 5), fill=(250, 246, 245), radius=8
                )

                draw.text(
                    centered_position,
                    obj_text,
                    font=self.labels_font,
                    fill=(0, 0, 0, 255),
                )
                image = np.array(img_pil)

        return Image.fromarray(image)
