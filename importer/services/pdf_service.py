from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz


@dataclass
class ExtractedImage:
    page: int
    filename: str
    path: str
    placeholder: str


@dataclass
class PDFContent:
    text: str
    images: List[ExtractedImage]
    total_pages: int


class PDFService:

    def __init__(self, pdf_file):
        self.document = fitz.open(
            stream=pdf_file.read(),
            filetype="pdf",
        )

    @property
    def total_pages(self):
        return self.document.page_count

    def extract(
        self,
        start_page,
        end_page,
        image_output_dir,
    ):

        start = start_page - 1
        end = end_page - 1

        Path(image_output_dir).mkdir(
            parents=True,
            exist_ok=True,
        )

        lesson = []

        images = []

        image_counter = 1

        for page_number in range(start, end + 1):

            page = self.document.load_page(page_number)

            text = page.get_text("text").strip()

            if text:

                lesson.append(text)

            page_images = page.get_images(full=True)

            for image in page_images:

                xref = image[0]

                info = self.document.extract_image(xref)

                extension = info["ext"]

                filename = (
                    f"page_{page_number+1}_image_{image_counter}.{extension}"
                )

                filepath = (
                    Path(image_output_dir) / filename
                )

                with open(filepath, "wb") as file:

                    file.write(info["image"])

                placeholder = f"[IMAGE_{image_counter}]"

                lesson.append(placeholder)

                images.append(

                    ExtractedImage(

                        page=page_number + 1,

                        filename=filename,

                        path=str(filepath),

                        placeholder=placeholder,

                    )

                )

                image_counter += 1

        return PDFContent(

            text="\n\n".join(lesson),

            images=images,

            total_pages=self.total_pages,

        )