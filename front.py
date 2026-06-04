import streamlit as st
import pandas as pd
import requests
import io

# ---------- 配置 ----------
API_BASE_URL = "http://localhost:8080/webapi"

# 设置页面
st.set_page_config(page_title="招聘岗位发布系统", layout="wide")
st.title("📋 招聘岗位发布系统")

# ---------- 工具函数 ----------
def fetch_positions():
    """从后端获取所有岗位"""
    try:
        resp = requests.get(f"{API_BASE_URL}/positions", timeout=5)
        resp.raise_for_status()
        return resp.json()["data"]
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端服务，请确保后端已启动 (端口8080)")
        return []
    except Exception as e:
        st.error(f"❌ 获取岗位列表失败: {str(e)}")
        return []

def create_position(title, responsibilities, requirements, bonus):
    """调用新增岗位 API"""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/positions",
            json={
                "title": title,
                "responsibilities": responsibilities,
                "requirements": requirements,
                "bonus": bonus
            },
            timeout=5
        )
        resp.raise_for_status()
        return True, "新增成功"
    except Exception as e:
        return False, f"新增失败: {str(e)}"

def update_position(position_id, title, responsibilities, requirements, bonus):
    """调用更新岗位 API"""
    try:
        data = {}
        if title:
            data["title"] = title
        if responsibilities:
            data["responsibilities"] = responsibilities
        if requirements:
            data["requirements"] = requirements
        if bonus is not None:
            data["bonus"] = bonus
        resp = requests.put(
            f"{API_BASE_URL}/positions/{position_id}",
            json=data,
            timeout=5
        )
        resp.raise_for_status()
        return True, "更新成功"
    except Exception as e:
        return False, f"更新失败: {str(e)}"

def delete_position(position_id):
    """调用删除岗位 API"""
    try:
        resp = requests.delete(
            f"{API_BASE_URL}/positions/{position_id}",
            timeout=5
        )
        resp.raise_for_status()
        return True, "删除成功"
    except Exception as e:
        return False, f"删除失败: {str(e)}"

def batch_upload_positions(positions_list):
    """调用批量上传 API"""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/positions/batch",
            json={"positions": positions_list},
            timeout=10
        )
        resp.raise_for_status()
        return True, resp.json().get("message", "导入成功")
    except Exception as e:
        return False, f"批量导入失败: {str(e)}"

# ---------- 页面主体 ----------

# 侧边栏 - 新增/编辑岗位
with st.sidebar:
    st.header("➕ 新增 / 编辑岗位")
    edit_mode = st.checkbox("编辑模式")
    
    # 编辑模式下选择要编辑的岗位
    selected_id = None
    if edit_mode:
        all_positions = fetch_positions()
        if all_positions:
            # 构建选项，格式："ID - 岗位名称"
            options = {f"{p['id']} - {p['title']}": p for p in all_positions}
            selected_key = st.selectbox("选择要编辑的岗位", list(options.keys()))
            if selected_key:
                selected_id = options[selected_key]["id"]
                default_title = options[selected_key]["title"]
                default_responsibilities = options[selected_key]["responsibilities"]
                default_requirements = options[selected_key]["requirements"]
                default_bonus = options[selected_key].get("bonus", "")
        else:
            st.warning("暂无岗位数据")
            edit_mode = False  # 无法编辑

    # 输入表单
    with st.form(key="position_form", clear_on_submit=not edit_mode):
        if edit_mode and selected_id:
            title = st.text_input("岗位名称", value=default_title)
            responsibilities = st.text_area("岗位职责", value=default_responsibilities, height=150)
            requirements = st.text_area("岗位要求", value=default_requirements, height=150)
            bonus = st.text_area("加分项", value=default_bonus, height=100)
        else:
            title = st.text_input("岗位名称")
            responsibilities = st.text_area("岗位职责", height=150)
            requirements = st.text_area("岗位要求", height=150)
            bonus = st.text_area("加分项", height=100)

        submitted = st.form_submit_button("💾 保存")
        
        if submitted:
            if not title or not responsibilities or not requirements:
                st.error("岗位名称、岗位职责和岗位要求不能为空")
            else:
                if edit_mode and selected_id:
                    # 执行更新
                    success, msg = update_position(selected_id, title, responsibilities, requirements, bonus)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    # 执行新增
                    success, msg = create_position(title, responsibilities, requirements, bonus)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# 主区域 - 岗位列表
st.header("📄 岗位列表")
positions = fetch_positions()

if positions:
    # 转换为 DataFrame 显示
    df = pd.DataFrame(positions)
    df = df.rename(columns={
        "id": "ID",
        "title": "岗位名称",
        "responsibilities": "岗位职责",
        "requirements": "岗位要求",
        "bonus": "加分项"
    })
    
    # 显示表格
    col1, col2 = st.columns([4, 1])
    with col1:
        st.dataframe(df, width="stretch", hide_index=True)
    with col2:
        st.write(f"共 {len(positions)} 个岗位")
    
    # 删除操作
    st.subheader("🗑️ 删除岗位")
    delete_ids = st.multiselect(
        "选择要删除的岗位 ID（支持多选）",
        options=[p['id'] for p in positions],
        format_func=lambda x: f"ID:{x} - {next((p['title'] for p in positions if p['id']==x), '')}"
    )
    if st.button("确认删除选中岗位"):
        if not delete_ids:
            st.warning("请至少选择一个岗位")
        else:
            success_count = 0
            for pid in delete_ids:
                success, msg = delete_position(pid)
                if success:
                    success_count += 1
                else:
                    st.error(f"删除 ID {pid} 失败: {msg}")
            if success_count > 0:
                st.success(f"成功删除 {success_count} 个岗位")
                st.rerun()
else:
    st.info("暂无岗位数据，请新增岗位或批量上传")

# 批量上传区域
st.header("📤 Excel 批量上传")
st.markdown("上传 Excel 文件（需包含 `title`、`responsibilities`、`requirements` 列，`bonus` 列可选）")
uploaded_files = st.file_uploader(
    "选择文件（支持多选）",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    for idx, uploaded_file in enumerate(uploaded_files):
        st.subheader(f"📄 文件 {idx+1}: {uploaded_file.name}")
        try:
            # 读取 Excel
            excel_df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # 验证必须列
            required_cols = {"title", "responsibilities", "requirements"}
            if not required_cols.issubset(excel_df.columns):
                missing = required_cols - set(excel_df.columns)
                st.error(f"❌ 文件 {uploaded_file.name} 缺少必需列：{', '.join(missing)}")
                continue  # 跳过该文件，继续处理下一个
            
            st.success(f"文件 {uploaded_file.name} 解析成功，预览前5行：")
            st.dataframe(excel_df.head(), width="stretch")
            
            # 将 NaN 替换为空字符串
            excel_df = excel_df.fillna("")
            
            # 确保 bonus 列存在（可选列）
            if "bonus" not in excel_df.columns:
                excel_df["bonus"] = ""
            
            # 转换为列表
            positions_data = excel_df[["title", "responsibilities", "requirements", "bonus"]].to_dict(orient="records")
            
            # 为每个文件单独创建导入按钮，防止相互干扰
            if st.button(f"🚀 确认导入 {uploaded_file.name}", key=f"import_{uploaded_file.name}_{idx}"):
                success, msg = batch_upload_positions(positions_data)
                if success:
                    st.success(f"{uploaded_file.name} 导入成功: {msg}")
                    st.rerun()
                else:
                    st.error(f"{uploaded_file.name} 导入失败: {msg}")
        except Exception as e:
            st.error(f"解析文件 {uploaded_file.name} 出错: {str(e)}")
