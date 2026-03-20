import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
from supabase import create_client, Client

# ==========================================
# --- 1. 初始化与配置 (必须是第一个 Streamlit 调用) ---
# ==========================================
st.set_page_config(page_title="玉佳生物科研业务管理系统", layout="wide")

@st.cache_resource
def init_connection():
    """初始化 Supabase 客户端"""
    try:
        # 确保在 Streamlit Cloud 的 Secrets 中配置了这两个变量
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"连接配置错误: {e}")
        return None

supabase = init_connection()
DATE_FORMAT = "%Y-%m-%d"

# ==========================================
# --- 2. 核心逻辑函数 (保持原样) ---
# ==========================================
def check_login(username, password):
    """身份验证检查"""
    # 实际生产中请使用 Supabase Auth 或哈希密码
    users = {
        "wxl": {"password": "123", "role": "scientific"},
        "pyt": {"password": "123", "role": "scientific"},
        "zcy": {"password": "123", "role": "finance"}
    }
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def load_data():
    """从 Supabase 加载样品数据 (防崩溃版)"""
    std_cols = [
        "id", "reception_date", "sender", "sender_company", "sample_type", "quantity",
        "progress", "requirements", "completion_date", "invoice_status", 
        "invoice_amount", "payment_status", "list_status", "uploaded_files"
    ]
    try:
        response = supabase.table("samples").select("*").execute()
        data = response.data
        
        if data: 
            df = pd.DataFrame(data)
        else: 
            df = pd.DataFrame(columns=std_cols)
            
        # 自愈机制：补齐缺失列
        for col in std_cols:
            if col not in df.columns:
                df[col] = ""
                
        df = df.fillna("") 
        # 强制转换特定列为字符串以供 data_editor 使用
        cols_to_str = ["requirements", "completion_date", "sender", "sender_company", "sample_type", "progress", "invoice_status", "invoice_amount", "payment_status", "list_status", "uploaded_files"]
        for col in cols_to_str:
            df[col] = df[col].astype(str)
            
        return df.sort_values("id").reset_index(drop=True)
    except Exception as e:
        st.error(f"读取样品数据失败: {e}")
        return pd.DataFrame(columns=std_cols)

def save_data(df):
    """保存样品数据"""
    try:
        records = df.to_dict("records")
        if records:
            supabase.table("samples").upsert(records).execute()
    except Exception as e:
        st.error(f"保存样品数据失败: {e}")

def load_transactions():
    """从 Supabase 加载财务流水数据 (防崩溃版)"""
    std_cols = ["id", "type", "date", "project", "amount", "source", "operator", "remarks", "invoice_files"]
    try:
        response = supabase.table("transactions").select("*").execute()
        data = response.data
        
        if data:
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame(columns=std_cols)
            
        # 自愈机制
        for col in std_cols:
            if col not in df.columns:
                df[col] = ""
                
        df = df.fillna("")
        return df.sort_values("id", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"读取流水数据失败: {e}")
        return pd.DataFrame(columns=std_cols)

def save_transactions(df):
    """保存财务流水数据"""
    try:
        records = df.to_dict("records")
        if records:
            supabase.table("transactions").upsert(records).execute()
    except Exception as e:
        st.error(f"保存流水数据失败: {e}")

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
    """登录界面 (已应用天蓝色背景与Logo融合技术)"""
    st.markdown("""
        <style>
        /* 1. 全屏背景颜色：天蓝色 */
        .stApp {
            background-color: #87CEEB !important; /* 天蓝色 SkyBlue */
            background-image: none !important; /* 确保移除任何背景图片 */
        }
        
        /* 2. 透明页眉 */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* 3. 巨型标题美化 - 72px，深蓝色以增强对比 */
        .login-title {
            color: #0047AB !important; /* 科博尔特蓝，更稳重 */
            text-align: center;
            font-size: 72px; 
            font-family: "楷体", "KaiTi", serif;
            font-weight: bold;
            margin-top: 10px; /* 紧贴 Logo 下方 */
            margin-bottom: 50px;
            white-space: nowrap; 
            text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.5); /* 增加白色阴影提升可读性 */
        }
        
        /* 4. 输入框标签左对齐 */
        .stTextInput label {
            display: flex;
            justify-content: flex-start; 
            font-size: 1.1rem;
            color: #333; 
            font-weight: bold;
        }
        
        /* 5. 登录框美化：600px 限制、居中、半透明白色（毛玻璃效果） */
        [data-testid="stForm"] {
            background-color: rgba(255, 255, 255, 0.6) !important; /* 稍提高透明度 */
            backdrop-filter: blur(15px); /* 增强毛玻璃模糊 */
            -webkit-backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.3); /* 减弱阴影颜色，更柔和 */
            border: 1px solid rgba(255, 255, 255, 0.5);
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* 6. 登录按钮立体效果 (保持蓝宝石色渐变) */
        div[data-testid="stFormSubmitButton"] > button {
            background-image: linear-gradient(180deg, #1E88E5 0%, #1565C0 100%) !important;
            color: white !important;
            border: 1px solid #0D47A1 !important;
            border-top: 1px solid #64B5F6 !important;
            border-radius: 12px !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            padding: 10px 24px !important;
            box-shadow: 0 5px 0 #0D47A1, 0 8px 15px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.1s ease !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:active {
            box-shadow: 0 2px 0 #0D47A1, 0 4px 6px rgba(0, 0, 0, 0.2) !important;
            transform: translateY(3px) !important;
        }

        /* 7. Logo 融合技术：去除图片白色背景 */
        .merged-logo {
            width: 320px;
            /* 核心：将图片与天蓝色背景进行正片叠底，使白色变透明 */
            mix-blend-mode: multiply; 
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
    """, unsafe_allow_html=True)

    # === Logo与标题部分 ===
    logo_url = "https://hporhdgbqajajdbefynt.supabase.co/storage/v1/object/public/Yujia/unnamed.jpg"
    st.markdown(f"""
        <div style="text-align: center; margin-top: 2rem;">
            <img src="{logo_url}" class="merged-logo" />
            <div class='login-title'>玉佳生物科研业务管理系统</div>
        </div>
    """, unsafe_allow_html=True)

    # === 登录表单部分 ===
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        
        st.write("") 
        
        # 按钮居中布局
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1.2, 1])
        with btn_col2:
            # use_container_width=True 让按钮铺满这一列
            submit_button = st.form_submit_button("登录", use_container_width=True)
        
        if submit_button:
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("用户名或密码错误。")

# ==========================================
# --- 4. 应用程序主入口 (保持原样) ---
# ==========================================
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None

    if not st.session_state.logged_in:
        login_page()
    else:
        # 登录后的导航和页面逻辑 (省略，保持你原有的逻辑即可)
        st.sidebar.title("玉佳生物业务管理系统")
        st.sidebar.markdown(f"**用户:** {st.session_state.username}")
        # ...
