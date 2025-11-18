from fastapi import FastAPI, UploadFile, File
import shutil
import os
from app.services.ppt_to_pdf import convert_ppt_to_pdf
from app.services.pdf_to_images import convert_pdf_to_images

app = FastAPI()

TEMP_DIR = "./temp"
OUTPUT_DIR = "./output"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.post("/convert-ppt")
async def convert_ppt(file: UploadFile = File(...)):
    # 1. temp에 파일 저장
    input_path = os.path.join(TEMP_DIR, file.filename)
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 2. PPT → PDF
    pdf_path = convert_ppt_to_pdf(input_path, TEMP_DIR)

    # 3. PDF → 이미지
    images = convert_pdf_to_images(pdf_path, OUTPUT_DIR)

    return {"pages": images}
