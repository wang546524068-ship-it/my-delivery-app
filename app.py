import streamlit as st
import pandas as pd
import urllib.parse

# 页面配置：设置为宽屏，标题为“派送清单”
st.set_page_config(page_title="我的派送清单", layout="wide")

# 隐藏 Streamlit 默认的顶部边距，让手机屏幕显示更多内容
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .stButton button {width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white;}
    </style>
    """, unsafe_allow_html=True)

st.title("📦 每日派送助手")

# 1. 地址输入区域
st.subheader("1. 粘贴地址列表")
raw_input = st.text_area("请把所有地址粘贴在下面：", height=150, placeholder="每行一个地址...")

if raw_input:
    # 解析地址并去重，保持原始粘贴顺序
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines))
    
    st.markdown("---")
    
    # 2. 功能按钮
    col_a, col_b = st.columns(2)
    with col_a:
        # 生成总路线预览图（前15站）
        dest_str = "/".join([urllib.parse.quote(a) for a in address_list[:15]])
        all_route_url = f"https://www.google.com/maps/dir/{dest_str}"
        st.link_button("🌐 查看全天预览图", all_route_url)
    
    with col_b:
        if st.button("🗑️ 清空列表"):
            st.rerun()

    st.subheader(f"📍 待配送清单 (共 {len(address_list)} 站)")

    # 3. 核心列表：纯数字编号 + 大导航按钮
    for i, addr in enumerate(address_list):
        # 使用列布局：左侧数字和地址，右侧大按钮
        cols = st.columns([4, 2])
        
        with cols[0]:
            # 用加粗数字显示站点
            st.markdown(f"### {i+1}")
            st.write(addr)
            
        with cols[1]:
            # 编码地址用于跳转导航
            query = urllib.parse.quote(addr)
            # 使用 google.navigation 协议直接唤起手机导航模式
            nav_url = f"google.navigation:q={query}"
            st.link_button("🚀 导航", nav_url)
        
        st.markdown("---") # 每一站之间划一条线，方便区分

else:
    st.info("👋 你好！请在上方输入框粘贴地址，我会自动为你生成带数字编号的导航清单。")
