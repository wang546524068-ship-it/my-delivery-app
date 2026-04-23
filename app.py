import streamlit as st
import pandas as pd
import urllib.parse

# 页面配置
st.set_page_config(page_title="派送大师 2026版", layout="wide")

# CSS 样式：优化手机端显示，大数字，绿按钮
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    .stButton button {
        width: 100%; border-radius: 12px; height: 3.5em; 
        background-color: #28a745; color: white; font-weight: bold; border: none;
    }
    .address-box {
        background-color: #ffffff; padding: 12px; border-radius: 10px;
        border: 1px solid #ddd; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 终极派送清单")

# 1. 地址输入
raw_input = st.text_area("在此粘贴全部地址：", height=150, placeholder="每行一个地址...")

if raw_input:
    # 解析并去重
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines))
    
    st.markdown("---")
    
    # 2. 全分布地图按钮
    # 策略：我们将地址转化为搜索词，利用 Google Maps 的“搜索附近”功能来标记
    # 对于多点展示，最稳定且免费的方法是引导用户进入 Google Maps 的特定搜索视图
    all_addr_query = "+OR+".join([urllib.parse.quote(f'"{a}"') for a in address_list[:10]]) # 限制前10个以保证链接不崩溃
    map_url = f"https://www.google.com/maps/search/{all_addr_query}"
    
    st.link_button("📍 在地图中预览所有站点分布 (前10站示例)", map_url)
    st.caption("提示：由于谷歌限制，全图预览通常只支持同时显示部分站点。")

    st.subheader(f"🔢 派送顺序 (共 {len(address_list)} 站)")

    # 3. 核心清单：大数字编号 + 修复版导航按钮
    for i, addr in enumerate(address_list):
        with st.container():
            col_idx, col_content, col_btn = st.columns([1, 4, 3])
            
            with col_idx:
                # 醒目的数字编号
                st.markdown(f"## {i+1}")
            
            with col_content:
                st.write(addr)
            
            with col_btn:
                encoded_addr = urllib.parse.quote(addr)
                # 使用谷歌官方推荐的 Universal Link，自动匹配 App 或浏览器
                nav_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
                st.link_button("🚀 导航", nav_url)
            
            st.markdown("---")

else:
    st.info("💡 粘贴地址后，这里会显示 1, 2, 3... 纯数字编号的派送列表。")
