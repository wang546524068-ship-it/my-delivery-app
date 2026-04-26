import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="Warman 派送大师 Pro", layout="wide")
st.title("📍 Warman 专用高精度派送助手")
st.markdown("针对 **Warman, SK** 进行了地理编码优化，确保定位精准。")

# --- 1. 获取密钥 ---
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("密钥错误：请检查 Secrets 中的 MAPS_API_KEY 配置。")
    st.stop()

# --- 2. 核心纠偏逻辑 ---
# Warman 的地理中心点和边界
WARMAN_CENTER = (52.3219, -106.5843)
WARMAN_BOUNDS = {
    'northeast': [52.3600, -106.5300],
    'southwest': [52.2800, -106.6300]
}

def get_warman_location(addr):
    """
    针对 Warman 的深度地理编码优化
    """
    # 自动补全后缀，确保不漂移到其他城市
    search_query = f"{addr}, Warman, SK, Canada"
    
    # 使用 bounds 参数限制搜索结果在 Warman 范围内
    # 使用 region='ca' 确保偏向加拿大数据
    res = gmaps.geocode(
        search_query, 
        region='ca', 
        bounds=WARMAN_BOUNDS
    )
    
    if res:
        # 获取谷歌解析后的标准化地址和坐标
        loc_data = res[0]
        return {
            'input': addr,
            'latlng': loc_data['geometry']['location'],
            'full_address': loc_data['formatted_address'],
            'accuracy': loc_data['geometry'].get('location_type') # ROOFTOP 为最高级
        }
    return None

# --- 3. 界面输入 ---
raw_input = st.text_area("📋 粘贴地址清单 (每行一个，例如: 218 Railway St N)", height=250)

if raw_input:
    address_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if st.button("🚀 开启 Warman 精准规划"):
        if len(address_lines) < 2:
            st.error("请输入至少 2 个地址。")
        else:
            with st.spinner('正在精算 Warman 坐标并优化最优路径...'):
                # 步骤 A: 坐标精算
                valid_locations = []
                for line in address_lines:
                    loc = get_warman_location(line)
                    if loc:
                        valid_locations.append(loc)
                    else:
                        st.warning(f"无法精准定位地址: {line}")

                if len(valid_locations) < 2:
                    st.error("有效地址不足，无法规划。")
                    st.stop()

                # 步骤 B: 路径优化 (TSP 算法)
                # 谷歌 API 单次 waypoint 限制为 25 个
                try:
                    # 使用坐标点 (latlng) 而非文字进行规划，精度最高
                    directions = gmaps.directions(
                        origin=valid_locations[0]['latlng'],
                        destination=valid_locations[-1]['latlng'],
                        waypoints=[v['latlng'] for v in valid_locations[1:-1]],
                        optimize_waypoints=True, # 自动寻找最短路径
                        mode="driving",
                        departure_time=datetime.now()
                    )

                    if directions:
                        route = directions[0]
                        order = route.get('waypoint_order', [])
                        
                        # 重新排列优化后的清单
                        final_sequence = [valid_locations[0]]
                        for idx in order:
                            final_sequence.append(valid_locations[idx + 1])
                        final_sequence.append(valid_locations[-1])

                        # --- 4. 地图展示 ---
                        col_m, col_l = st.columns([2, 1])
                        
                        with col_m:
                            # 初始化地图，中心设在 Warman
                            m = folium.Map(location=WARMAN_CENTER, zoom_start=14)
                            
                            # 绘制真实马路轨迹
                            path = googlemaps.convert.decode_polyline(route['overview_polyline']['points'])
                            folium.PolyLine([(p['lat'], p['lng']) for p in path], color="#2563EB", weight=6).add_to(m)

                            # 绘制带编号的 Marker
                            for i, item in enumerate(final_sequence, 1):
                                is_start = (i == 1)
                                is_end = (i == len(final_sequence))
                                color = "#DC2626" if is_start else ("#111827" if is_end else "#2563EB")
                                
                                folium.Marker(
                                    location=[item['latlng']['lat'], item['latlng']['lng']],
                                    icon=folium.DivIcon(html=f"""
                                        <div style="background-color:{color}; color:white; border-radius:50%; 
                                        width:28px; height:28px; display:flex; align-items:center; justify-content:center;
                                        font-size:12px; font-weight:bold; border:2px solid white; box-shadow: 0px 2px 4px rgba(0,0,0,0.3);">{i}</div>"""),
                                    popup=f"站 {i}: {item['input']}"
                                ).add_to(m)
                            
                            folium_static(m, width=900)

                        with col_l:
                            st.subheader("📊 派送统计")
                            km = sum(leg['distance']['value'] for leg in route['legs']) / 1000
                            mins = sum(leg['duration']['value'] for leg in route['legs']) / 60
                            st.metric("总里程", f"{km:.1f} km")
                            st.metric("预计耗时", f"{mins:.0f} 分钟")
                            
                            st.divider()
                            st.write("📋 **派送顺序列表：**")
                            for i, item in enumerate(final_sequence, 1):
                                # 显示解析到的完整地址，方便纠错
                                st.markdown(f"**{i}. {item['input']}**")
                                st.caption(f"系统识别: {item['full_address']}")

                except Exception as e:
                    st.error(f"路径规划出错: {e}")
