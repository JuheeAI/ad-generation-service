import os
from pathlib import Path
import streamlit as st


CURRENT_DIR = Path(__file__).parent.resolve()
PAGES_DIR = CURRENT_DIR / "pages"

ASSETS_DIR = CURRENT_DIR.parent.parent / "assets" 

def setup_page() -> None:
    """
    전역 페이지 설정
    """
    icon_path = str(ASSETS_DIR / "OAP.jpg")
    logo_path = str(ASSETS_DIR / "logo.png")
    
    if not (ASSETS_DIR / "OAP.jpg").exists():
        icon_path = None
    
    st.set_page_config(page_title="OpenADProject", page_icon=icon_path)
    
    try:
        if (ASSETS_DIR / "logo.png").exists():
            st.logo(logo_path, size="large")
    except Exception:
        pass

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            padding-left: 4rem;
            padding-right: 4rem;
            max-width: 80%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_sidebar_status():
    with st.sidebar:
        if "access_token" in st.session_state:
            user_id = st.session_state.get("username", "사용자")
            st.markdown(f"**{user_id}님** 환영합니다!🤗")
            if st.button("로그아웃", type="primary", width="stretch", icon=":material/logout:"):
                st.session_state.pop("access_token", None)
                st.rerun()

def build_pages() -> dict:
    """
    네비게이션 페이지 구성
    st.Page() 안에 str(PAGES_DIR / "파일명.py") 사용하여
    절대 경로로 파일을 지정합니다.
    """
    is_logged_in = bool(st.session_state.get("access_token"))

    def page_path(filename):
        return str(PAGES_DIR / filename)

    if not is_logged_in:
        return {
            "🔐 Auth": [
                st.Page(page_path("login_page.py"), title="로그인", icon=":material/login:"),
                st.Page(page_path("signup_page.py"), title="회원가입", icon=":material/account_circle:"),
            ]
        }

    return {
        "🏠 Home": [
            st.Page(page_path("main_page.py"), title="메인 페이지", icon=":material/dashboard:"),
        ],
        "📷 이미지 생성": [
            st.Page(page_path("image_main_page.py"), title="이미지 생성 가이드", icon=":material/menu_book:"),
            st.Page(page_path("image_insta_page.py"), title="인스타그램", icon=":material/numbers:"),
        ],
        "✏️ 광고문구 생성": [
            st.Page(page_path("text_main_page.py"), title="광고 문구 가이드", icon=":material/menu_book:"),
            st.Page(page_path("text_insta_page.py"), title="인스타그램 / 네이버 플레이스", icon=":material/numbers:"),
            st.Page(page_path("text_community_page.py"), title="당근마켓 / 지역카페", icon=":material/diversity_1:"),
        ],
        "📁 보관함": [
            st.Page(page_path("history_image_page.py"), title="이미지 보관함", icon=":material/image:"),
            st.Page(page_path("history_text_page.py"), title="광고문구 보관함", icon=":material/border_color:"),
            st.Page(page_path("history_model_page.py"), title="모델 보관함", icon=":material/sentiment_satisfied:"),
        ],
    }

def run_navigation(pages: dict) -> None:
    pg = st.navigation(pages)
    pg.run()

def main() -> None:
    setup_page()
    render_sidebar_status() 
    pages = build_pages()
    run_navigation(pages)

if __name__ == "__main__":
    main()