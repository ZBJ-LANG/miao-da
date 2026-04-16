import streamlit as st
import requests
import uuid
import base64
from datetime import datetime

API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="智能服装穿搭助手",
    page_icon="👗",
    layout="wide"
)


def check_backend():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def init_session_state():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'is_logged_in' not in st.session_state:
        st.session_state.is_logged_in = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state.messages = []


init_session_state()


def show_login_page():
    st.title("👗 智能服装穿搭助手")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 登录", "📝 注册"])
    
    with tab1:
        with st.form("login_form", clear_on_submit=True):
            st.subheader("用户登录")
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                submitted = st.form_submit_button("登录", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.warning("请输入用户名和密码")
                else:
                    st.info("登录功能需要后端服务支持")
    
    with tab2:
        with st.form("register_form", clear_on_submit=True):
            st.subheader("新用户注册")
            new_username = st.text_input("用户名", placeholder="请输入用户名")
            new_password = st.text_input("密码", type="password", placeholder="请输入密码")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            email = st.text_input("邮箱（选填）", placeholder="请输入邮箱")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                submitted = st.form_submit_button("注册", use_container_width=True)
            
            if submitted:
                if not new_username or not new_password:
                    st.warning("请输入用户名和密码")
                elif new_password != confirm_password:
                    st.error("两次输入的密码不一致")
                elif len(new_password) < 6:
                    st.warning("密码长度至少6位")
                else:
                    st.info("注册功能需要后端服务支持")
    
    st.markdown("---")
    st.markdown("##### 💡 提示：注册后首次登录需要填写您的体型信息，以便我们为您提供更精准的穿搭推荐。")


def show_main_app():
    backend_online = check_backend()
    if not backend_online:
        st.warning("⚠️ 后端服务未连接，请确保 FastAPI 服务正在运行")
    
    st.title("👗 智能服装穿搭助手")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("退出登录", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    st.markdown("---")
    
    page = st.sidebar.radio(
        "功能菜单",
        ["💬 AI对话", "👔 虚拟衣橱", "👤 个人信息"],
        index=0
    )
    
    if page == "💬 AI对话":
        show_chat_page()
    elif page == "👔 虚拟衣橱":
        show_wardrobe_page()
    elif page == "👤 个人信息":
        show_profile_page()


def show_chat_page():
    st.header("💬 AI穿搭对话")
    
    st.info("📍 当前用户信息: 请先登录以获取个性化推荐")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_input = st.text_input(
            "请输入您的需求",
            placeholder="例如: 推荐一套商务休闲搭配",
            key="chat_input"
        )
        image_url_input = st.text_input(
            "📷 可选：输入图片URL（AI会根据图片风格辅助搜索）",
            placeholder="https://example.com/image.jpg",
            key="image_url_input"
        )
        uploaded_file = st.file_uploader(
            "或上传本地图片文件",
            type=['jpg', 'jpeg', 'png', 'webp'],
            key="chat_image_uploader"
        )
        if uploaded_file:
            st.image(uploaded_file, caption="已上传图片", width=150)
    
    with col2:
        st.write("")
        st.write("")
        send_button = st.button("发送 ✈️", type="primary")
    
    if send_button and user_input:
        st.info("AI对话功能需要后端服务支持")
    
    st.divider()
    st.subheader("对话历史")
    
    if not st.session_state.messages:
        st.info("👆 请在上方输入您的穿搭需求，我会为您推荐合适的搭配或搜索商品！")


def show_wardrobe_page():
    st.header("👔 我的虚拟衣橱")
    st.info("虚拟衣橱功能需要后端服务支持")


def show_profile_page():
    st.header("👤 个人信息")
    st.info("个人信息功能需要后端服务支持")


if __name__ == "__main__":
    # 直接检查和设置 session_state 属性
    if 'is_logged_in' not in st.session_state:
        st.session_state['is_logged_in'] = False
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None
    if 'user_info' not in st.session_state:
        st.session_state['user_info'] = None
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    
    if not st.session_state.get('is_logged_in', False):
        show_login_page()
    else:
        show_main_app()