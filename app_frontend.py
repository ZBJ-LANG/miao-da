import streamlit as st
import requests
import uuid
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

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


def api_register(username: str, password: str, email: str = None):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={"username": username, "password": password, "email": email},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            return {"error": response.json().get("detail", "注册失败")}
        return {"error": "注册失败"}
    except Exception as e:
        return {"error": str(e)}


def api_login(username: str, password: str):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"error": "用户名或密码错误"}
        return {"error": "登录失败"}
    except Exception as e:
        return {"error": str(e)}


def api_chat(message: str, user_id: str = "default", session_id: str = None):
    try:
        payload = {"message": message, "user_id": user_id, "session_id": session_id}
        response = requests.post(f"{API_BASE_URL}/api/chat/", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        return {"error": "请求失败"}
    except Exception as e:
        return {"error": str(e)}


def api_search(keyword: str, user_id: str = "default"):
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/search/",
            json={"message": keyword, "user_id": user_id},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return {"items": [], "error": "搜索失败"}
    except Exception as e:
        return {"items": [], "error": str(e)}


def api_get_products(category: str = None, limit: int = 20):
    try:
        if category:
            response = requests.get(
                f"{API_BASE_URL}/api/products/category/{category}?limit={limit}",
                timeout=10
            )
        else:
            response = requests.get(
                f"{API_BASE_URL}/api/products/count/all",
                timeout=10
            )
        if response.status_code == 200:
            return response.json()
        return {"error": "获取商品失败"}
    except:
        return {"error": "获取商品失败"}


def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None


def render_sidebar():
    with st.sidebar:
        st.title("👗 智能服装穿搭助手")

        backend_status = check_backend()
        if backend_status:
            st.success("✅ 后端服务已连接")
        else:
            st.error("❌ 后端服务未连接")
            st.info("请确保后端服务正在运行")

        st.divider()

        menu = ["首页", "AI穿搭推荐", "商品浏览", "个人中心"]
        choice = st.radio("功能菜单", menu, index=0)

        return choice


def render_home():
    st.title("👗 欢迎使用智能服装穿搭助手")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🤖 AI智能推荐")
        st.write("基于阿里云通义千问大模型，为您提供专业的穿搭建议")
        st.image("https://img.alicdn.com/imgextra/i4/1924119553/O1CN01N7qEst2KRKD6zfMVz_!!1924119553.jpg",
                 use_container_width=True)

    with col2:
        st.markdown("### 🎯 核心功能")
        st.write("• AI智能穿搭推荐")
        st.write("• 图片搜索相似商品")
        st.write("• 虚拟试穿效果预览")
        st.write("• 个性化衣橱管理")
        st.write("• 天气穿衣建议")

    st.divider()

    st.markdown("### 📊 系统状态")
    if check_backend():
        st.success("后端服务：已连接")
        try:
            count_data = api_get_products()
            if "count" in count_data:
                st.info(f"商品总数：{count_data['count']}")
        except:
            pass
    else:
        st.error("后端服务：未连接")


def render_chat():
    st.title("💬 AI穿搭推荐")

    init_session()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    message = st.text_input("请描述您想要的穿搭风格或场景：", key="chat_input")

    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("发送", type="primary")
    with col2:
        clear_button = st.button("清空对话")

    if clear_button:
        st.session_state.chat_history = []
        st.rerun()

    if send_button and message:
        with st.spinner("AI正在分析..."):
            result = api_chat(message, st.session_state.user_id, st.session_state.session_id)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.chat_history.append({
                    "user": message,
                    "assistant": result
                })

    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["user"])

        with st.chat_message("assistant"):
            if "items" in chat["assistant"] and chat["assistant"]["items"]:
                st.write(chat["assistant"].get("message", "为您找到以下商品推荐："))

                items = chat["assistant"]["items"][:6]
                cols = st.columns(3)
                for idx, item in enumerate(items):
                    with cols[idx % 3]:
                        st.image(item.get("image_url", ""), width=150)
                        st.caption(item.get("name", ""))
                        st.caption(f"¥{item.get('price', 0)}")
            else:
                st.write(chat["assistant"].get("message", "抱歉，暂时没有找到合适的推荐。"))


def render_products():
    st.title("🛍️ 商品浏览")

    categories = ["全部", "上衣", "下装", "连衣裙", "鞋子", "配件"]
    selected = st.selectbox("选择分类", categories)

    if selected == "全部":
        category = None
    else:
        category = selected

    with st.spinner("加载商品..."):
        result = api_get_products(category)

    if "error" in result:
        st.error(result["error"])
    else:
        if isinstance(result, list) and len(result) > 0:
            st.success(f"找到 {len(result)} 件商品")

            cols = st.columns(4)
            for idx, product in enumerate(result):
                with cols[idx % 4]:
                    st.image(product.get("image_url", ""), width=150)
                    st.caption(product.get("name", ""))
                    st.caption(f"¥{product.get('price', 0)}")
        else:
            st.info("暂无商品数据")


def render_profile():
    st.title("👤 个人中心")

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["登录", "注册"])

        with tab1:
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            if st.button("登录", type="primary"):
                if username and password:
                    result = api_login(username, password)
                    if "error" not in result:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = result.get("id", "default")
                        st.success("登录成功！")
                        st.rerun()
                    else:
                        st.error(result["error"])
                else:
                    st.warning("请输入用户名和密码")

        with tab2:
            new_username = st.text_input("用户名", key="register_username")
            new_password = st.text_input("密码", type="password", key="register_password")
            new_email = st.text_input("邮箱（可选）", key="register_email")
            if st.button("注册", type="primary"):
                if new_username and new_password:
                    result = api_register(new_username, new_password, new_email)
                    if "error" not in result:
                        st.success("注册成功，请登录！")
                    else:
                        st.error(result["error"])
                else:
                    st.warning("请输入用户名和密码")
    else:
        st.success(f"当前用户：{st.session_state.username}")

        if st.button("退出登录"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = "default"
            st.rerun()

        st.divider()
        st.markdown("### 用户设置")
        st.info("更多功能开发中...")


def main():
    init_session()
    choice = render_sidebar()

    if choice == "首页":
        render_home()
    elif choice == "AI穿搭推荐":
        render_chat()
    elif choice == "商品浏览":
        render_products()
    elif choice == "个人中心":
        render_profile()


if __name__ == "__main__":
    main()
