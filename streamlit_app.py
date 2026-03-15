import streamlit as st
import pandas as pd
import os
from datetime import date
import json
from supabase import create_client, Client

# 初始化 Supabase 客户端
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()
# --- 配置和常数 ---
DATA_FILE = "sample_management_data.csv"
UPLOADS_DIR = "uploads"
USER_CREDENTIALS_FILE = "users.json" # 用于存储简单加密的密码
DATE_FORMAT = "%Y-%m-%d"

# 初始化数据和文件夹
if not os.path.exists(DATA_FILE):
    # 创建具有所有必需字段的初始数据
    df = pd.DataFrame(columns=[
        "id", "reception_date", "sender", "sample_type", "quantity",
        "progress", "requirements", "invoice_status", "list_status", "uploaded_files"
    ])
    df.to_csv(DATA_FILE, index=False)

if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# --- 数据操作函数 ---
def load_data():
    """从 CSV 文件加载数据。"""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # 修复数据类型冲突：将缺失值替换为空白
        df = df.fillna("") 
        
        # 强制将这些可能被误判为数字的列转换为字符串类型 (str)
        cols_to_str = ["requirements", "sender", "sample_type", "progress", "invoice_status", "list_status", "uploaded_files"]
        for col in cols_to_str:
            if col in df.columns:
                df[col] = df[col].astype(str)
                
        return df
    return pd.DataFrame()
def save_data(df):
    """将数据帧保存到 CSV 文件。"""
    df.to_csv(DATA_FILE, index=False)

# --- 身份验证（简单原型） ---
# 注意：在生产环境中，必须使用安全的、哈希化的密码存储和专业的认证方案。
def init_users():
    """初始化预定义的用户凭据。"""
    users = {
        "wang_xiaoliang": {"password": "password_wx", "role": "scientific"},
        "peng_yutao": {"password": "password_py", "role": "scientific"},
        "zhou_cuiying": {"password": "password_zc", "role": "finance"}
    }
    with open(USER_CREDENTIALS_FILE, 'w') as f:
        json.dump(users, f)

if not os.path.exists(USER_CREDENTIALS_FILE):
    init_users()

def check_login(username, password):
    """简单的登录检查。"""
    with open(USER_CREDENTIALS_FILE, 'r') as f:
        users = json.load(f)
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

# --- UI 辅助函数 ---
def display_uploaded_files(files_json):
    """解析并显示 Supabase 云端文件的下载链接。"""
    if pd.isna(files_json) or files_json == "[]" or not files_json:
        st.write("暂无上传文件。")
    else:
        files = json.loads(files_json)
        for file_info in files:
            # 直接从 Supabase 获取公开下载链接
            public_url = supabase.storage.from_('uploads').get_public_url(file_info["filename"])
            st.markdown(f"[⬇️ 点击下载：{file_info['original_name']}]({public_url})")

# ==========================================
# --- 登录界面 ---
# ==========================================
def login_page():
    st.title("玉佳生物对外科研业务管理系统 - 登录")
    
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
                st.success(f"登录成功！欢迎，{username}")
                # 重新加载应用程序以应用状态更改
                st.rerun()
            else:
                st.error("用户名或密码错误。")

