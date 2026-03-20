import streamlit as st
import pandas as pd
from datetime import date, datetime
import json
from supabase import create_client, Client

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
            
        for col in std_cols:
            if col not in df.columns:
                df[col] = ""
                
        df = df.fillna("") 
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
    """登录界面 (已应用高级美化)"""
    st.markdown("""
        <style>
        /* 1. 全屏背景图与自愈设置 */
        .stApp {
            background-image: url("https://hporhdgbqajajdbefynt.supabase.co/storage/v1/object/public/Zhongjia/56211398.png");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }
        
        /* 2. 透明页眉 */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* 3. 巨型标题美化 - 72px */
        .login-title {
            color: #1976D2 !important; 
            text-align: center;
            font-size: 72px; 
            font-family: "楷体", "KaiTi", serif;
            font-weight: bold;
            margin-top: 48px; 
            white-space: nowrap; 
            text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.8); 
        }
        
        /* 4. 输入框标签左对齐 */
        .stTextInput label {
            display: flex;
            justify-content: flex-start; 
            font-size: 1.1rem;
            color: #333; 
            font-weight: bold;
        }
        
        /* 5. 登录框美化：600px 限制、居中、毛玻璃效果 */
        [data-testid="stForm"] {
            background-color: rgba(255, 255, 255, 0.5) !important; 
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.4);
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* 6. 登录按钮立体效果 */
        div[data-testid="stFormSubmitButton"] > button {
            background-image: linear-gradient(180deg, #1E88E5 0%, #1565C0 100%) !important;
            color: white !important;
            border: 1px solid #0D47A1 !important;
            border-top: 1px solid #64B5F6 !important;
            border-radius: 12px !important;
            font-weight: bold !important;
            font-size: 1.1rem !important;
            padding: 10px 24px !important;
            box-shadow: 0 5px 0 #0D47A1, 0 8px 15px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.1s ease !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:active {
            box-shadow: 0 2px 0 #0D47A1, 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            transform: translateY(3px) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # === Logo与标题部分 ===
    logo_url = "https://hporhdgbqajajdbefynt.supabase.co/storage/v1/object/public/Yujia/unnamed.jpg"
    st.markdown(f"""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 48px;">
            <img src="{logo_url}" width="320" style="border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2);" />
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

def scientific_staff_page():
    """科研页面内容 (保持原逻辑)"""
    st.title(f"科研业务管理 - 欢迎，{st.session_state.username}")
    df = load_data()
    tab1, tab2, tab3, tab4 = st.tabs(["🆕 样品录入", "📋 样品概览", "📁 查看上传文件", "💸 支出流水登记"])
    # ... (后续内容保持不变)
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
                sender = st.text_input("请输入新寄样人姓名") if selected_sender == "➕ 新增寄样人 (手动输入)" else selected_sender
                existing_companies = [s for s in df["sender_company"].unique() if str(s).strip() != ""] if not df.empty else []
                company_options = existing_companies + ["➕ 新增寄样单位 (手动输入)"]
                selected_company = st.selectbox("选择寄样单位 (选填)", company_options)
                sender_company = st.text_input("请输入新寄样单位") if selected_company == "➕ 新增寄样单位 (手动输入)" else selected_company
                existing_types = [s for s in df["sample_type"].unique() if str(s).strip() != ""] if not df.empty else []
                type_options = existing_types + ["➕ 新增样品类型 (手动输入)"]
                selected_type = st.selectbox("选择样品类型", type_options)
                sample_type = st.text_input("请输入新样品类型") if selected_type == "➕ 新增样品类型 (手动输入)" else selected_type
                quantity = st.number_input("样品数量", min_value=1, step=1)
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                existing_reqs = [s for s in df["requirements"].unique() if str(s).strip() != ""] if not df.empty else []
                req_options = existing_reqs + ["➕ 新增处理要求 (手动输入)"]
                selected_req = st.selectbox("选择处理要求", req_options)
                requirements = st.text_area("请输入新要求") if selected_req == "➕ 新增处理要求 (手动输入)" else selected_req
            uploaded_files = st.file_uploader("上传相关文件", accept_multiple_files=True)
            submit_sample = st.form_submit_button("保存新样品记录")
            if submit_sample:
                # 样品保存逻辑
                new_files_list = []
                for file in uploaded_files:
                    unique_filename = f"{st.session_state.username}_{file.size}_{file.name}"
                    supabase.storage.from_("uploads").upload(path=unique_filename, file=file.getvalue(), file_options={"content-type": file.type})
                    new_files_list.append({"original_name": file.name, "filename": unique_filename})
                new_data = {
                    "id": int(df["id"].max() + 1) if not df.empty else 1,
                    "reception_date": reception_time, "sender": sender, "sender_company": sender_company,
                    "sample_type": sample_type, "quantity": quantity, "progress": progress, "requirements": requirements,
                    "completion_date": "", "invoice_status": "未开具", "invoice_amount": "", "payment_status": "否", 
                    "list_status": "未开具", "uploaded_files": json.dumps(new_files_list)
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("样品记录已保存！")
                st.rerun()

    with tab2:
        st.subheader("所有样品状态概览与编辑")
        edited_df = st.data_editor(df, num_rows="dynamic", key="sci_editor", use_container_width=True)
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

    with tab4:
        st.subheader("💸 登记业务支出流水")
        t_df = load_transactions()
        with st.form("sci_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date = st.date_input("支出日期", value=date.today())
                t_project = st.text_input("支出项目 / 事项")
                t_amount = st.number_input("金额 (元)", min_value=0.0)
            with col2:
                t_source = st.text_input("支付账户")
                t_operator = st.text_input("登记人", value=st.session_state.username)
                t_remarks = st.text_area("备注")
            uploaded_invoices = st.file_uploader("上传支出凭证", accept_multiple_files=True, key="sci_inv")
            if st.form_submit_button("提交支出记录"):
                inv_files_list = [{"original_name": f.name, "filename": f"trans_{f.name}"} for f in uploaded_invoices]
                new_record = {
                    "id": int(t_df["id"].max() + 1) if not t_df.empty else 1, "type": "支出", "date": t_date.strftime(DATE_FORMAT),
                    "project": t_project, "amount": float(t_amount), "source": t_source, "operator": t_operator,
                    "remarks": t_remarks, "invoice_files": json.dumps(inv_files_list)
                }
                save_transactions(pd.concat([t_df, pd.DataFrame([new_record])], ignore_index=True))
                st.success("登记成功！")
                st.rerun()

def finance_page():
    """财务页面内容 (保持原逻辑)"""
    st.title(f"财务管理 - 欢迎，{st.session_state.username}")
    tab1, tab2, tab3 = st.tabs(["📝 样品账单待办", "💰 收支流水登记", "📊 总财务报表"])
    
    with tab1:
        df = load_data()
        pending_df = df[(df["invoice_status"] == "未开具") | (df["payment_status"] == "否")]
        edited_finance_df = st.data_editor(pending_df, key="fin_editor", use_container_width=True)
        if st.button("保存账单状态"):
            df.update(edited_finance_df)
            save_data(df)
            st.success("已更新！")
            st.rerun()
    
    with tab2:
        st.subheader("收支流水登记")
        # 此处省略具体重复表单逻辑，保持你原有的即可
        pass

    with tab3:
        st.subheader("财务报表")
        t_df = load_transactions()
        if not t_df.empty:
            st.metric("累计结余", f"¥ {t_df[t_df['type']=='收入']['amount'].sum() - t_df[t_df['type']=='支出']['amount'].sum():,.2f}")
            st.dataframe(t_df)

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
            st.rerun()

        if st.session_state.role == "scientific":
            scientific_staff_page()
        elif st.session_state.role == "finance":
            finance_page()
