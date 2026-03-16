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
        "wangxiaoliang": {"password": "Yujia@003", "role": "scientific"},
        "pengyutao": {"password": "Yujia@002", "role": "scientific"},
        "zhoucuiying": {"password": "Yujia@001", "role": "finance"}
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

# --- 财务流水数据处理 ---
def load_transactions():
    """从 Supabase 加载财务流水数据"""
    try:
        response = supabase.table("transactions").select("*").execute()
        data = response.data
        if data:
            df = pd.DataFrame(data)
            df = df.fillna("")
            return df.sort_values("id", ascending=False).reset_index(drop=True)
        else:
            return pd.DataFrame(columns=["id", "type", "date", "project", "amount", "source", "operator", "remarks"])
    except Exception as e:
        st.error(f"读取流水数据失败: {e}")
        return pd.DataFrame(columns=["id", "type", "date", "project", "amount", "source", "operator", "remarks"])

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
    tab1, tab2, tab3 = st.tabs(["🆕 样品录入", "📋 样品概览", "📁 查看上传文件"])

    with tab1:
        st.subheader("录入新样品接收情况")
        with st.form("new_sample_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                # 优化1：时间可直接手动修改和输入
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                reception_time = st.text_input("接收时间 (可直接修改)", value=current_time_str)
                
                # 优化2：寄样人姓名记忆库
                existing_senders = [s for s in df["sender"].unique() if str(s).strip() != ""] if not df.empty else []
                sender_options = existing_senders + ["➕ 新增寄样人 (手动输入)"]
                selected_sender = st.selectbox("选择寄样人", sender_options)
                
                if selected_sender == "➕ 新增寄样人 (手动输入)":
                    sender = st.text_input("请输入新寄样人姓名")
                else:
                    sender = selected_sender

                sample_type = st.text_input("样品类型")
                quantity = st.number_input("样品数量", min_value=1, step=1)
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                requirements = st.text_area("样品处理要求/注意事项")
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
                        "reception_date": reception_time,  # 直接存入手动修改的时间字符串
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
    """财务页面 - 业务流水与报表功能"""
    st.title(f"财务管理 - 欢迎，{st.session_state.username}")
    tab1, tab2, tab3 = st.tabs(["📝 样品账单待办", "💰 收支流水登记", "📊 总财务报表"])

    with tab1:
        df = load_data()
        st.subheader("📝 财务待办清单 (针对科研样品)")
        pending_df = df[(df["invoice_status"] == "未开具") | (df["list_status"] == "未开具") | (df["payment_status"] == "否")]
        edited_finance_df = st.data_editor(pending_df, key="fin_editor")
        if st.button("保存样品财务状态更新"):
            df.update(edited_finance_df)
            save_data(df)
            st.success("样品财务状态已成功更新！")
            st.rerun()

    with tab2:
        st.subheader("💰 登记最新业务收支流水")
        t_df = load_transactions()
        trans_type = st.radio("选择需要登记的类型", ["收入", "支出"], horizontal=True)
        
        with st.form("transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_date = st.date_input("发生日期", value=date.today())
                t_project = st.text_input("所属项目 / 事项")
                t_amount = st.number_input("金额 (元)", min_value=0.0, step=100.0)
            
            with col2:
                if trans_type == "支出":
                    t_source = st.text_input("资金来源/支付账户 (如: 某对公账户/支付宝)")
                    t_operator = st.text_input("登记人", value=st.session_state.username)
                    t_remarks = st.text_area("备注信息")
                else:
                    t_source = st.text_input("收入来源/打款方 (如: 某客户公司)")
                    t_operator = st.session_state.username
                    t_remarks = st.text_area("回款备注")
                    
            submitted = st.form_submit_button(f"提交【{trans_type}】记录")
            
            if submitted:
                new_id = int(t_df["id"].max() + 1) if not t_df.empty and "id" in t_df.columns else 1
                new_record = {
                    "id": new_id,
                    "type": trans_type,
                    "date": t_date.strftime(DATE_FORMAT),
                    "project": t_project,
                    "amount": float(t_amount),
                    "source": t_source,
                    "operator": t_operator,
                    "remarks": t_remarks
                }
                t_df = pd.concat([t_df, pd.DataFrame([new_record])], ignore_index=True)
                save_transactions(t_df)
                st.success(f"成功登记一笔 {t_amount} 元的【{trans_type}】流水！")
                st.rerun()

    with tab3:
        st.subheader("📊 业务总收支报表")
        t_df = load_transactions()
        
        if not t_df.empty:
            total_income = t_df[t_df["type"] == "收入"]["amount"].sum()
            total_expense = t_df[t_df["type"] == "支出"]["amount"].sum()
            balance = total_income - total_expense
            
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("💰 总收入 (元)", f"¥ {total_income:,.2f}")
            col_b.metric("💸 总支出 (元)", f"¥ {total_expense:,.2f}")
            col_c.metric("🏦 当前结余 (元)", f"¥ {balance:,.2f}", delta=float(balance))
            
            st.divider()
            st.markdown("##### 🧾 收支明细账单 (支持表格内直接修改)")
            edited_t_df = st.data_editor(t_df, num_rows="dynamic", key="trans_table_editor", use_container_width=True)
            
            if st.button("保存明细账单更改"):
                save_transactions(edited_t_df)
                st.success("收支明细数据已更新！")
                st.rerun()
        else:
            st.info("当前暂无流水记录，请在【收支流水登记】模块录入数据。")

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
