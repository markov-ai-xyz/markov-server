import cv2
import pytesseract
import numpy as np
import re
from app.aws.s3 import upload_image_to_s3
from app.enums.box_classifications import BoxClassification
from collections import Counter
from typing import Tuple, Dict


def detect_boxes_iterative(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((5, 5), np.uint8)
    min_iterations = 4
    max_iterations = 9
    max_content_blocks = 20
    min_area = 2000

    for iterations in range(min_iterations, max_iterations):
        dilated = cv2.dilate(binary, kernel, iterations=iterations)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        content_blocks = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area > min_area:
                content_blocks.append((x, y, w, h))

        if len(content_blocks) <= max_content_blocks or iterations == max_iterations:
            return content_blocks


def merge_boxes(
    boxes, threshold=5, image_width=None, image_height=None, coverage_threshold=0.9
):
    def merge_two_boxes(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        max_w = max(x1 + w1, x2 + w2) - min_x
        max_h = max(y1 + h1, y2 + h2) - min_y
        return min_x, min_y, max_w, max_h

    def is_covering_image(box):
        if image_width is None or image_height is None:
            return False
        _, _, box_width, box_height = box
        box_area = box_width * box_height
        image_area = image_width * image_height
        return (box_area / image_area) > coverage_threshold

    def boxes_intersect(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        return (
            x1 < x2 + w2 + threshold
            and x2 < x1 + w1 + threshold
            and y1 < y2 + h2 + threshold
            and y2 < y1 + h1 + threshold
        )

    def boxes_below_threshold(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        share_left_edge = abs(x1 - (x2 + w2)) < threshold
        share_right_edge = abs((x1 + w1) - x2) < threshold
        share_top_edge = abs(y1 - (y2 + h2)) < threshold
        share_bottom_edge = abs((y1 + h1) - y2) < threshold

        vertical_overlap = (y1 < y2 + h2) and (y2 < y1 + h1)
        horizontal_overlap = (x1 < x2 + w2) and (x2 < x1 + w1)

        return ((share_left_edge or share_right_edge) and vertical_overlap) or (
            (share_top_edge or share_bottom_edge) and horizontal_overlap
        )

    if image_width is not None and image_height is not None:
        boxes = [box for box in boxes if not is_covering_image(box)]

    merged = []
    while boxes:
        current = boxes.pop(0)
        merged_any = True

        while merged_any:
            merged_any = False
            i = 0
            while i < len(boxes):
                if boxes_intersect(current, boxes[i]) or boxes_below_threshold(
                    current, boxes[i]
                ):
                    current = merge_two_boxes(current, boxes.pop(i))
                    merged_any = True
                else:
                    i += 1

        if not is_covering_image(current):
            merged.append(current)

    return merged


def is_header(
    image,
    box,
    full_image_height,
    header_position_threshold=0.2,
    text_length_threshold=50,
    word_count_threshold=10,
) -> bool:
    x, y, w, h = box
    roi = image[y : y + h, x : x + w]

    if not is_near_top(y, full_image_height, header_position_threshold):
        return False

    text = pytesseract.image_to_string(roi).strip()
    if not is_short_text(text, text_length_threshold, word_count_threshold):
        return False

    if not count_numbers(text) < 10:
        return False

    return True


def is_footer(
    image,
    box,
    full_image_height,
    footer_position_threshold=0.8,
    text_length_threshold=50,
    word_count_threshold=10,
) -> bool:
    x, y, w, h = box
    roi = image[y : y + h, x : x + w]

    if not is_near_bottom(y, full_image_height, footer_position_threshold):
        return False

    text = pytesseract.image_to_string(roi).strip()
    if not is_short_text(text, text_length_threshold, word_count_threshold):
        return False

    if not count_numbers(text) < 10:
        return False

    return True


def count_numbers(text: str) -> int:
    return sum(c.isdigit() for c in text)


def is_short_text(text: str, length_threshold: int, word_count_threshold: int) -> bool:
    return len(text) < length_threshold and len(text.split()) < word_count_threshold


def is_near_top(y: int, full_image_height: int, threshold: float) -> bool:
    return y < full_image_height * threshold


def is_near_bottom(y: int, full_image_height: int, threshold: float) -> bool:
    return y > full_image_height * threshold


def analyze_text(text: str) -> Dict[str, float]:
    lines = text.split("\n")
    non_empty_lines = [line.strip() for line in lines if line.strip()]

    if not non_empty_lines:
        return {}

    words = re.findall(r"\w+", text.lower())
    word_freq = Counter(words)

    table_line_count = sum(
        1 for line in non_empty_lines if re.search(r"\t|\s{3,}", line)
    )
    column_count = max(
        (len(re.findall(r"\S+", line)) for line in non_empty_lines), default=0
    )

    lines_with_number_endings = 0
    for line in non_empty_lines:
        last_chars = line[-10:] if len(line) >= 10 else line
        if sum(c.isdigit() for c in last_chars) >= len(last_chars) * 0.3:
            lines_with_number_endings += 1

    metrics = {
        "avg_line_length": sum(len(line) for line in non_empty_lines)
        / len(non_empty_lines),
        "max_line_length": max(len(line) for line in non_empty_lines),
        "num_lines": len(non_empty_lines),
        "num_count": sum(c.isdigit() for c in text),
        "special_char_count": sum(not c.isalnum() and c != " " for c in text),
        "table_line_count": table_line_count,
        "column_count": column_count,
        "lines_with_number_endings": lines_with_number_endings,
        "unique_word_ratio": len(word_freq) / len(words) if words else 0,
        "text_length": len(text),
        "word_count": len(words),
    }

    return metrics


def classify_text(metrics: Dict[str, float]) -> BoxClassification:
    if not metrics:
        return BoxClassification.IMAGE

    char_density = metrics["text_length"] / (
        metrics["num_lines"] * metrics["max_line_length"]
    )
    avg_words_per_line = metrics["word_count"] / metrics["num_lines"]

    table_score = (
        metrics["table_line_count"] / metrics["num_lines"]
        + metrics["num_count"] / metrics["text_length"]
        + metrics["special_char_count"] / metrics["text_length"]
        + metrics["lines_with_number_endings"] / metrics["num_lines"]
    )

    if (
        table_score > 0.4 and metrics["column_count"] >= 2 and metrics["num_lines"] >= 2
    ) or (
        metrics["lines_with_number_endings"] / metrics["num_lines"] > 0.5
        and metrics["num_lines"] >= 2
    ):
        return BoxClassification.TABLE

    elif (
        metrics["avg_line_length"] < 40
        and metrics["num_lines"] > 3
        and avg_words_per_line < 7
    ):
        return BoxClassification.LIST

    elif metrics["num_lines"] <= 2 and 20 < metrics["text_length"] < 200:
        return BoxClassification.CAPTION

    elif (
        metrics["avg_line_length"] > 40
        and metrics["num_lines"] > 1
        and char_density > 0.6
        and avg_words_per_line > 6
    ):
        return BoxClassification.PARAGRAPH

    elif (
        metrics["num_lines"] <= 3
        and metrics["text_length"] < 100
        and metrics["unique_word_ratio"] > 0.8
    ):
        return BoxClassification.TITLE

    elif metrics["text_length"] < 50:
        return BoxClassification.BLURB

    else:
        return BoxClassification.UNCLASSIFIED


def get_ocr_classification(image: np.ndarray, box: Tuple[int, int, int, int]) -> str:
    full_image_height = image.shape[0]
    if is_header(image, box, full_image_height):
        return "Header"
    if is_footer(image, box, full_image_height):
        return "Footer"

    x, y, w, h = box
    roi = image[y : y + h, x : x + w]
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(roi, config=custom_config)
    metrics = analyze_text(text)
    classification = classify_text(metrics)

    return str(classification.value)


def parse(image_path, kwargs=None):
    image = cv2.imread(image_path)
    if image is None:
        return "Error: Could not read the image."

    height, width = image.shape[:2]
    boxes = detect_boxes_iterative(image)
    merged_boxes = merge_boxes(boxes, image_width=width, image_height=height)

    image_with_boxes = image.copy()
    blocks_list = []

    for box in merged_boxes:
        x, y, w, h = box
        cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)

        ocr_classification = get_ocr_classification(image, box)
        text_x = x
        text_y = y + h + 20
        cv2.putText(
            image_with_boxes,
            ocr_classification,
            (text_x, text_y),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.6,
            color=(0, 0, 255),
            thickness=2,
        )

        cropped_image = image[y : (y + h), x : (x + w)]
        text = pytesseract.image_to_string(cropped_image)
        blocks_list.append(
            {
                "classification": ocr_classification,
                "text": text,
                "coordinates": {"left": x, "top": y, "width": w, "height": h},
            }
        )

    s3_url = upload_image_to_s3(image_with_boxes)
    return {"segmented_image_url": s3_url, "blocks": blocks_list}
