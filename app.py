import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static

# 页面设置
st.set_page_config(page_title="派送大师 Pro - 精度修复版", layout="wide")

try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("API Key 缺失")
    st.stop()

def get_clean_order():
    st.title("🚚 派送助手 - 深度精度修复版")
    
    # 增加城市和后缀锁定，防止定位到外地
    with st.sidebar:
        city = st.text_input("锁定城市", "Warman")
        province = st.text_input("锁定省份", "SK")
        country = "Canada"

    raw_input = st.text_area("粘贴地址清单：", height=200)
    
    if st.button("🚀 深度优化线路"):
        # 1. 强化地址清洗
        temp_list = [line.strip() for line in raw_input.split('\n') if line.strip()]
        
        # 强制格式化地址：[原始地址], [城市], [省份], [国家]
        # 这样可以极大提高 Geocoding 的准确度
        formatted_addresses = [f"{addr}, {city}, {province}, {country}" for addr in temp_list]
        
        with st.spinner('正在进行坐标精算...'):
            try:
                # 2. 增加地址校验逻辑：先转成经纬度，防止 Directions 识别错误
                valid_locations = []
                for original, full in zip(temp_list, formatted_addresses):
                    geocode_result = gmaps.geocode(full)
                    if geocode_result:
                        loc = geocode_result[0]['geometry']['location']
                        valid_locations.append({
                            'original': original,
                            'full': full,
                            'latlng': (loc['lat'], loc['lng'])
                        })
                
                if not valid_locations:
                    st.error("无法识别任何地址")
                    return

                # 3. 调用 Directions API (使用坐标而不是文字地址，这样最准)
                # 注意：谷歌限制中间点最多 23 个（加上起点终点共 25）
                # 如果你超过 25 个点，这里必须分两段处理
                if len(valid_locations) > 25:
                    st.warning("⚠️ 站点超过 25 个，谷歌无法自动优化全部顺序。已为您优化前 25 个。")
                    test_locations = valid_locations[:25]
                else:
                    test_locations = valid_locations

                optimize_res = gmaps.directions(
                    origin=test_locations[0]['latlng'],
                    destination=test_locations[-1]['latlng'],
                    waypoints=[l['latlng'] for l in test_locations[1:-1]],
                    optimize_waypoints=True,
                    mode="driving"
                )

                if optimize_res:
                    route = optimize_res[0]
                    order = route['waypoint_order']
                    
                    # 重新排序列表
                    optimized_order = [test_locations[0]]
                    for i in order:
                        optimized_order.append(test_locations[i+1])
                    optimized_order.append(test_locations[-1])

                    # --- 地图展示 ---
                    m = folium.Map(location=optimized_order[0]['latlng'], zoom_start=14)
                    
                    # 绘制真实路径
                    path = googlemaps.convert.decode_polyline(route['overview_polyline']['points'])
                    folium.PolyLine([(p['lat'], p['lng']) for p in path], color="blue", weight=5).add_to(m)

                    # 标记点
                    for i, item in enumerate(optimized_order, 1):
                        folium.Marker(
                            location=item['latlng'],
                            popup=item['original'],
                            icon=folium.DivIcon(html=f"""<div style="background-color:blue; color:white; border-radius:50%; width:25px; height:25px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white;">{i}</div>""")
                        ).add_to(m)

                    folium_static(m)
                    
                    # 显示清单
                    st.success("✅ 优化完成！点击下方按钮可直接跳转手机导航。")
                    for i, item in enumerate(optimized_order, 1):
                        st.write(f"{i}. {item['original']}")

            except Exception as e:
                st.error(f"规划失败：{e}")

get_clean_order()
