from enum import Enum


class BoxClassification(Enum):
    BLURB = "Short Text"
    CAPTION = "Caption"
    IMAGE = "Image"
    LIST = "List"
    PARAGRAPH = "Paragraph"
    TABLE = "Table"
    TITLE = "Title/Subtitle"
    UNCLASSIFIED = "Unclassified Text"
