from pathlib import Path


# =================================================
# 이거 쓰려면 comtypes 설치 필요한데 도커에선 못 쓴다고 하네요 -> s3_utils의 load_slide_images로 대체
# =================================================
# def export_slide_images(pptx_path, output_dir):
#     """
#     Windows COM 객체를 사용하여 PPTX의 각 슬라이드를 PNG 이미지로 추출합니다.
#     (Windows 및 MS PowerPoint 설치 필요)
#     """
#     pptx_path = str(Path(pptx_path).resolve())
#     output_dir = Path(output_dir).resolve()
#     output_dir.mkdir(parents=True, exist_ok=True)

#     # powerpoint 객체 생성 (Visible = 1은 화면 표시를 안 한다는 의미)
#     powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
#     powerpoint.Visible = 1  

#     presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=True)

#     if len(presentation.Slides) == 0:
#         print(f"[ERROR] PPTX has no slides: {pptx_path}")
#         presentation.Close()
#         powerpoint.Quit()
#         return

#     for i, slide in enumerate(presentation.Slides, start=1):
#         # 파일명은 slide_1.png, slide_2.png 형태
#         out_file = (output_dir / f"slide_{i}.png").resolve()
#         # print(f"[INFO] Exporting slide {i} -> {out_file}")
#         try:
#             slide.Export(str(out_file), "PNG")
#         except Exception as e:
#             print(f"[ERROR] Failed to export slide {i}: {e}")

#     presentation.Close()
#     powerpoint.Quit()
#     # print("[INFO] Exported slide images →", output_dir)


def find_slide_image(slide_image_folder, slide_idx):
    """슬라이드 전체 이미지 파일명을 slide_1.png, slide_2.png로 찾음 (0-based index)"""
    # 파일 저장명 slide_1.png -> 0.png 형태로 변경됨
    slide_file = Path(slide_image_folder) / f"{slide_idx}.png"
    if slide_file.exists():
        return slide_file
    return None