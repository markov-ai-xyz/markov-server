import fitz
import os
import tempfile
from PIL import Image
from typing import Any, Dict, List
from app.enums.resolutions import Resolution
from app.parsers.image import parse


def parse_pdf(file_path: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    res_value = kwargs.get("res")
    if res_value is None or res_value not in (res.value for res in Resolution):
        return {"Error": "Please specify 'res' as either 'high_res' or 'low_res'"}
    # TODO: Sanitize & clean text; create unified response schema
    if kwargs.get("res") == "low_res":
        return parse_pdf_low_res(file_path)
    if kwargs.get("res") == "high_res":
        return parse_pdf_high_res(file_path)

    raise ValueError("Resolution enums must be updated")


def parse_pdf_low_res(file_path: str) -> Dict[str, Any]:
    with fitz.open(file_path) as pdf:
        text_extractions: List[Dict[str, Any]] = []
        image_extractions: List[Dict[str, Any]] = []

        for page_num in range(len(pdf)):
            page = pdf[page_num]

            text = page.get_text()
            if text.strip():
                text_extractions.append(
                    {
                        "page_number": page_num + 1,
                        "content": text.strip(),
                    }
                )

            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_data = base_image["image"]

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{base_image['ext']}"
                ) as temp_file:
                    temp_file.write(image_data)
                    temp_file_path = temp_file.name

                parse_result = parse(temp_file_path)
                image_extractions.append(
                    {
                        "segmented_image_url": parse_result.get(
                            "segmented_image_url", ""
                        ),
                        "text": parse_result.get("text", ""),
                        "page_number": page_num + 1,
                        "image_index": img_index + 1,
                        "format": base_image["ext"],
                        "size": len(image_data),
                    }
                )
                os.unlink(temp_file_path)

        return {
            "metadata": {
                "file_name": file_path.split("/")[-1],
                "total_pages": len(pdf),
                "text_extractions_count": len(text_extractions),
                "image_extractions_count": len(image_extractions),
            },
            "text_extractions": text_extractions,
            "image_extractions": image_extractions,
        }


def parse_pdf_high_res(file_path: str) -> Dict[str, Any]:
    with fitz.open(file_path) as pdf:
        page_extractions: List[Dict[str, Any]] = []

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            temp_file = None

            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                img.save(temp_file.name, format="PNG")
                temp_file.close()

                parse_result = parse(temp_file.name)

                page_extraction = {
                    "page_number": page_num + 1,
                    "blocks": parse_result.get("blocks", []),
                    "segmented_image_url": parse_result.get("segmented_image_url", ""),
                }

                page_extractions.append(page_extraction)

            except Exception as e:
                print(f"Error processing page {page_num + 1}: {str(e)}")

            finally:
                if temp_file is not None:
                    try:
                        os.unlink(temp_file.name)
                    except Exception as e:
                        print(f"Error deleting temporary file: {str(e)}")

        return {
            "metadata": {
                "file_name": file_path.split("/")[-1],
                "total_pages": len(pdf),
                "pages_processed": len(page_extractions),
            },
            "page_extractions": page_extractions,
        }
