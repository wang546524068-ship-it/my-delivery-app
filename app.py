import streamlit as st
import googlemaps
import folium
import pandas as pd
from streamlit_folium import folium_static
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="派送大师 Pro - 全面升级版", layout="wide", initial_sidebar_state="expanded")

# 自定义 CSS 样式
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 派送大师 Pro (V2.0 全面升级版)")
st.info("集成了 Google TSP (旅行商算法) 优化，支持真实路网规划及多站导航导出。")

# --- 1. API 核心连接 ---
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except Exception as e:
    st.error("❌ 密钥配置错误：请检查 Streamlit Secrets 中的 MAPS_API_KEY")
    st.stop()

# --- 2. 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 规划设置")
    city_context = st.text_input("默认搜索城市/省份", "Warman, SK")
    st.divider()
    optimize_for = st.radio("优化目标", ["最快时间 (考慮路況)", "最短距离"])
    st.caption("提示：当站点超过25个时，由于谷歌API限制，建议分两批导入规划。")

# --- 3. 地址处理区域 ---
raw_input = st.text_area("📍 输入派送地址清单（每行一个）", height=250, placeholder="例如：\n218 Railway St N\n502 2nd Ave N\n...")

if raw_input:
    # 预处理：清洗地址并补全城市信息
    input_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if st.button("🌟 开始深度优化最优路线"):
        if len(input_lines) < 2:
            st.error("请输入至少 2 个地址。")
        elif len(input_lines) > 27:
            st.warning("⚠️ 检测到超过 25 个中途点。Google API 可能会拒绝优化请求。建议先处理前 25 个。")
        
        with st.spinner('🚀 正在连接 Google 交通大数据中心进行智能排程...'):
            try:
                # 补全地址以防解析错误
                full_addrs = [f"{a}, {city_context}" if city_context.lower() not in a.lower() else a for a in input_lines]
                
                # 调用 Directions API
                # origin: 第一个地址, destination: 最后一个地址 (通常是返回点或最后一个送货点)
                # optimize_waypoints=True 启动谷歌 TSP 算法
                directions_result = gmaps.directions(
                    origin=full_addrs[0],
                    destination=full_addrs[-1],
                    waypoints=full_addrs[1:-1] if len(full_addrs) > 2 else None,
                    optimize_waypoints=True,
                    mode="driving",
                    language="zh-CN",
                    departure_time=datetime.now() # 考虑当前实时路况
                )

                if not directions_result:
                    st.error("无法解析路线，请检查地址是否准确。")
                else:
                    res = directions_result[0]
                    waypoint_order = res.get('waypoint_order', [])
                    
                    # 构建重新排序后的地址清单
                    optimized_list = [input_lines[0]] # 起点
                    for idx in waypoint_order:
                        optimized_list.append(input_lines[idx + 1])
                    if len(input_lines) > 1:
                        optimized_list.append(input_lines[-1]) # 终点

                    # --- 4. 结果展示与地图 ---
                    col_map, col_list = st.columns([2, 1])

                    with col_map:
                        st.subheader("🗺️ 智能导航示意图")
                        # 初始地图中心
                        center = res['legs'][0]['start_location']
                        m = folium.Map(location=[center['lat'], center['lng']], zoom_start=13, tiles="cartodbpositron")

                        # 绘制蓝色行驶路径
                        path = googlemaps.convert.decode_polyline(res['overview_polyline']['points'])
                        folium.PolyLine([(p['lat'], p['lng']) for p in path], color="#3D5AFE", weight=6, opacity=0.8).add_to(m)

                        # 循环标记每一个站点
                        for i, addr in enumerate(optimized_list, 1):
                            # 获取各段坐标
                            if i <= len(res['legs']):
                                loc = res['legs'][i-1]['start_location']
                            else:
                                loc = res['legs'][-1]['end_location']
                            
                            # 标记不同颜色：起点红色，终点黑色，中间蓝色
                            icon_color = "red" if i == 1 else ("black" if i == len(optimized_list) else "blue")
                            
                            folium.Marker(
                                location=[loc['lat'], loc['lng']],
                                icon=folium.DivIcon(html=f"""
                                    <div style="background-color:{icon_color}; color:white; border-radius:50%; 
                                    width:24px; height:24px; display:flex; align-items:center; justify-content:center;
                                    font-size:12px; font-weight:bold; border:2px solid white;">{i}</div>"""),
                                popup=f"第{i}站: {addr}"
                            ).add_to(m)
                        
                        folium_static(m, width=800)

                    with col_list:
                        st.subheader("📋 派送顺序清单")
                        total_dist = sum(leg['distance']['value'] for leg in res['legs']) / 1000
                        total_mins = sum(leg['duration']['value'] for leg in res['legs']) / 60
                        
                        st.metric("总里程", f"{total_dist:.1f} km")
                        st.metric("预计耗时", f"{total_mins:.0f} 分钟")
                        
                        st.divider()
                        
                        for i, addr in enumerate(optimized_list, 1):
                            st.write(f"**{i}.** {addr}")
                        
                        # --- 5. 导出功能 ---
                        st.divider()
                        # 生成 Google Maps 批量链接 (方便手机一键开启)
                        base_url = "https://www.google.com/maps/dir/"
                        nav_url = base_url + "/".join([googlemaps.convert.quote(a + f", {city_context}") for a in optimized_list])
                        st.link_button("📱 打开手机 Google Maps 导航", nav_url)

            except Exception as e:
                st.error(f"规划失败，报错信息：{str(e)}")

