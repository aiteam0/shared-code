import json
import os
import shutil
# import requests # 로컬 템플릿을 사용하므로 requests는 필요 없을 수 있습니다.
from huggingface_hub import snapshot_download

# 스크립트 위치를 기준으로 현재 디렉토리 정의
# __file__은 스크립트 파일의 경로를 나타냅니다.
try:
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: # 스크립트 파일이 아닌 인터랙티브 환경 등에서 실행될 경우
    CURRENT_DIR = os.getcwd() # 현재 작업 디렉토리를 사용
print(f"스크립트/작업 디렉토리: {CURRENT_DIR}")

# 모델 다운로드 기본 경로 설정 (현재 폴더 아래 models)
TARGET_MODEL_BASE_DIR = os.path.join(CURRENT_DIR, "models")
print(f"타겟 모델 기본 디렉토리: {TARGET_MODEL_BASE_DIR}")

# 기본 모델 디렉토리 생성 (이미 존재하면 무시)
os.makedirs(TARGET_MODEL_BASE_DIR, exist_ok=True)

# --- 로컬 템플릿 로드, 수정, 저장 함수 ---
def load_modify_save_json(template_filename, output_filename, modifications):
    """
    로컬 템플릿 JSON 파일을 로드하고, 내용을 수정한 후,
    지정된 출력 파일에 저장합니다.
    """
    data = {}
    if os.path.exists(template_filename):
        try:
            with open(template_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"구성 템플릿 로드 완료: {template_filename}")
        except json.JSONDecodeError:
            print(f"JSON 템플릿 읽기 오류: {template_filename}. 빈 설정으로 시작합니다.")
        except Exception as e:
            print(f"템플릿 로드 중 오류 발생 {template_filename}: {e}. 빈 설정으로 시작합니다.")
    else:
        print(f"템플릿 파일을 찾을 수 없습니다: {template_filename}. 빈 설정으로 시작합니다.")
        # 템플릿이 없으면 여기서 중단할지, 빈 설정으로 계속할지 결정
        # return # 주석 해제 시 템플릿 없으면 중단

    # 내용 수정 적용
    for key, value in modifications.items():
        data[key] = value
    print(f"수정 내용 적용 완료: {modifications}")

    # 수정된 내용 저장
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"구성 파일 저장 완료: {output_filename}")
    except Exception as e:
        print(f"구성 파일 저장 중 오류 발생 {output_filename}: {e}")

# --- 메인 실행 블록 ---
if __name__ == '__main__':

    # 1. PDF-Extract-Kit 모델 다운로드
    mineru_patterns = [
        # "models/Layout/LayoutLMv3/*",
        "models/Layout/YOLO/*",
        "models/MFD/YOLO/*",
        "models/MFR/unimernet_hf_small_2503/*",
        "models/OCR/paddleocr_torch/*",
        # "models/TabRec/TableMaster/*",
        # "models/TabRec/StructEqTable/*",
    ]
    print("PDF-Extract-Kit 모델 다운로드를 시작합니다...")
    # snapshot_download는 다운로드된 디렉토리의 절대 경로를 반환합니다.
    pdf_kit_download_dir = snapshot_download(
        'opendatalab/PDF-Extract-Kit-1.0',
        allow_patterns=mineru_patterns,
        local_dir=TARGET_MODEL_BASE_DIR, # ./models 디렉토리에 다운로드
        local_dir_use_symlinks=False     # 심볼릭 링크 대신 실제 파일 복사 (권장)
    )
    # 중요: 원본 스크립트는 다운로드된 내용 안에 'models' 하위 폴더가 있다고 가정했습니다.
    # 이 가정을 유지합니다. 설정 파일에 저장될 경로는 ./models/models가 됩니다.
    # 절대 경로 사용이 설정 파일에는 더 안정적입니다.
    final_pdf_kit_model_dir = os.path.join(pdf_kit_download_dir, 'models')
    print(f"PDF-Extract-Kit 다운로드 위치: {pdf_kit_download_dir}")
    print(f"PDF-Extract-Kit 설정용 유효 모델 경로: {final_pdf_kit_model_dir}")


    # 2. LayoutReader 모델 다운로드
    # 구성 관리를 위해 TARGET_MODEL_BASE_DIR 아래 하위 폴더에 저장
    layoutreader_target_subdir = os.path.join(TARGET_MODEL_BASE_DIR, "layoutreader")
    os.makedirs(layoutreader_target_subdir, exist_ok=True) # 하위 폴더 생성

    layoutreader_pattern = [
        "*.json",
        "*.safetensors",
    ]
    print("LayoutReader 모델 다운로드를 시작합니다...")
    layoutreader_model_dir = snapshot_download(
        'hantian/layoutreader',
        allow_patterns=layoutreader_pattern,
        local_dir=layoutreader_target_subdir, # ./models/layoutreader 디렉토리에 다운로드
        local_dir_use_symlinks=False
    )
    print(f"LayoutReader 모델 다운로드 위치: {layoutreader_model_dir}")


    # 3. (선택 사항) PaddleOCR 처리 - 원본과 동일하게 주석 처리 유지
    # paddleocr_model_dir = os.path.join(final_pdf_kit_model_dir, 'OCR', 'paddleocr') # pdf_kit 내 'models' 하위 폴더 기준 경로
    # user_paddleocr_dir = os.path.expanduser('~/.paddleocr')
    # if os.path.exists(user_paddleocr_dir):
    #     shutil.rmtree(user_paddleocr_dir)
    # if os.path.exists(paddleocr_model_dir): # 실제 다운로드되었는지 확인
    #    shutil.copytree(paddleocr_model_dir, user_paddleocr_dir)
    #    print(f"PaddleOCR 모델 복사 완료: {paddleocr_model_dir} -> {user_paddleocr_dir}")
    # else:
    #    print(f"PaddleOCR 디렉토리를 찾을 수 없습니다 ({paddleocr_model_dir}), 복사를 건너<0xEB><0x9B><0x8D>니다.")


    # 4. JSON 설정 파일 구성
    # 현재 디렉토리에 있는 로컬 템플릿 파일 사용
    json_template_file = os.path.join(CURRENT_DIR, 'magic-pdf.template.json')
    config_file_name = 'magic-pdf.json'
    # ***** 변경: 최종 설정 파일을 현재 디렉토리에 저장 *****
    config_file_output_path = os.path.join(CURRENT_DIR, config_file_name) # 홈 디렉토리 대신 CURRENT_DIR 사용

    # 설정에는 snapshot_download에서 반환된 절대 경로 사용
    json_mods = {
        'models-dir': final_pdf_kit_model_dir,          # 예: /path/to/script/models/models
        'layoutreader-model-dir': layoutreader_model_dir # 예: /path/to/script/models/layoutreader
    }

    print(f"구성 파일을 업데이트합니다: {config_file_output_path}") # 경로가 로컬 경로로 변경됨
    load_modify_save_json(json_template_file, config_file_output_path, json_mods)

    # 최종 확인 메시지
    print(f"--- 설정 요약 ---")
    print(f"PDF-Extract-Kit 모델 경로: {json_mods['models-dir']}")
    print(f"LayoutReader 모델 경로: {json_mods['layoutreader-model-dir']}")
    print(f"구성 파일 저장 위치: {config_file_output_path}") # 경로가 로컬 경로로 변경됨
    print(f"-----------------------------")