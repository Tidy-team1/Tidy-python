from pathlib import Path
<<<<<<< HEAD


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
=======
import comtypes.client
import time
import os

def export_slide_images(pptx_path, output_dir):
    pptx_path = str(Path(pptx_path).resolve())
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
    # Visible=1 이어야 오류가 덜 남
    powerpoint.Visible = 1 

    try:
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False, ReadOnly=True)
        
        for i, slide in enumerate(presentation.Slides, start=1):
            out_file = output_dir / f"slide_{i}.png"
            
            # 이미 있으면 스킵 (속도 향상)
            if out_file.exists():
                continue
                
            # [중요] 해상도 지정 (너비, 높이) - 기본값보다 크게 해야 화질 좋음
            # Scale 2배 정도 (약 1920x1080)
            slide.Export(str(out_file), "PNG", 1920, 1080)
            
            # 파일이 생성될 때까지 잠깐 대기 (비동기 이슈 방지)
            retry = 0
            while not out_file.exists() and retry < 10:
                time.sleep(0.1)
                retry += 1

        presentation.Close()
    except Exception as e:
        print(f"[ERROR] PPT Export failed: {e}")
    finally:
        try:
            powerpoint.Quit()
        except:
            pass

def find_slide_image(slide_image_folder, slide_idx):
    # 0-based index -> 1-based filename
    slide_file = Path(slide_image_folder) / f"slide_{slide_idx+1}.png"
>>>>>>> 4c62c61 (pth 파일 업로드)
    if slide_file.exists():
        return slide_file
    return None