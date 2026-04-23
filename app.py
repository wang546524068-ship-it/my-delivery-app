import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="私人配送助手 AI版", layout="wide")

# ==========================================
# 1. 配置你的 API KEY
# ==========================================
API_KEY = "AIzaSyCHVm0sk4fbhxUUeFVFeYHHcfUTHJnPmyk" 

# ==========================================
# 2. 核心算法：地理编码与路径优化
# ==========================================
def get_lat_lng(address):
    """将地址转换为经纬度"""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={API_KEY}"
    try:
        res = requests.get(url).json()
        if res['status'] == 'OK':
            loc = res['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except:
        return None, None

def solve_tsp(addresses):
    """最近邻算法：从第一个点开始，每次找最近的下一个点"""
    if not addresses: return []
    
    # 获取所有点的经纬度数据
    nodes = []
    with st.spinner('正在定位地址坐标...'):
        for addr in addresses:
            lat, lng = get_lat_lng(addr)
            if lat is not None:
                nodes.append({"addr": addr, "lat": lat, "lng": lng})
    
    if not nodes: return addresses
    
    # 路径规划逻辑
    unvisited = nodes[:]
    optimized_route = []
    # 默认第一个地址为起始点
    current_node = unvisited.pop(0)
    optimized_route.append(current_node['addr'])
    
    while unvisited:
        # 计算距离当前点最近的一个
        next_node = min(unvisited, key=lambda x: (x['lat']-current_node['lat'])**2 + (x['lng']-current_node['lng'])**2)
        optimized_route.append(next_node['addr'])
        unvisited.remove(next_node)
        current_node = next_node
        
    return optimized_route

# ==========================================
# 3. 网页界面设计
# ==========================================
st.title("🚀 智能路径规划系统")

raw_input = st.text_area("在此粘贴原始地址列表：", height=150, placeholder="每行一个地址...")

if raw_input:
    lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    address_list = list(dict.fromkeys(lines))
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✨ 智能优化排序 (最短路径)", type="primary", use_container_width=True):
            if "AIza" not in API_KEY:
                st.error("请先在代码中填入正确的 API Key！")
            else:
                st.session_state.final_list = solve_tsp(address_list)
                st.success("优化成功！已按地理位置重新排队。")

    with col2:
        if st.button("🗑️ 重置", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # 获取当前显示的列表（优化后的或原始的）
    display_list = st.session_state.get('final_list', address_list)

    st.markdown("---")
    st.subheader(f"🔢 派送清单 (共 {len(display_list)} 站)")

    for i, addr in enumerate(display_list):
        # 手机端大卡片设计
        with st.container():
            c1, c2 = st.columns([4, 2])
            with c1:
                st.markdown(f"### {i+1}")
                st.write(addr)
            with c2:
                encoded_addr = urllib.parse.quote(addr)
                # 统一使用最优的导航跳转协议
                nav_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
                st.link_button("🚀 导航", nav_url)
            st.markdown("---")
