import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
from supabase import create_client, Client
import urllib.parse # 用于转义 SVG 字符串

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
    """登录界面 (已应用淡黄色 SVG 文字水印背景与 Logo 融合)"""

    # --- 核心：定义 SVG 水印模式 ---
    # 定义小篆（这里用 Web 安全字体模拟，最好提供字体文件）、黑体、行书（用楷体模拟）
    # 24px, 白色, 逆时针45度 (即旋转 -45度)
    # 增加一点透明度让它更像水印 (opactiy="0.3")
    svg_pattern = """
    <svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
        <style>
            .watermark { 
                fill: white; 
                font-size: 48px; 
                opacity: 0.3; /* 水印透明度 */
                text-anchor: middle;
            }
            /* 模拟小篆：通常需要专用字体，这里用 Google Fonts 或本地字体，若无则显示为衬线体 */
            .xiaozhuan { font-family: "STXingkai", "华文行楷", "KaiTi", serif; font-weight: bold; } 
            .heiti { font-family: "SimHei", "黑体", sans-serif; font-weight: bold; }
            .xingshu { font-family: "KaiTi", "楷体", serif; }
        </style>
        
        <text x="75" y="75" transform="rotate(-45 75 75)" class="watermark xiaozhuan">玉佳</text>
        
        <text x="225" y="75" transform="rotate(-45 225 75)" class="watermark heiti">玉佳</text>
        
        <text x="75" y="225" transform="rotate(-45 75 225)" class="watermark xingshu">玉佳</text>
        
        <text x="225" y="225" transform="rotate(-45 225 225)" class="watermark xiaozhuan">玉佳</text>
        
    </svg>
    """
    # 将 SVG 字符串转义为 CSS 可用的 URL 格式
    svg_data_url = f"data:image/svg+xml;charset=utf-8,{urllib.parse.quote(svg_pattern)}"

    st.markdown(f"""
        <style>
        /* 1. 全屏背景：淡黄色 + SVG 文字水印 */
        .stApp {{
            /* 1.1 背景色：淡黄色 (和图片一致) */
            background-color: #FEF9C3 !important; /* Tailwind yellow-100, 柔和的淡黄色 */
            
            /* 1.2 背景图片：平铺的 SVG 水印 */
            background-image: url("{svg_data_url}") !important;
            background-repeat: repeat !important;
            background-position: center !important;
            background-attachment: fixed !important; /* 固定背景，文字滚动时水印不动 */
        }}
        
        /* 2. 透明页眉 */
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        /* 3. 巨型标题美化 - 72px，深蓝色以增强对比 */
        .login-title {{
            color: #0047AB !important; /* 科博尔特蓝，更稳重 */
            text-align: center;
            font-size: 72px; 
            font-family: "楷体", "KaiTi", serif;
            font-weight: bold;
            margin-top: -10px; /* 紧贴 Logo 下方，略微上移 */
            margin-bottom: 50px;
            white-space: nowrap; 
            text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8); /* 增加白色阴影提升可读性 */
        }}
        
        /* 4. 输入框标签左对齐 */
        .stTextInput label {{
            display: flex;
            justify-content: flex-start; 
            font-size: 1.1rem;
            color: #333; 
            font-weight: bold;
        }}
        
        /* 5. 登录框美化：600px 限制、居中、半透明白色（毛玻璃效果） */
        [data-testid="stForm"] {{
            background-color: rgba(255, 255, 255, 0.7) !important; /* 稍提高透明度，让背景水印隐约可见 */
            backdrop-filter: blur(10px); /* 模糊效果 */
            -webkit-backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.2); /* 减弱阴影颜色 */
            border: 1px solid rgba(255, 255, 255, 0.4);
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
            position: relative; /* 确保在背景之上 */
            z-index: 1;
        }}
        
        /* 6. 登录按钮立体效果 (保持蓝宝石色渐变) */
        div[data-testid="stFormSubmitButton"] > button {{
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
        }}
        
        div[data-testid="stFormSubmitButton"] > button:active {{
            box-shadow: 0 2px 0 #0D47A1, 0 4px 6px rgba(0, 0, 0, 0.2) !important;
            transform: translateY(3px) !important;
        }}

        /* 7. Logo 径向渐变容器：为了更好地融合，我们将渐变中心设为淡黄色 */
        .logo-gradient-container {{
            width: 380px; /* 容器稍大于 Logo 宽度 */
            height: auto;
            margin-left: auto;
            margin-right: auto;
            /* 核心：径向渐变，从中心完全透明（显示Logo）过度到背景的淡黄色 */
            /* 这样 Logo 的白色边缘会自然过度到淡黄色背景，而不是突兀的白色 */
            background: radial-gradient(circle, rgba(254,249,195,0) 30%, rgba(254,249,195,0.7) 50%, rgba(254,249,195,1) 70%);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px; /* 增加内边距 */
            border-radius: 50%; /* 圆形容器 */
        }}

        /* 8. Logo 混合模式：保持正片叠底，去除 Logo 本身的白色背景 */
        .merged-logo {{
            width: 320px;
            mix-blend-mode: multiply; 
            display: block;
        }}
        </style>
    """, unsafe_allow_html=True)

    # === Logo与标题部分 ===
    logo_url = "https://hporhdgbqajajdbefynt.supabase.co/storage/v1/object/public/Yujia/Yujia.png"
    st.markdown(f"""
        <div style="text-align: center; margin-top: 2rem; position: relative; z-index: 1;">
            <div class="logo-gradient-container">
                <img src="{logo_url}" class="merged-logo" />
            </div>
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
        st.write("欢迎进入系统！(这里是你原有的主页逻辑)")
        # ... 保持你原有的逻辑 ...
