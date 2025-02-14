from app.aws.s3 import upload_image_to_s3
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import torch
import cv2


model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


def preprocess_image(image, target_size=(224, 224)):
    image = cv2.resize(image, target_size)
    image = cv2.convertScaleAbs(image, alpha=1.2, beta=10)
    return image


def parse(video_path, target_elements, sample_rate=10, similarity_threshold=0.9):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"FPS: {fps}")
    print(f"Frame Count: {frame_count}")

    extracted_entities = {}
    frame_number = 0
    while True:
        ret, frame = video.read()
        if not ret:
            break

        if frame_number % sample_rate == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)

            scales = [0.5, 1.0, 1.5]
            all_probs = []

            for scale in scales:
                scaled_size = (
                    int(pil_image.width * scale),
                    int(pil_image.height * scale),
                )
                scaled_image = pil_image.resize(scaled_size)
                processed_image = preprocess_image(np.array(scaled_image))

                inputs = processor(
                    text=target_elements,
                    images=processed_image,
                    return_tensors="pt",
                    padding=True,
                ).to(device)

                with torch.no_grad():
                    outputs = model(**inputs)

                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                all_probs.append(probs)

            combined_probs = torch.mean(torch.stack(all_probs), dim=0)

            for i, element in enumerate(target_elements):
                if combined_probs[0][i] > similarity_threshold:
                    file_name = f"{element}_{frame_number}.jpg"
                    s3_url = upload_image_to_s3(frame, file_name=file_name)
                    extracted_entities[file_name] = s3_url
                    print(
                        f"Detected {element} in frame {frame_number} with probability {combined_probs[0][i]:.4f}"
                    )

        frame_number += 1
    video.release()
    return extracted_entities
