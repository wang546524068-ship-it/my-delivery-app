import streamlit as st
import pandas as pd
import urllib.parse

# 页面配置
st.set_page_config(page_title="私人配送助手", layout="wide")

# 强制手机端样式优化
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .stButton button {
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #28a745; 
        color: white; 
        font-weight: bold;
        border: none;
    }
    .address-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 配送清单 (数字版)")

# 1. 地址输入
raw_input = st.text_area("在此粘贴地址列表：", height=150)

if raw_input:
    # 解析并去重
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines))
    
    st.markdown("---")
    
    # 2. 全局分布按钮（不带连线，只带标注）
    # 使用 Google Maps Search 模式来展示所有点，避免 A-B-C 连线
    search_query = urllib.parse.quote("Warman, SK")
    # 如果想在地图上看到多个点，最简单免费办法是跳转到已搜好的预览
    st.link_button("📍 在地图上查看所有位置分布", f"https://www.google.com/maps/search/{search_query}")

    st.subheader(f"🔢 今日任务：{len(address_list)} 站")

    # 3. 核心清单展示
    for i, addr in enumerate(address_list):
        # 创建一个容器模拟卡片样式
        with st.container():
            col_text, col_nav = st.columns([3, 2])
            
            with col_text:
                # 巨大的数字编号
                st.markdown(f"### 站点 {i+1}")
                st.write(addr)
            
            with col_nav:
                # 编码地址
                encoded_addr = urllib.parse.quote(addr)
                # 使用标准的 Google Maps 导航协议
                # 这种格式会直接打开手机 App 并进入该地点的预览或导航页
                final_nav_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
                st.link_button("🚀 开始导航", final_nav_url)
            
            st.markdown("---")

else:
    st.info("请先粘贴地址列表。")