# ==========================================
# --- 科研人员页面 (Scientific Staff) ---
# ==========================================
def scientific_staff_page():
    st.title(f"科研业务管理 - 欢迎，{st.session_state.username}")
    df = load_data()

    # --- 部分 1：录入新样品 ---
    with st.expander("🆕 录入新样品接收情况", expanded=True):
        with st.form("new_sample_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                reception_date = st.date_input("接收时间", value=date.today())
                sender = st.text_input("寄样人")
                sample_type = st.selectbox("样品类型", ["血清", "血浆", "细胞", "组织", "DNA/RNA", "其他"])
                quantity = st.number_input("样品数量", min_value=1, step=1)
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                requirements = st.text_area("样品处理要求/注意事项")
                
            uploaded_files = st.file_uploader("上传相关文件 (如寄样清单、协议、实验结果)", accept_multiple_files=True)
            
            submit_sample = st.form_submit_button("保存新样品记录")
            
            if submit_sample:
                # 处理文件上传
                new_files_list = []
                for file in uploaded_files:
                    # 修改了这里，且保证了对齐
                    unique_filename = f"{st.session_state.username}_{file.size}_{file.name}"
                    
                    # 将上传的文件转换为字节流并推送到 Supabase 的 'uploads' 存储桶
                    file_bytes = file.getvalue()
                    supabase.storage.from_('uploads').upload(
                        path=unique_filename,
                        file=file_bytes,
                        file_options={"content-type": file.type}
                    )
                    
                    new_files_list.append({"original_name": file.name, "filename": unique_filename})
                
                # 创建新记录
                new_data = {
                    "id": len(df) + 1,
                    "reception_date": reception_date.strftime(DATE_FORMAT),
                    "sender": sender,
                    "sample_type": sample_type,
                    "quantity": quantity,
                    "progress": progress,
                    "requirements": requirements,
                    "invoice_status": "未开具", # 默认状态
                    "list_status": "未开具",   # 默认状态
                    "uploaded_files": json.dumps(new_files_list) # 以 JSON 字符串存储文件列表
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("新样品记录已保存并上传相关文件！")
                st.rerun() # 刷新以显示新数据

    # --- 部分 2：查看和更新所有样品 ---
    st.divider()
    st.subheader("📋 所有样品概览")
    
    # 允许在数据帧中直接编辑“进度”和“要求”
    edited_df = st.data_editor(
        df,
        column_config={
            "id": "ID",
            "reception_date": st.column_config.DateColumn("接收时间", format="YYYY-MM-DD", disabled=True),
            "sender": st.column_config.TextColumn("寄样人", disabled=True),
            "sample_type": st.column_config.TextColumn("样品类型", disabled=True),
            "quantity": st.column_config.NumberColumn("样品数量", disabled=True),
            "progress": st.column_config.SelectboxColumn("当前进度", options=["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"]),
            "requirements": st.column_config.TextColumn("样品处理要求"),
            "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
            "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
            "uploaded_files": st.column_config.TextColumn("已上传文件 (代码)", disabled=True)
        },
        num_rows="dynamic",
        key="scientific_editor"
    )

    if st.button("保存对样品状态的更改"):
        save_data(edited_df)
        st.success("更改已保存。")
        st.rerun()

    # --- 部分 3：查看单个样品的具体文件 ---
    st.divider()
    st.subheader("📁 查看特定样品的上传文件")
    sample_to_view_files = st.selectbox("选择要查看文件的样品 ID", edited_df['id'].unique(), index=None, placeholder="选择一个 ID...")
    
    if sample_to_view_files is not None:
        sample_row = edited_df[edited_df['id'] == sample_to_view_files].iloc[0]
        st.write(f"**寄样人:** {sample_row['sender']}, **类型:** {sample_row['sample_type']}")
        st.write("**已上传文件列表：**")
        display_uploaded_files(sample_row['uploaded_files'])

# ==========================================
# --- 财务人员页面 (Finance Staff) ---
# ==========================================
def finance_page():
    st.title(f"财务管理 - 欢迎，{st.session_state.username}")
    df = load_data()
    
    st.subheader("📝 财务待办清单")
    st.write("以下是未完全开具发票或清单的样品批次：")

    # 过滤出需要注意的样品（即，未完成财务流程的样品）
    pending_finance_df = df[
        (df['invoice_status'] == '未开具') | (df['list_status'] == '未开具')
    ]

    # 允许直接编辑“发票状态”和“清单状态”
    edited_finance_df = st.data_editor(
        pending_finance_df,
        column_config={
            "id": "ID",
            "reception_date": st.column_config.DateColumn("接收时间", format="YYYY-MM-DD", disabled=True),
            "sender": st.column_config.TextColumn("寄样人", disabled=True),
            "sample_type": st.column_config.TextColumn("样品类型", disabled=True),
            "quantity": st.column_config.NumberColumn("样品数量", disabled=True),
            "progress": st.column_config.TextColumn("当前进度", disabled=True),
            "requirements": st.column_config.TextColumn("样品处理要求", disabled=True),
            "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
            "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
            "uploaded_files": st.column_config.TextColumn("已上传文件 (代码)", disabled=True)
        },
        key="finance_editor"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("保存财务状态更新"):
            # 将编辑后的数据合并回主数据帧
            df.update(edited_finance_df)
            save_data(df)
            st.success("财务状态已成功更新！")
            st.rerun()

    # --- 部分 2：查看所有财务记录 ---
    st.divider()
    with st.expander("📊 查看所有财务记录汇总"):
        # 显示完整的、未经过滤的数据帧，只允许对“发票状态”和“清单状态”进行编辑
        edited_all_finance_df = st.data_editor(
            df,
            column_config={
                "id": "ID",
                "reception_date": st.column_config.DateColumn("接收时间", format="YYYY-MM-DD", disabled=True),
                "sender": st.column_config.TextColumn("寄样人", disabled=True),
                "sample_type": st.column_config.TextColumn("样品类型", disabled=True),
                "progress": st.column_config.TextColumn("当前进度", disabled=True),
                "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
                "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
                "uploaded_files": st.column_config.TextColumn("已上传文件 (代码)", disabled=True)
            },
            disabled=["id", "reception_date", "sender", "sample_type", "quantity", "progress", "requirements", "uploaded_files"],
            key="all_finance_editor"
        )
        
        if st.button("保存所有状态更改"):
             save_data(edited_all_finance_df)
             st.success("所有更改已保存。")
             st.rerun()

# ==========================================
# --- 应用程序主入口 ---
# ==========================================
if __name__ == '__main__':
    # 初始化 session 状态
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None

    # 根据登录状态显示页面
    if not st.session_state.logged_in:
        login_page()
    else:
        # 添加侧边栏导航和注销
        st.sidebar.title("玉佳生物管理")
        st.sidebar.markdown(f"**用户:** {st.session_state.username}")
        st.sidebar.markdown(f"**角色:** {'科研' if st.session_state.role == 'scientific' else '财务'}")
        
        if st.sidebar.button("注销"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

        # 根据角色重定向到特定页面
        if st.session_state.role == "scientific":
            scientific_staff_page()
        elif st.session_state.role == "finance":
            finance_page()
        else:
            st.error("未知用户角色。")
