### 보고서 (발표 자료)
- [소상공인을 위한 온라인 콘텐츠 제작 서비스](https://drive.google.com/file/d/1x69WY5Waohpitvix3U2cmRzTAvKAihuU/view?usp=sharing)

### 협업일지
- 윤승호: [https://www.notion.so/yoonsnowdev/1d6219b29fc380a0b152d5457e2f4839?pvs=4](https://www.notion.so/1d6219b29fc380a0b152d5457e2f4839?pvs=21)
- 김민경: [https://endurable-ice-f3c.notion.site/Daily-268218930d5e80b59688f91293fb744c](https://www.notion.so/Daily-268218930d5e80b59688f91293fb744c?pvs=21)
- 김하늘: [https://www.notion.so/26906aa61633805c8115c3b58a0a42c4?source=copy_link](https://www.notion.so/26906aa61633805c8115c3b58a0a42c4?pvs=21)
- 방지형: [https://www.notion.so/237f89eac2f180dcbce8de3bb40cdd64?source=copy_link](https://www.notion.so/237f89eac2f180dcbce8de3bb40cdd64?pvs=21)
- 손주희: [https://www.notion.so/23846e2fcad880189b0ad50df0aea229?source=copy_link](https://www.notion.so/26846e2fcad880f799a3e4702d382700?pvs=21)

<br>
<br>
<br>


# 📌 프로젝트 개요
디지털 마케팅의 높은 장벽을 허무는 것을 목표로 합니다. IT 기기나 복잡한 설명서가 낯선 부모님 세대나 소상공인도, 단 몇 번의 클릭만으로 자신의 상황에 꼭 맞는 전문가 수준의 광고 콘텐츠를 즉시 생성할 수 있는 가장 직관적인 AI 서비스를 만듭니다.

### 해결하려는 문제
소상공인이나 시니어 세대는 마케팅의 필요성을 느끼지만, 시간 부족, 높은 비용, 복잡한 디지털 툴 사용의 어려움 때문에 효과적인 광고를 집행하지 못하고 있습니다.

### 타겟 유저
* 디지털 마케팅에 익숙하지 않은 50대 이상의 시니어 사장님
* 마케팅 전담 인력 없이 혼자서 모든 것을 해결해야 하는 1인 사업가

### 핵심 기능
* 초고품질 이미지 생성: 최신 FLUX.2 모델을 도입하여 실제 사진과 구분이 어려운 수준의 광고 이미지 제작
* 원클릭 광고 카피: GPT-4o 기반으로 인스타그램, 블로그, 당근마켓 등 채널별 맞춤 홍보 문구 자동 생성
* 직관적인 UI: 복잡한 프롬프트 입력 없이 버튼 클릭만으로 완성되는 사용자 경험

### 기대 효과
사용자는 더 이상 광고 문구를 고민하는 데 시간을 낭비하지 않고, 클릭 몇 번만으로 광고를 만들 수 있습니다. 이를 통해 마케팅 비용과 노력을 줄여 핵심 비즈니스에 더 집중할 수 있습니다.

### 기술 스택

- **언어:**
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
- **프레임워크:**
  ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
- **라이브러리:**
  ![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
  ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
  ![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=white)
- **도구:**
  ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)
  ![Notion](https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=notion&logoColor=white)
  ![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)

<br>
<br>

# ⚙️ 설치 및 실행 방법 (Docker 환경)
이 프로젝트는 RTX A6000 (48GB VRAM) 이상의 GPU 환경에 최적화되어 있으며, 단일 스크립트로 백엔드와 프론트엔드를 동시에 실행합니다. Docker를 통해 배포 환경을 표준화했습니다. 복잡한 라이브러리 설치 과정 없이 도커만 있으면 즉시 실행 가능합니다.

### 1. 사전 준비
1. **리포지토리 복제(Clone)**
    ```bash
    git clone [https://github.com/your-username/ad-generation-service.git](https://github.com/your-username/ad-generation-service.git)
    cd ad-generation-service
    ```

2. **환경 변수 설정(.env) 프로젝트 루트 경로에 `.env` 파일을 생성하고 키를 입력합니다.
    ```bash
    # .env 파일 생성
    vi .env
    ```
    `.env` 내용 예시
    ```bash
    OPENAI_API_KEY=sk-proj-...
    HF_TOKEN=hf_...
    ```
3. **Docker 실행**
    Docker Compose를 사용해 Backend(FastAPI)와 Frontend(Streamlit) 컨테이너를 동시에 빌드하고 실행합니다.
    1. 서비스 시작(Build & Run)
       ```bash
       docker compose up -d --build
       ```
       * `-d`: 백그라운드 실행
       * `--build`: 코드 변경 사항이 있을 경우 이미지를 새로 빌드
    2. 실행 상태 확인
       ```bash
       docker compose ps
       ```
       * `ad-project-backend`와 `ad-project-frontend` 상태가 `Up`이면 정상입니다.
    3. 로그 확인 (실시간)
       ```bash
       # 전체 로그 확인
       docker compose logs -f

       # 특정 서비스 로그만 확인
       docker compose logs -f backend
       docker compose logs -f frontend
       ```
4. **서비스 접속**
    브라우저를 열고 아래 주소로 접속합니다.
    * Frontend (서비스 화면): `http://localhost:8501`
    * Backend (API 문서): `http://localhost:9000/docs`

5. **서비스 종료**
    사용을 마친 후 컨테이너를 안전하게 종료합니다.
    ```bash
    docker compose down
    ```

<br>
<br>

# 📂 프로젝트 구조
기존의 복잡한 멀티 서버 구조를 통합해 관리 효율성을 높였습니다.
```bash
ad-generation-service/
├── start.sh                 # 전체 서비스(FE+BE) 원클릭 실행 스크립트
├── docker-compose.yml       # 도커 배포 설정 파일
├── Dockerfile               # 도커 이미지 빌드 설정
├── requirements.txt         # 통합 의존성 패키지 목록
├── .env                     # 환경 변수 (API Key 등)
└── src/
    ├── backend/             # FastAPI 서버 + AI 모델 엔진 (FLUX.1)
    │   ├── main.py          # 서버 진입점
    │   ├── services/        # 이미지/텍스트 생성 로직
    │   └── routers/         # API 엔드포인트
    └── frontend/            # Streamlit UI
        ├── app.py           # 앱 진입점
        └── pages/           # 화면별 페이지 코드
```

<br>
<br>

# 💡 데모 사이트
GCP 환경에서 배포된 데모 페이지입니다. (현재는 사용 불가능합니다.)

🔗 **Link:** **[http://34.123.118.58:8501/](http://34.123.118.58:8501/)**

---

### **로그인 정보**
| 구분 | 내용 |
|:---:|:---|
| 아이디 | `admin` |
| 비밀번호 | `1234` |

---

![서비스 메인 화면](image/OpenADProject_text.gif)

<br>
<br>

# 🤖 사용한 모델 및 라이선스
라이선스 규정을 준수하기 위해 각 모델의 사용 정책을 확인했습니다.

### 텍스트 생성 모델
* OpenAI GPT-4.0-mini
  * 빠르고 효율적인 텍스트 생성 모델로 광고 카피 및 마케팅 문구 작성에 사용됩니다.
  * 라이선스: OpenAI API 정책에 따름.

### 이미지 생성 모델
* FLUX.2 [dev]
  * 최신 Diffusion Transformer 기반의 고성능 이미지 생성 모델. 텍스트 이해도가 매우 높고 실사 표현이 뛰어납니다.
  * 4-bit Quantization (bitsandbytes) 적용, RTX A6000 네이티브 최적화 (CUDA).
  * 라이선스: FLUX.2-dev Non-Commercial License (비상업적 용도, 연구 및 테스트용)
