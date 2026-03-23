import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
from supabase import create_client, Client
import urllib.parse 

# ==========================================
# --- 1. 初始化与配置 ---
# ==========================================
st.set_page_config(page_title="玉佳生物科研业务管理系统", layout="wide")

@st.cache_resource
def init_connection():
    """初始化 Supabase 客户端"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"连接配置错误: 请检查 Streamlit Secrets 中是否配置了 SUPABASE_URL 和 KEY。错误信息: {e}")
        return None

supabase = init_connection()

# ==========================================
# --- 2. 核心逻辑函数 ---
# ==========================================
def check_login(username, password):
    """身份验证检查"""
    users = {
        "wxl": {"password": "123", "role": "scientific"},
        "pyt": {"password": "123", "role": "scientific"},
        "zcy": {"password": "123", "role": "finance"}
    }
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def load_data():
    """加载样品数据"""
    std_cols = ["id", "reception_date", "sender", "sender_company", "sample_type", "quantity", "progress", "requirements", "completion_date", "invoice_status", "invoice_amount", "payment_status", "list_status", "uploaded_files"]
    try:
        response = supabase.table("samples").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=std_cols)
        for col in std_cols:
            if col not in df.columns: df[col] = ""
        return df.sort_values("id").reset_index(drop=True)
    except Exception as e:
        st.error(f"加载失败: {e}")
        return pd.DataFrame(columns=std_cols)

def load_transactions():
    """加载财务流水数据"""
    std_cols = ["id", "type", "date", "project", "amount", "source", "operator", "remarks", "invoice_files"]
    try:
        response = supabase.table("transactions").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=std_cols)
        for col in std_cols:
            if col not in df.columns: df[col] = ""
        return df.sort_values("id", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.error(f"财务加载失败: {e}")
        return pd.DataFrame(columns=std_cols)

# ==========================================
# --- 3. UI 页面函数 ---
# ==========================================

def login_page():
    """登录界面"""
    svg_pattern = """
    <svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
        <style>.watermark { fill: white; font-size: 48px; opacity: 0.3; text-anchor: middle; font-family: "KaiTi", serif; }</style>
        <text x="75" y="75" transform="rotate(-45 75 75)" class="watermark">玉佳</text>
        <text x="225" y="225" transform="rotate(-45 225 225)" class="watermark">玉佳</text>
    </svg>
    """
    svg_data_url = f"data:image/svg+xml;charset=utf-8,{urllib.parse.quote(svg_pattern)}"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: #FEF9C3 !important; background-image: url("{svg_data_url}") !important; background-repeat: repeat !important; }}
        .login-title {{ color: #0047AB; text-align: center; font-size: 60px; font-family: "KaiTi"; font-weight: bold; margin-bottom: 30px; }}
        [data-testid="stForm"] {{ background-color: rgba(255, 255, 255, 0.7) !important; backdrop-filter: blur(10px); border-radius: 20px; padding: 40px; max-width: 600px; margin: auto; }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-title'>玉佳生物科研管理系统</div>", unsafe_allow_html=True)

    with st.form("login_form"):
        u = st.text_input("用户名")
        p = st.text_input("密码", type="password")
        if st.form_submit_button("登录", use_container_width=True):
            role = check_login(u, p)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.role = role
                st.rerun()
            else:
                st.error("账号或密码错误")

# ==========================================
# --- 4. 业务页面逻辑 ---
# ==========================================

def main_app():
    """登录后的主程序内容"""
    # 侧边栏设置
    st.sidebar.title("🧬 玉佳生物系统")
    st.sidebar.info(f"当前用户: {st.session_state.username} | 权限: {st.session_state.role}")
    
    # 权限菜单逻辑
    menu_options = ["样品业务管理"]
    if st.session_state.role == "finance":
        menu_options.append("财务流水看板")
    menu_options.append("退出登录")
    
    choice = st.sidebar.radio("功能导航", menu_options)

    # --- 逻辑分流 ---
    if choice == "样品业务管理":
        st.title("📦 样品业务实时管理")
        df = load_data()
        
        # 使用 data_editor 实现行内编辑
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="sample_editor")
        
        if st.button("保存样品表修改"):
            # 这里调用你的 save_data(edited_df)
            try:
                records = edited_df.to_dict("records")
                supabase.table("samples").upsert(records).execute()
                st.success("数据已成功同步至 Supabase！")
            except Exception as e:
                st.error(f"保存失败: {e}")

    elif choice == "财务流水看板":
        st.title("💰 财务收支流水")
        df_trans = load_transactions()
        st.dataframe(df_trans, use_container_width=True)
        
        with st.expander("新增流水记录"):
            with st.form("add_trans"):
                # 这里可以添加简单的财务录入表单
                st.write("财务录入表单逻辑...")
                st.form_submit_button("提交")

    elif choice == "退出登录":
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# --- 5. 启动入口 ---
# ==========================================
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()
