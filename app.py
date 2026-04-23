import streamlit as st
import googlemaps
import folium
from streamlit_folium import folium_static

# 设置页面
st.set_page_config(page_title="派送大师 Pro", layout="wide")
st.title("🚚 我的私人配送助手 Pro")

# 从 Streamlit Secrets 获取 API Key (安全做法)
# 请在 Streamlit 控制台的 Settings -> Secrets 里添加：MAPS_API_KEY = "你的KEY"
try:
    API_KEY = st.secrets["MAPS_API_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("请先在 Secrets 中配置 MAPS_API_KEY")
    st.stop()

# 地址输入
raw_input = st.text_area("粘贴所有地址（每行一个）：", height=200)

if raw_input:
    address_list = [line.strip() for line in raw_input.split('\n') if line.strip()]
    
    if st.button("开始规划并生成地图"):
        st.subheader(f"今日待送：{len(address_list)} 个站点")
        
        # 1. 地理编码：将地址转为坐标
        locations = []
        for addr in address_list:
            res = gmaps.geocode(addr)
            if res:
                loc = res[0]['geometry']['location']
                locations.append({"address": addr, "lat": loc['lat'], "lng": loc['lng']})
        
        if locations:
            # 2. 创建地图（以第一个点为中心）
            m = folium.Map(location=[locations[0]['lat'], locations[0]['lng']], zoom_start=13)
            
            # 3. 在地图上标出带数字的圆圈
            for i, loc in enumerate(locations, 1):
                folium.Marker(
                    location=[loc['lat'], loc['lng']],
                    popup=loc['address'],
                    icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; background-color: blue; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white;">{i}</div>""")
                ).add_to(m)
            
            # 4. 显示地图
            folium_static(m)
            
            # 5. 显示清单
            st.write("### 派送顺序清单")
            for i, loc in enumerate(locations, 1):
                st.write(f"{i}. {loc['address']}")
