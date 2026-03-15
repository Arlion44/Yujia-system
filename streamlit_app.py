import streamlit as st
import pandas as pd
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
DATE_FORMAT = "%Y-%m-%d"

# --- 数据操作函数 ---
def load_data():
    """从 Supabase 云端数据库加载数据。"""
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
            df = df.sort_values("id").reset_index(drop=True)
            return df
        else: 
            return pd.DataFrame(columns=[
                "id", "reception_date", "sender", "sample_type", "quantity",
                "progress", "requirements", "completion_date", "invoice_status", "payment_status", "list_status", "uploaded_files"
            ])
    except Exception as e:
        st.error(f"读取云端数据失败: {e}")
        return pd.DataFrame()

def save_data(df):
    """将数据保存到 Supabase 云端数据库。"""
    try:
        records = df.to_dict("records")
        if records:
            supabase.table("samples").upsert(records).execute()
    except Exception as e:
        st.error(f"保存云端数据失败: {e}")

# --- 身份验证 ---
def check_login(username, password):
    """简单的登录检查。"""
    
    users = {
        "wangxiaoliang": {"password": "Yujia@003", "role": "scientific"},
        "pengyutao": {"password": "Yujia@002", "role": "scientific"},
        "zhoucuiying": {"password": "Yujia@001", "role": "finance"}
    }
    
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
            public_url = supabase.storage.from_("uploads").get_public_url(file_info["filename"])
            st.markdown(f"[⬇️ 点击下载：{file_info['original_name']}]({public_url})")

# ==========================================
# --- 登录界面 ---
# ==========================================
def login_page():
    # 注入自定义 CSS 来修改登录界面的样式
    custom_css = """
    <style>
        /* 1. 整个页面背景设置为嫩绿色 */
        [data-testid="stAppViewContainer"] {
            background-color: #e8f5e9;
        }
        
        /* 隐藏顶部的 Streamlit 默认装饰条，避免影响居中视觉 */
        [data-testid="stHeader"] {
            display: none;
        }

        /* 2. 让登录框在网页中居中，并限制最大宽度 */
        .block-container {
            padding-top: 15vh !important;
            max-width: 600px !important;
        }

        /* 3. 设置表单为白色背景，加上圆角和阴影 */
        [data-testid="stForm"] {
            background-color: #ffffff;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: none;
        }

        /* 4. 登录按钮靠右对齐 */
        [data-testid="stFormSubmitButton"] {
            text-align: right; /* 让容器内的按钮右对齐 */
            display: block;
            margin-top: 20px;
        }
        
        /* 按钮本身的微调 */
        div[data-testid="stFormSubmitButton"] button {
            margin-left: auto; /* 确保在 flex 布局下也能靠右 */
        }
    </style>
     """, unsafe_allow_html=True)
    
    # 标题：正楷、蓝色、居中，底部外边距 40px (约等于两行间隔)
    st.markdown("""
        <h2 style='text-align: center; color: #1976D2; font-family: "楷体", "KaiTi", "STKaiti", serif; font-size: 48px; margin-top: 0; margin-bottom: 40px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
            玉佳生物科研业务管理系统
        </h2>
    """, unsafe_allow_html=True)
    
    # Streamlit 的 st.form 自带 Enter 键提交功能
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
                st.rerun()
            else:
                st.error("用户名或密码错误。")

