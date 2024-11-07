import PIL
import cv2
import numpy as np

from dependencies import Dependencies
from PIL import Image, ImageDraw, ImageFilter

dep = Dependencies()


# utility function for main object detection
def _combine_masks_around_main_object(objects, main_object_idx, proximity_threshold=20):
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
def _get_main_object_index(objects):
    # Assuming each object has a 'class' label, 'mask', and 'bbox' (bounding box)
    return max(objects, key=lambda i: np.sum(objects[i]["mask"]))  # Largest mask area


# on image upload
def infer_image(image: PIL.Image) -> (PIL.Image, []):

    # Get predictions for the image and overlay them on it
    results = dep.seg_model(image)
    predictions = dep.get_predictions_dict(results)
    segmented_image = dep.overlay_masks_on_image(image, predictions)

    # TODO: predictions need to be saved somewhere

    return segmented_image, predictions


# remove background
def remove_background(image: PIL.Image) -> PIL.Image:
    # TODO: load predictions from somewhere
    predictions = {...}

    main_object_idx = _get_main_object_index(predictions)

    combined_mask = _combine_masks_around_main_object(
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
def pick_up_object(image: PIL.Image, object_list: []) -> PIL.Image:
    # TODO: load predictions from somewhere
    predictions = {...}

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
def edit_background(image: PIL.Image, background_image: PIL.Image) -> PIL.Image:
    # TODO: load predictions from somewhere
    predictions = {...}

    main_object_idx = _get_main_object_index(predictions)

    combined_mask = _combine_masks_around_main_object(
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
def cut_out_object(image: PIL.Image, object_list: []) -> PIL.Image:
    # TODO: load predictions from somewhere
    predictions = {...}

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
    inpainted_image = dep.inpaint_model(
        prompt=prompt, image=image, mask_image=mask_image
    ).images[0]

    # Resize the inpainted image back to its original size
    inpainted_image = inpainted_image.resize(original_size)

    return inpainted_image
