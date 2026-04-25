import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static
import time

# --- 页面配置 ---
st.set_page_config(page_title="派送大师 Pro Max", layout="wide")
st.title("🚚 派送大师 Pro Max (60站全自动版)")

# --- 1. 获取密钥 ---
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("请检查 Secrets 中的 MAPS_API_KEY 配置。")
    st.stop()

# --- 2. 侧边栏设置 (纠偏关键) ---
with st.sidebar:
    st.header("📍 定位纠偏设置")
    locked_city = st.text_input("目标城市", "Warman")
    locked_prov = st.text_input("目标省份", "SK")
    locked_country = "Canada"
    st.info("系统会自动为所有地址补充以上后缀，确保定位精准。")

# --- 3. 地址输入 ---
raw_input = st.text_area("粘贴地址清单 (建议每次 60 个以内)：", height=300, placeholder="每行一个地址...")

# --- 4. 核心功能函数 ---
def get_precise_geocode(addr):
    """带偏置逻辑的地理编码"""
    full_addr = f"{addr}, {locked_city}, {locked_prov}, {locked_country}"
    # 限制在 Warman 附近搜索 (Location Bias)
    # 坐标大约是 Warman 中心: 52.3219, -106.5843
    res = gmaps.geocode(full_addr, region='ca')
    if res:
        return {
            'original': addr,
            'latlng': res[0]['geometry']['location'],
            'formatted': res[0]['formatted_address']
        }
    return None

if raw_input:
    input_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if st.button("🚀 开始超长路径优化规划"):
        if len(input_lines) < 2:
            st.error("请至少输入两个地址。")
        else:
            with st.spinner(f'正在对 {len(input_lines)} 个点进行坐标精算与分段规划...'):
                # 步骤 A: 坐标精算 (Geocoding)
                valid_locations = []
                for addr in input_lines:
                    loc = get_precise_geocode(addr)
                    if loc:
                        valid_locations.append(loc)
                    else:
                        st.warning(f"无法定位地址: {addr}，已跳过。")
                
                # 步骤 B: 分段逻辑 (突破 25 个限制)
                # 谷歌 API 单次 waypoint 上限是 23 (加上起点终点共 25)
                # 我们按每 23 个点为一段进行切割
                MAX_WAYPOINTS = 23
                optimized_full_list = []
                total_distance = 0
                full_path_points = []

                # 如果站点多，分批处理
                for i in range(0, len(valid_locations), MAX_WAYPOINTS):
                    chunk = valid_locations[i : i + MAX_WAYPOINTS + 1]
                    if len(chunk) < 2: break
                    
                    # 调用 Directions API
                    res = gmaps.directions(
                        origin=chunk[0]['latlng'],
                        destination=chunk[-1]['latlng'],
                        waypoints=[c['latlng'] for c in chunk[1:-1]],
                        optimize_waypoints=True,
                        mode="driving"
                    )
                    
                    if res:
                        route = res[0]
                        # 获取这一段的优化顺序
                        order = route.get('waypoint_order', [])
                        
                        # 按优化后的顺序把点存入总列表
                        # 每一段的起点
                        if not optimized_full_list:
                            optimized_full_list.append(chunk[0])
                        
                        # 每一段优化的中间点
                        for idx in order:
                            optimized_full_list.append(chunk[idx + 1])
                        
                        # 每一段的终点
                        optimized_full_list.append(chunk[-1])
                        
                        # 累计里程和路径线
                        total_distance += sum(leg['distance']['value'] for leg in route['legs'])
                        decoded_line = googlemaps.convert.decode_polyline(route['overview_polyline']['points'])
                        full_path_points.extend([(p['lat'], p['lng']) for p in decoded_line])

                # --- 5. 地图展示与结果渲染 ---
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.subheader("🗺️ 智能路径示意图")
                    # 创建地图
                    m = folium.Map(location=[optimized_full_list[0]['latlng']['lat'], optimized_full_list[0]['latlng']['lng']], zoom_start=13)
                    
                    # 绘制总线路
                    folium.PolyLine(full_path_points, color="#2196F3", weight=6, opacity=0.8).add_to(m)

                    # 标记站点编号
                    for i, item in enumerate(optimized_full_list, 1):
                        # 起点红色，其余蓝色
                        color = "#f44336" if i == 1 else "#3f51b5"
                        folium.Marker(
                            location=[item['latlng']['lat'], item['latlng']['lng']],
                            icon=folium.DivIcon(html=f"""
                                <div style="background-color:{color}; color:white; border-radius:50%; 
                                width:24px; height:24px; display:flex; align-items:center; justify-content:center;
                                font-size:11px; font-weight:bold; border:2px solid white; box-shadow:0 2px 5px rgba(0,0,0,0.2);">{i}</div>"""),
                            popup=item['original']
                        ).add_to(m)
                    
                    folium_static(m, width=900)

                with col2:
                    st.subheader("📊 行程概览")
                    st.metric("总里程", f"{total_distance/1000:.1f} km")
                    st.metric("总站点数", f"{len(optimized_full_list)} 站")
                    
                    st.write("---")
                    st.write("📋 **派送顺序：**")
                    for i, item in enumerate(optimized_full_list, 1):
                        st.write(f"**{i}.** {item['original']}")
