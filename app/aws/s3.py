from dotenv import load_dotenv
import boto3
import cv2
import json
import os
import uuid

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")


def get_s3_client():
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_REGION:
        raise ValueError("One or more AWS environment variables are not set.")

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def upload_image_to_s3(
    image, bucket_name="file-destination", folder_path=None, file_name=None
):
    file_name = file_name or str(uuid.uuid4())
    s3_key = f"{folder_path}/{file_name}" if folder_path else file_name

    s3_client = get_s3_client()
    _, buffer = cv2.imencode(".jpg", image)

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=buffer.tobytes(),
            ContentType="image/jpeg",
        )
        region = s3_client.meta.region_name
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"

    except Exception as e:
        print(f"Error uploading image to S3: {str(e)}")


def upload_json_to_s3(json_data, bucket_name="file-destination", s3_key="temp.json"):
    s3_client = get_s3_client()
    json_string = json.dumps(json_data)

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json_string,
            ContentType="application/json",
        )
        print(f"Successfully uploaded json to {bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")


def download_large_file_from_s3(s3_key, local_file_path, bucket_name="file-destination", chunk_size=8192):
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        total_size = 0
        with open(local_file_path, "wb") as file:
            while True:
                chunk = response['Body'].read(chunk_size)
                if not chunk:
                    break
                file.write(chunk)
                total_size += len(chunk)
                print(f"Downloaded {total_size} bytes", end="\r")
        print(f"Finished downloading. Total file size: {total_size} bytes")
        return local_file_path

    except Exception as e:
        print(f"Error getting object from S3: {str(e)}")
        return None
