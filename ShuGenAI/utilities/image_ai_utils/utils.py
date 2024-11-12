import PIL
import cv2
import json
import torch
import numpy as np

from pathlib import Path
from ultralytics import YOLO
from PIL import ImageFont, ImageDraw, Image, ImageFilter
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


class ImageAIUtils:
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
            np.array([int(c[i: i + 2], 16) for i in (1, 3, 5)])
            for c in color_codes
            if c
        ]

    def _get_predictions_dict(self, results, lang="eng"):
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

    def _overlay_masks_on_image(self, image, objects):
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

    # utility function for main object detection
    def _combine_masks_around_main_object(self, objects, main_object_idx, proximity_threshold=20):
        def is_within_proximity(bbox1, bbox2, threshold=20):
            # Calculate if two bounding boxes are within a given pixel proximity threshold
            x1, y1, w1, h1 = bbox1
            x2, y2, w2, h2 = bbox2

            return (
                    abs(x1 - x2) <= threshold
                    or abs(y1 - y2) <= threshold
                    or abs((x1 + w1) - (x2 + w2)) <= threshold
                    or abs((y1 + h1) - (y2 + h2)) <= threshold
            )

        main_object = objects[main_object_idx]
        combined_mask = main_object["mask"].copy()

        for i, obj in enumerate(objects.values()):
            if i != main_object_idx:
                # Check if object is close enough or overlaps with the main object's bounding box
                if is_within_proximity(
                        main_object["bbox"], obj["bbox"], threshold=proximity_threshold
                ):
                    combined_mask = cv2.bitwise_or(
                        combined_mask, obj["mask"]
                    )  # Add to main mask

        return combined_mask

    # utility function for main object detection
    def _get_main_object_index(self, objects):
        # Assuming each object has a 'class' label, 'mask', and 'bbox' (bounding box)
        return max(objects, key=lambda i: np.sum(objects[i]["mask"]))  # Largest mask area

    # on image upload
    def infer_image(self, image: PIL.Image) -> (PIL.Image, []):

        # Get predictions for the image and overlay them on it
        results = self.seg_model(image)
        predictions = self._get_predictions_dict(results)
        segmented_image = self._overlay_masks_on_image(image, predictions)

        # TODO: predictions need to be saved somewhere

        return segmented_image, predictions

    # remove background
    def remove_background(self, image: PIL.Image, predictions) -> PIL.Image:
        # TODO: load predictions from somewhere

        main_object_idx = self._get_main_object_index(predictions)

        combined_mask = self._combine_masks_around_main_object(
            predictions, main_object_idx, proximity_threshold=20
        )

        # Convert the image to RGBA (if it's not already in that format)
        background_removed_image = image.convert("RGBA")

        # Convert the numpy mask to a PIL image in grayscale mode
        mask_image = Image.fromarray(combined_mask * 255, mode="L")

        # Set the background pixels to transparent
        background_removed_image.putalpha(mask_image)

        return background_removed_image

    # Pick up an object
    def pick_up_object(self, image: PIL.Image, object_list: [], predictions) -> PIL.Image:

        selected_objects = [predictions[i] for i in object_list]

        # Merge the selected masks into one
        merged_mask = np.zeros_like(selected_objects[0]["mask"], dtype=np.uint8)
        for obj in selected_objects:
            merged_mask = cv2.bitwise_or(merged_mask, obj["mask"])

        # Convert the image to RGBA (if it's not already in that format)
        background_removed_image = image.convert("RGBA")

        # Convert the numpy mask to a PIL image in grayscale mode
        mask_image = Image.fromarray(merged_mask * 255, mode="L")

        # Set the background pixels to transparent
        background_removed_image.putalpha(mask_image)

        return background_removed_image

    # Edit background
    def edit_background(self, image: PIL.Image, background_image: PIL.Image, predictions) -> PIL.Image:

        main_object_idx = self._get_main_object_index(predictions)

        combined_mask = self._combine_masks_around_main_object(
            predictions, main_object_idx, proximity_threshold=20
        )

        # Resize the background image to match the dimensions of the image
        background_image = background_image.resize(image.size)

        # Overlay the image on top of the resized background
        background_removed_image = image.convert("RGBA")

        # Convert the numpy mask to a PIL image in grayscale mode
        mask_image = Image.fromarray(combined_mask * 255, mode="L")
        # Set the background pixels to transparent
        background_removed_image.putalpha(mask_image)

        background_image = background_image.convert("RGBA")
        edited_image = Image.alpha_composite(background_image, background_removed_image)

        return edited_image

    # cut out object
    def cut_out_object(self, image: PIL.Image, object_list: [], predictions) -> PIL.Image:

        # resize the image to 512x512
        original_size = image.size
        image = image.resize((512, 512))

        selected_objects = [predictions[i] for i in object_list]

        # Merge the selected masks into one
        merged_mask = np.zeros_like(selected_objects[0]["mask"], dtype=np.uint8)
        for obj in selected_objects:
            merged_mask = cv2.bitwise_or(merged_mask, obj["mask"])

        # Make mask larger to include the object's outline
        kernel = np.ones((10, 10), np.uint8)

        # Dilate the mask
        padded_mask = cv2.dilate(merged_mask, kernel, iterations=5)

        mask_image = Image.fromarray(padded_mask * 255).convert("RGB").resize((512, 512))

        prompt = "blends seamlessly with the surrounding area"
        inpainted_image = self.inpaint_model(
            prompt=prompt, image=image, mask_image=mask_image
        ).images[0]

        # Resize the inpainted image back to its original size
        inpainted_image = inpainted_image.resize(original_size)

        return inpainted_image
