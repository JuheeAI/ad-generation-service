import os

# =========================================================
# [설정] 여기에 합치고 싶은 파일 확장자와 무시할 폴더를 적으세요
# =========================================================
ALLOWED_EXTENSIONS = {'.py', '.sh', '.txt', '.md', '.toml', '.yml', '.yaml', '.dockerignore', 'Dockerfile'}
IGNORE_DIRS = {
    '.git', '__pycache__', 'venv', 'env', '.ipynb_checkpoints', 
    'outputs', 'data', 'images', 'test_folder', # 결과물이나 데이터 폴더는 제외
    'node_modules' # 프론트엔드 라이브러리 제외
}
OUTPUT_FILE = "full_project_code.txt"

def is_text_file(filename):
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS) or filename == 'Dockerfile'

def merge_files():
    current_dir = os.getcwd()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # 프로젝트 구조(Tree) 먼저 기록
        outfile.write(f"=== PROJECT STRUCTURE ROOT: {current_dir} ===\n")
        for root, dirs, files in os.walk(current_dir):
            # 무시할 폴더 제거
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            level = root.replace(current_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if is_text_file(f):
                    outfile.write(f"{subindent}{f}\n")
        
        outfile.write("\n\n" + "="*80 + "\n\n")

        # 실제 파일 내용 기록
        for root, dirs, files in os.walk(current_dir):
            # 무시할 폴더 제거
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if is_text_file(file) and file != 'merge_project.py' and file != OUTPUT_FILE:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, current_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                            # 구분선과 파일명 기록
                            outfile.write(f"\n{'='*80}\n")
                            outfile.write(f"FILE PATH: {rel_path}\n")
                            outfile.write(f"{'='*80}\n\n")
                            
                            outfile.write(content)
                            outfile.write("\n")
                            print(f"✅ Added: {rel_path}")
                    except Exception as e:
                        print(f"⚠️ Skipping {rel_path}: {e}")

    print(f"\n🎉 완료! 모든 코드가 '{OUTPUT_FILE}'에 저장되었습니다.")

if __name__ == "__main__":
    merge_files()