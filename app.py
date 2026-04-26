import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="派送大师 Pro Max", layout="wide")
st.title("🚚 派送大师 Pro Max (高精度路径优化版)")

# --- 1. 获取密钥 ---
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("密钥错误：请检查 Secrets 中的 MAPS_API_KEY 配置。")
    st.stop()

# --- 2. 侧边栏纠偏配置 ---
with st.sidebar:
    st.header("📍 区域纠偏设置")
    locked_city = st.text_input("目标城市", "Warman")
    locked_prov = st.text_input("省份", "SK")
    st.info("系统会自动修正地址，防止定位到其他省份或城市。")
    optimize_mode = st.radio("优化首选", ["最短时间", "最短路程"])

# --- 3. 地址输入 ---
raw_input = st.text_area("粘贴地址清单：", height=250, placeholder="每行一个地址...")

# --- 4. 核心逻辑函数 ---
def geocode_address(addr):
    """带城市锁定的高精度地理编码"""
    # 强制拼接城市名，确保唯一性
    full_addr = f"{addr}, {locked_city}, {locked_prov}, Canada"
    # 使用 region 偏置
    res = gmaps.geocode(full_addr, region='ca')
    if res:
        return {
            'addr': addr,
            'latlng': res[0]['geometry']['location'],
            'place_id': res[0]['place_id']
        }
    return None

if raw_input:
    input_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if st.button("🚀 执行高精度路径规划"):
        if len(input_lines) < 2:
            st.error("请输入至少两个地址。")
        else:
            with st.spinner('正在精算坐标并优化最优路径...'):
                # 步骤 A: 预转换坐标 (确保位置准确)
                coords_list = []
                for line in input_lines:
                    loc = geocode_address(line)
                    if loc:
                        coords_list.append(loc)
                    else:
                        st.warning(f"无法精准定位: {line}，请检查格式。")

                if len(coords_list) < 2:
                    st.stop()

                # 步骤 B: 路径优化请求
                # 谷歌一次最多支持 25 个点优化。
                # 如果点数多，我们会按批次处理，但这里为了保证“最优”，我们优先展示前 25 个
                try:
                    directions_result = gmaps.directions(
                        origin=coords_list[0]['latlng'],
                        destination=coords_list[-1]['latlng'],
                        waypoints=[c['latlng'] for c in coords_list[1:-1]],
                        optimize_waypoints=True, # 核心优化算法
                        mode="driving",
                        departure_time=datetime.now() # 考虑路况
                    )

                    if not directions_result:
                        st.error("规划失败：谷歌未能计算出有效线路。")
                    else:
                        route = directions_result[0]
                        order = route.get('waypoint_order', [])
                        
                        # 重新构建优化后的顺序
                        optimized_order = [coords_list[0]] # 起点
                        for idx in order:
                            optimized_order.append(coords_list[idx + 1])
                        optimized_order.append(coords_list[-1]) # 终点

                        # --- 5. 地图展示 ---
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            m = folium.Map(location=[optimized_order[0]['latlng']['lat'], optimized_order[0]['latlng']['lng']], zoom_start=13)
                            
                            # 绘制路网贴合线
                            polyline = googlemaps.convert.decode_polyline(route['overview_polyline']['points'])
                            folium.PolyLine([(p['lat'], p['lng']) for p in polyline], color="#1A73E8", weight=6).add_to(m)

                            # 打点编号
                            for i, item in enumerate(optimized_order, 1):
                                folium.Marker(
                                    location=[item['latlng']['lat'], item['latlng']['lng']],
                                    icon=folium.DivIcon(html=f"""
                                        <div style="background-color:{'#E94235' if i==1 else '#1A73E8'}; color:white; border-radius:50%; 
                                        width:26px; height:26px; display:flex; align-items:center; justify-content:center;
                                        font-size:11px; font-weight:bold; border:2px solid white; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">{i}</div>"""),
                                    popup=item['addr']
                                ).add_to(m)
                            
                            folium_static(m, width=800)

                        with col2:
                            dist_km = sum([leg['distance']['value'] for leg in route['legs']]) / 1000
                            time_min = sum([leg['duration']['value'] for leg in route['legs']]) / 60
                            st.metric("总里程", f"{dist_km:.1f} km")
                            st.metric("预计行驶时间", f"{time_min:.0f} 分钟")
                            st.divider()
                            st.write("📋 **最优顺序清单：**")
                            for i, item in enumerate(optimized_order, 1):
                                st.write(f"**{i}.** {item['addr']}")

                except Exception as e:
                    st.error(f"发生错误: {e}")
