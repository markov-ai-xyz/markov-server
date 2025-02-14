import base64
import os
import fitz
import assemblyai as aai

from dotenv import load_dotenv
from langchain.schema import Document
from app.loggers.custom import logger
from app.parsers.image import parse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import CSVLoader, Docx2txtLoader, TextLoader

load_dotenv()

ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")
aai.settings.api_key = ASSEMBLY_AI_API_KEY
transcriber = aai.Transcriber()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)


def process_csv(file_path, kwargs):
    try:
        loader = CSVLoader(file_path)
        documents = loader.load()

        csv_text = "\n".join([doc.page_content for doc in documents])
        text_split = text_splitter.split_text(csv_text)
        logger.info("CSV file loaded successfully.")
        return text_split

    except Exception as e:
        logger.error("Error processing CSV: %s", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_docx(file_path, kwargs):
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        logger.info("DOCX file loaded successfully.")
        return documents

    except Exception as e:
        logger.error("Error processing DOCX: %s", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_pdf(file_path, kwargs):
    try:
        documents = []
        image_count = 0

        with fitz.open(file_path) as pdf:
            for page_num in range(len(pdf)):
                page = pdf[page_num]

                text = page.get_text()
                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={"page": page_num + 1, "type": "text"},
                        )
                    )

                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf.extract_image(xref)
                    image_bytes = base_image["image"]
                    base64_image = base64.b64encode(image_bytes).decode("utf-8")

                    image_document = Document(
                        page_content=f"[Image {image_count + 1}]",
                        metadata={
                            "page": page_num + 1,
                            "type": "image",
                            "image_data": base64_image,
                            "image_format": base_image["ext"],
                        },
                    )
                    documents.append(image_document)
                    image_count += 1
        logger.info(
            f"PDF file loaded successfully. Extracted {len(documents)} chunks (including {image_count} images)."
        )

    except Exception as e:
        logger.error("Error processing PDF: %s", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_text(file_path, kwargs):
    try:
        loader = TextLoader(file_path)
        documents = loader.load()
        logger.info("TXT file loaded successfully.")
        return documents

    except Exception as e:
        logger.error("Error processing TXT: %s", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_audio(file_path, kwargs):
    try:
        transcript = transcriber.transcribe(file_path)
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(transcript.error)
            return []
        else:
            logger.info("Audio file loaded successfully.")
            text_split = text_splitter.split_text(transcript.text)
            return text_split

    except Exception as e:
        logger.error("Error processing audio: %s", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def process_image(file_path, kwargs):
    try:
        image_format = file_path.split(".")[-1].lower()
        extraction_result = parse(file_path)

        image_document = {
            "page": 1,
            "type": "image",
            "image_format": image_format,
            "extracted_text": extraction_result.get("text"),
            "num_objects": extraction_result.get("num_objects"),
            "segmented_image": extraction_result.get("segmented_image"),
        }
        logger.info("Image file processed successfully.")
        return image_document

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