# ==========================================
# --- 科研人员页面 (Scientific Staff) ---
# ==========================================
def scientific_staff_page():
    st.title(f"科研业务管理 - 欢迎，{st.session_state.username}")
    df = load_data()

    # 创建三个独立的标签页
    tab1, tab2, tab3 = st.tabs(["🆕 样品录入", "📋 样品概览", "📁 查看上传文件"])

    # -----------------------------------
    # 标签页 1：样品录入界面
    # -----------------------------------
    with tab1:
        st.subheader("录入新样品接收情况")
        with st.form("new_sample_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                reception_date = st.date_input("接收时间", value=date.today())
                sender = st.text_input("寄样人")
                sample_type = st.text_input("样品类型", placeholder="请输入（例如：土壤、植物组织...）")
                quantity = st.number_input("样品数量", min_value=1, step=1)
            with col2:
                progress = st.selectbox("当前进度", ["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"])
                requirements = st.text_area("样品处理要求/注意事项")
                
            uploaded_files = st.file_uploader("上传相关文件 (如寄样清单、协议、实验结果)", accept_multiple_files=True)
            submit_sample = st.form_submit_button("保存新样品记录")
            
            if submit_sample:
                new_files_list = []
                for file in uploaded_files:
                    unique_filename = f"{st.session_state.username}_{file.size}_{file.name}"
                    
                    file_bytes = file.getvalue()
                    supabase.storage.from_("uploads").upload(
                        path=unique_filename,
                        file=file_bytes,
                        file_options={"content-type": file.type}
                    )
                    
                    new_files_list.append({"original_name": file.name, "filename": unique_filename})
                
                new_data = {
                    "id": len(df) + 1 if len(df) > 0 else 1,
                    "reception_date": reception_date.strftime(DATE_FORMAT),
                    "sender": sender,
                    "sample_type": sample_type,
                    "quantity": quantity,
                    "progress": progress,
                    "requirements": requirements,
                    "completion_date": "", 
                    "invoice_status": "未开具",
                    "payment_status": "否", 
                    "list_status": "未开具",
                    "uploaded_files": json.dumps(new_files_list)
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("新样品记录已保存并上传相关文件！")
                st.rerun()

    # -----------------------------------
    # 标签页 2：样品概览界面
    # -----------------------------------
    with tab2:
        st.subheader("所有样品状态概览与编辑")
        edited_df = st.data_editor(
            df,
            column_config={
                "id": "ID",
                "reception_date": st.column_config.DateColumn("接收时间", format="YYYY-MM-DD", disabled=True),
                "sender": st.column_config.TextColumn("寄样人", disabled=True),
                "sample_type": st.column_config.TextColumn("样品类型"),
                "quantity": st.column_config.NumberColumn("样品数量", disabled=True),
                "progress": st.column_config.SelectboxColumn("当前进度", options=["已接收", "预处理中", "检测中", "数据分析中", "已完成", "出现问题"]),
                "requirements": st.column_config.TextColumn("样品处理要求"),
                "completion_date": st.column_config.TextColumn("完成时间"), 
                "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
                "payment_status": st.column_config.SelectboxColumn("是否收款", options=["否", "是"]), 
                "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
                "uploaded_files": st.column_config.TextColumn("已上传文件", disabled=True)
            },
            num_rows="dynamic",
            key="scientific_editor"
        )

        if st.button("保存对样品状态的更改"):
            save_data(edited_df)
            st.success("更改已保存。")
            st.rerun()

    # -----------------------------------
    # 标签页 3：查看上传文件界面
    # -----------------------------------
    with tab3:
        st.subheader("查看特定样品的上传文件")
        sample_to_view_files = st.selectbox("选择要查看文件的样品 ID", df["id"].unique(), index=None, placeholder="选择一个 ID...")
        
        if sample_to_view_files is not None:
            sample_row = df[df["id"] == sample_to_view_files].iloc[0]
            st.write(f"**寄样人:** {sample_row['sender']}, **类型:** {sample_row['sample_type']}")
            st.write("**已上传文件列表：**")
            display_uploaded_files(sample_row["uploaded_files"])

# ==========================================
# --- 财务人员页面 (Finance Staff) ---
# ==========================================
def finance_page():
    st.title(f"财务管理 - 欢迎，{st.session_state.username}")
    df = load_data()
    
    st.subheader("📝 财务待办清单")
    st.write("以下是未完全开具发票、清单，或未收款的样品批次：")

    pending_finance_df = df[
        (df["invoice_status"] == "未开具") | 
        (df["list_status"] == "未开具") | 
        (df["payment_status"] == "否")
    ]

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
            "completion_date": st.column_config.TextColumn("完成时间", disabled=True),
            "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
            "payment_status": st.column_config.SelectboxColumn("是否收款", options=["否", "是"]),
            "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
            "uploaded_files": st.column_config.TextColumn("已上传文件", disabled=True)
        },
        key="finance_editor"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("保存财务状态更新"):
            df.update(edited_finance_df)
            save_data(df)
            st.success("财务状态已成功更新！")
            st.rerun()

    st.divider()
    with st.expander("📊 查看所有财务记录汇总"):
        edited_all_finance_df = st.data_editor(
            df,
            column_config={
                "id": "ID",
                "reception_date": st.column_config.DateColumn("接收时间", format="YYYY-MM-DD", disabled=True),
                "sender": st.column_config.TextColumn("寄样人", disabled=True),
                "sample_type": st.column_config.TextColumn("样品类型", disabled=True),
                "progress": st.column_config.TextColumn("当前进度", disabled=True),
                "invoice_status": st.column_config.SelectboxColumn("发票状态", options=["未开具", "已开具", "无需开具"]),
                "payment_status": st.column_config.SelectboxColumn("是否收款", options=["否", "是"]),
                "list_status": st.column_config.SelectboxColumn("清单状态", options=["未开具", "已开具", "无需开具"]),
                "uploaded_files": st.column_config.TextColumn("已上传文件", disabled=True)
            },
            disabled=["id", "reception_date", "sender", "sample_type", "quantity", "progress", "requirements", "completion_date", "uploaded_files"],
            key="all_finance_editor"
        )
        
        if st.button("保存所有状态更改"):
             save_data(edited_all_finance_df)
             st.success("所有更改已保存。")
             st.rerun()

# ==========================================
# --- 应用程序主入口 ---
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
        
        role_name = "科研" if st.session_state.role == "scientific" else "财务"
        st.sidebar.markdown(f"**角色:** {role_name}")
        
        if st.sidebar.button("注销"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()

        if st.session_state.role == "scientific":
            scientific_staff_page()
        elif st.session_state.role == "finance":
            finance_page()
        else:
            st.error("未知用户角色。")
