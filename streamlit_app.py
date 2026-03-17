import streamlit as st
import pandas as pd
from datetime import date, datetime
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
        "wxl": {"password": "123", "role": "scientific"},
        "pyt": {"password": "123", "role": "scientific"},
        "zcy": {"password": "123", "role": "finance"}
    }
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def load_data():
    """从 Supabase 加载样品数据"""
    try:
        response = supabase.table("samples").select("*").execute()
        data = response.data
        if data: 
            df = pd.DataFrame(data)
            df = df.fillna("") 
            cols_to_str = ["requirements", "completion_date", "sender", "sender_company", "sample_type", "progress", "invoice_status", "invoice_amount", "payment_status", "list_status", "uploaded_files"]
            for col in cols_to_str:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            return df.sort_values("id").reset_index(drop=True)
        else: 
            return pd.DataFrame(columns=[
                "id", "reception_date", "sender", "sender_company", "sample_type", "quantity",
                "progress", "requirements", "completion_date", "invoice_status", "invoice_amount", "payment_status", "list_status", "uploaded_files"
            ])
    except Exception as e:
        st.error(f"读取样品数据失败: {e}")
        return pd.DataFrame()

def save_data(df):
    """保存样品数据"""
    try:
        records = df.to_dict("records")
        if records:
            supabase.table("samples").upsert(records).execute()
    except Exception as e:
        st.error(f"保存样品数据失败: {e}")

def load_transactions():
    """从 Supabase 加载财务流水数据"""
    try:
        response = supabase.table("transactions").select("*").execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            df = df.fillna("")
            if "invoice_files" not in df.columns:
                df["invoice_files"] = ""
            return df.sort_values("id", ascending=False).reset_index(drop=True)
        else:
            return pd.DataFrame(columns=["id", "type", "date", "project", "amount", "source", "operator", "remarks", "invoice_files"])
    except Exception as e:
        st.error(f"读取流水数据失败: {e}")
        return pd.DataFrame(columns=["id", "type", "date", "project", "amount", "source", "operator", "remarks", "invoice_files"])

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
    """登录界面"""
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #e8f5e9 !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .block-container { padding-top: 12vh !important; max-width: 600px !important; }
    [data-testid="stForm"] {
        background-color: #ffffff !important; padding: 40px !important;
        border-radius: 15px !important; box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        border: none !important;
    }
    div[data-testid="stFormSubmitButton"] {
        display: flex !important; justify-content: flex-end !important; margin-top: 30px !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        width: 100px !important; background-color: #1976D2 !important;
        color: white !important; border-radius: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
    tab1, tab2, tab3, tab4 = st.tabs(["🆕 样品录入", "📋 样品概览", "📁 查看上传文件", "💸 支出流水登记"])

    with tab1:
        st.subheader("录入新样品接收情况")
        with st.form("new_sample_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                reception_time = st.text_input("接收时间 (可直接修改)", value=current_time_str)
                
                existing_senders = [s for s in df["sender"].unique() if str(s).strip() != ""] if not df.empty else []
                sender_options = existing_senders + ["➕ 新增寄样人 (手动输入)"]
                selected_sender = st.selectbox("选择寄样人", sender_options)
                if selected_sender == "➕ 新增寄样人 (手动输入)":
                    sender = st.text_input("请输入新寄样人姓名")
                else:
                    sender = selected_sender

                existing_companies = [s for s in df["sender_company"].unique() if str(s).strip() != ""] if (not df.empty and "sender_company" in df.columns) else []
                company_options = existing_companies + ["➕ 新增寄样单位 (手动输入)"]
                selected_company = st.selectbox("选择寄样单位 (选填)", company_options)
                if selected_company == "➕ 新增寄样单位 (手动输入)":
                    sender_company = st.text_input("请输入新寄样单位", placeholder="例如：某某大学、某某医院...")
                else:
                    sender_company = selected_company

                existing_types = [s for s in df["sample_type"].unique() if str(s).strip() != ""] if not df.empty else []
                type_options = existing_types + ["➕ 新增样品类型 (手动输入)"]
                selected_type = st.selectbox("选择样品类型", type_options)
                if selected_type == "➕ 新增样品类型 (手动输入)":
                    sample_type = st.text_input("请输入新样品类型")
                else:
                    sample_type = selected_type

                quantity = st.number_input("样品数量", min_value=1, step=1)
                
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                
                existing_reqs = [s for s in df["requirements"].unique() if str(s).strip() != ""] if not df.empty else []
                req_options = existing_reqs + ["➕ 新增处理要求/注意事项 (手动输入)"]
                selected_req = st.selectbox("选择处理要求/注意事项", req_options)
                if selected_req == "➕ 新增处理要求/注意事项 (手动输入)":
                    requirements = st.text_area("请输入新处理要求/注意事项")
                else:
                    requirements = selected_req

            uploaded_files = st.file_uploader("上传相关文件", accept_multiple_files=True)
            submit_sample = st.form_submit_button("保存新样品记录")
            
            if submit_sample:
                if not sender:
                    st.warning("请填写或选择寄样人！")
                else:
                    new_files_list = []
                    for file in uploaded_files:
                        unique_filename = f"{st.session_state.username}_{file.size}_{file.name}"
                        supabase.storage.from_("uploads").upload(path=unique_filename, file=file.getvalue(), file_options={"content-type": file.type})
                        new_files_list.append({"original_name": file.name, "filename": unique_filename})
                    
                    new_data = {
                        "id": int(df["id"].max() + 1) if not df.empty else 1,
                        "reception_date": reception_time,
                        "sender": sender,
                        "sender_company": sender_company,
                        "sample_type": sample_type, "quantity": quantity,
                        "progress": progress, "requirements": requirements, "completion_date": "", 
                        "invoice_status": "未开具", "invoice_amount": "", "payment_status": "否", "list_status": "未开具", 
                        "uploaded_files": json.dumps(new_files_list)
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    save
