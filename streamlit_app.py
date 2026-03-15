import streamlit as st
import pandas as pd
from datetime import date
import json
from supabase import create_client, Client

# ==========================================
# --- 1. 初始化与配置 ---
# ==========================================
@st.cache_resource
def init_connection():
    """初始化 Supabase 客户端"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"连接配置错误: {e}")
        return None

supabase = init_connection()
DATE_FORMAT = "%Y-%m-%d"

# ==========================================
# --- 2. 核心逻辑函数 ---
# ==========================================
def check_login(username, password):
    """身份验证检查"""
    users = {
        "wangxiaoliang": {"password": "Yujia@003", "role": "scientific"},
        "pengyutao": {"password": "Yujia@002", "role": "scientific"},
        "zhoucuiying": {"password": "Yujia@001", "role": "finance"}
    }
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def load_data():
    """从 Supabase 加载数据"""
    try:
        response = supabase.table("samples").select("*").execute()
        data = response.data
        if data: 
            df = pd.DataFrame(data)
            df = df.fillna("") 
            cols_to_str = ["requirements", "completion_date", "sender", "sample_type", "progress", "invoice_status", "payment_status", "list_status", "uploaded_files"]
            for col in cols_to_str:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            return df.sort_values("id").reset_index(drop=True)
        else: 
            return pd.DataFrame(columns=[
                "id", "reception_date", "sender", "sample_type", "quantity",
                "progress", "requirements", "completion_date", "invoice_status", "payment_status", "list_status", "uploaded_files"
            ])
    except Exception as e:
        st.error(f"读取数据失败: {e}")
        return pd.DataFrame()

def save_data(df):
    """保存数据"""
    try:
        records = df.to_dict("records")
        if records:
            supabase.table("samples").upsert(records).execute()
    except Exception as e:
        st.error(f"保存数据失败: {e}")

def display_uploaded_files(files_json):
    """文件下载逻辑"""
    if pd.isna(files_json) or files_json == "[]" or not files_json:
        st.write("暂无上传文件。")
    else:
        try:
            files = json.loads(files_json)
            for file_info in files:
                public_url = supabase.storage.from_("uploads").get_public_url(file_info["filename"])
                st.markdown(f"[⬇️ 点击下载：{file_info['original_name']}]({public_url})")
        except:
            st.write("文件解析错误。")

# ==========================================
# --- 3. UI 页面函数 ---
# ==========================================

def login_page():
    """登录界面 - 已修正按钮至右下角"""
    st.markdown("""
    <style>
    /* 全局背景与布局 */
    [data-testid="stAppViewContainer"] {
        background-color: #e8f5e9 !important;
    }
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0);
    }
    .block-container {
        padding-top: 12vh !important;
        max-width: 600px !important;
    }

    /* 登录白框样式 */
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        padding: 40px !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        border: none !important;
    }

    /* --- 核心修改：强制按钮定位到右下角 --- */
    /* 1. 针对表单内的按钮容器 */
    div[data-testid="stFormSubmitButton"] {
        display: flex !important;
        justify-content: flex-end !important; /* 强制内容靠右 */
        margin-top: 30px !important;
    }
    
    /* 2. 针对按钮本身的样式微调 */
    div[data-testid="stFormSubmitButton"] button {
        width: 100px !important; /* 设定一个固定宽度，更像传统的登录按钮 */
        background-color: #1976D2 !important;
        color: white !important;
        border-radius: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 标题部分
    st.markdown("""
        <div style="text-align: center; width: 100%; margin-bottom: 30px;">
            <h1 style='color: #1976D2; font-family: "楷体", "KaiTi", serif; font-size: 30px; white-space: nowrap; margin: 0;'>
                玉佳生物科研业务管理系统
            </h1>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        
        # 这个按钮会被 CSS 自动推向右侧
        submit_button = st.form_submit_button("登录")
        
        if submit_button:
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("用户名或密码错误。")

def scientific_staff_page():
    """科研页面"""
    st.title(f"科研业务管理 - 欢迎，{st.session_state.username}")
    df = load_data()
    tab1, tab2, tab3 = st.tabs(["🆕 样品录入", "📋 样品概览", "📁 查看上传文件"])

    with tab1:
        st.subheader("录入新样品接收情况")
        with st.form("new_sample_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                reception_date = st.date_input("接收时间", value=date.today())
                sender = st.text_input("寄样人")
                sample_type = st.text_input("样品类型")
                quantity = st.number_input("样品数量", min_value=1, step=1)
            with col2
