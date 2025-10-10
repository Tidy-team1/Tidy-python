import fitz  # PyMuPDF
import time  # 시간 측정을 위해 추가

def extract_pdf_content_info(pdf_path):
    start_time = time.time()  # 시작 시간 기록

    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"\n===== Page {page_num + 1} =====\n")

        # 1️⃣ 텍스트 추출 (dict 모드)
        print("--- 텍스트 ---")
        text_dict = page.get_text("dict")
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        print(f"텍스트: {span['text']}")
                        print(f"  폰트: {span['font']}, 크기: {span['size']}, 색상: {span['color']}")
                        print(f"  위치: {span['bbox']}\n")

        # 2️⃣ 도형 추출
        print("--- 도형 ---")
        drawings = page.get_drawings()
        for d in drawings:
            print(f"도형 bbox: {d['rect']}, 선 색상: {d.get('color')}, 채움 색상: {d.get('fill')}, 종류: {d['type']}")

        # 3️⃣ 이미지 위치/크기 정보 추출 (저장하지 않음)
        print("--- 이미지 ---")
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            width, height = pix.width, pix.height
            bbox = page.get_image_bbox(img)  # 이미지가 페이지에서 차지하는 영역
            print(f"이미지 {img_index}: 크기 = ({width}x{height}), 페이지 위치 = {bbox}")
            pix = None

    doc.close()

    end_time = time.time()    # 끝난 시간 기록
    elapsed_time = end_time - start_time  # 경과 시간 계산
    print(f"검사 소요 시간: {elapsed_time:.2f}초")  # 초 단위 출력

if __name__ == "__main__":
    pdf_file = "input/pdf/example.pdf"  # 테스트할 PDF 파일 경로
    extract_pdf_content_info(pdf_file)
