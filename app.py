import streamlit as st
import pandas as pd
import urllib.parse

# 页面基础配置
st.set_page_config(page_title="派送大师", layout="wide")

st.title("🚚 我的私人配送助手")
st.markdown("---")

# 侧边栏说明
with st.sidebar:
    st.header("操作指南")
    st.write("1. 粘贴地址列表")
    st.write("2. 系统自动生成编号")
    st.write("3. 点击‘去导航’唤起地图")

# 地址输入框
raw_input = st.text_area("直接粘贴所有地址（每行一个）：", height=250, placeholder="例如：\n3 Solar Rd, Warman, SK\n420 Eldorado St, Warman, SK")

if raw_input:
    # 解析并去重
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines)) # 保持顺序去重
    
    st.subheader(f"📍 今日待送: {len(address_list)} 个站点")
    
    # 建立展示表格
    for i, addr in enumerate(address_list):
        # 创建两列，一列显示地址，一列放置按钮
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**站点 {i+1}:** {addr}")
            
        with col2:
            # 构建 Google 地图链接
            query = urllib.parse.quote(addr)
            google_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            st.link_button("🚀 导航", google_url, use_container_width=True)

    if st.button("🗑️ 清空列表"):
        st.rerun()
else:
    st.warning("请在上方粘贴地址以开始。")
