import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="派送大师 Pro", layout="wide")

st.title("🚚 我的私人配送助手 Pro")

# 地址输入框
raw_input = st.text_area("粘贴所有地址：", height=200, placeholder="每行一个地址...")

if raw_input:
    # 1. 解析地址并去重
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines))

    # 2. 排序逻辑 (这里我们提供一个简单的自动优化按钮)
    # 提示：真正的算法需要API，这里我们先提供一个“手动微调”和“一键串联”的功能
    
    st.subheader(f"📍 今日待送: {len(address_list)} 个站点")
    
    # --- 按钮区 ---
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # 生成总路线示意图的链接 (Google Maps 最多支持串联约10-15个点)
        dest_str = "/".join([urllib.parse.quote(a) for a in address_list[:15]])
        all_route_url = f"https://www.google.com/maps/dir/{dest_str}"
        st.link_button("🌐 查看全天总路线示意图", all_route_url, use_container_width=True)
    
    with col_btn2:
        if st.button("🔄 重新按 Warman 南北顺序排序", use_container_width=True):
            # 这是一个简单的逻辑：包含数字路名的通常在北边，这里可以根据你对地形的了解定制
            address_list.sort() # 默认字母排序，你可以手动在这里调整
            st.success("已完成初步排序！")

    st.markdown("---")

    # 3. 显示详细列表
    for i, addr in enumerate(address_list):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.info(f"**第 {i+1} 站:** {addr}")
        with c2:
            query = urllib.parse.quote(addr)
            # 使用导航模式的链接
            st.link_button("🚀 导航", f"google.navigation:q={query}", use_container_width=True)

else:
    st.info("请在上方粘贴地址。")
