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
            <h1 style='color: #1976D2; font-family: "楷体", "KaiTi", serif; font-size: 48px; white-space: nowrap; margin: 0;'>
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
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                requirements = st.text_area("样品处理要求/注意事项")
            uploaded_files = st.file_uploader("上传相关文件", accept_multiple_files=True)
            submit_sample = st.form_submit_button("保存新样品记录")
            
            if submit_sample:
                new_files_list = []
                for file in uploaded_files:
                    unique_filename = f"{st.session_state.username}_{file.size}_{file.name}"
                    supabase.storage.from_("uploads").upload(path=unique_filename, file=file.getvalue(), file_options={"content-type": file.type})
                    new_files_list.append({"original_name": file.name, "filename": unique_filename})
                
                new_data = {
                    "id": int(df["id"].max() + 1) if not df.empty else 1,
                    "reception_date": reception_date.strftime(DATE_FORMAT),
                    "sender": sender, "sample_type": sample_type, "quantity": quantity,
                    "progress": progress, "requirements": requirements, "completion_date": "", 
                    "invoice_status": "未开具", "payment_status": "否", "list_status": "未开具",
                    "uploaded_files": json.dumps(new_files_list)
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("记录已保存！")
                st.rerun()

    with tab2:
        st.subheader("所有样品状态概览与编辑")
        edited_df = st.data_editor(df, num_rows="dynamic", key="sci_editor")
        if st.button("保存更改"):
            save_data(edited_df)
            st.success("更改已保存。")
            st.rerun()

    with tab3:
        st.subheader("查看特定样品的上传文件")
        sample_id = st.selectbox("选择样品 ID", df["id"].unique() if not df.empty else [], index=None)
        if sample_id:
            row = df[df["id"] == sample_id].iloc[0]
            display_uploaded_files(row["uploaded_files"])

def finance_page():
    """财务页面"""
    st.title(f"财务管理 - 欢迎，{st.session_state.username}")
    df = load_data()
    st.subheader("📝 财务待办清单")
    pending_df = df[(df["invoice_status"] == "未开具") | (df["list_status"] == "未开具") | (df["payment_status"] == "否")]
    edited_finance_df = st.data_editor(pending_df, key="fin_editor")
    
    if st.button("保存财务状态更新"):
        df.update(edited_finance_df)
        save_data(df)
        st.success("财务状态已成功更新！")
        st.rerun()

# ==========================================
# --- 4. 应用程序主入口 ---
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
        st.sidebar.title("玉佳生物业务管理系统")
        st.sidebar.markdown(f"**用户:** {st.session_state.username}")
        role_display = "科研" if st.session_state.role == "scientific" else "财务"
        st.sidebar.markdown(f"**角色:** {role_display}")
        
        if st.sidebar.button("注销"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

        if st.session_state.role == "scientific":
            scientific_staff_page()
        elif st.session_state.role == "finance":
            finance_page()
