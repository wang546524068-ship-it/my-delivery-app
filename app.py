<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Saskatoon-Warman 配送助手</title>
    <style>
        /* 这里的代码是控制网页长什么样的 */
        body { margin: 0; display: flex; height: 100vh; font-family: "Microsoft YaHei", sans-serif; }
        #sidebar { width: 400px; background: #f4f4f4; padding: 20px; box-shadow: 2px 0 5px rgba(0,0,0,0.1); z-index: 10; display: flex; flex-direction: column; }
        #map { flex: 1; } /* 地图占据剩下的屏幕 */
        textarea { width: 100%; height: 200px; border: 1px solid #ccc; border-radius: 4px; padding: 10px; font-size: 14px; }
        .btn-group { margin-top: 15px; }
        button { width: 100%; padding: 12px; margin-bottom: 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; }
        .btn-blue { background: #1a73e8; color: white; }
        .btn-green { background: #34a853; color: white; }
        #status { margin-top: 10px; color: #d93025; font-size: 14px; }
    </style>
</head>
<body>

<div id="sidebar">
    <h2>配送路线优化</h2>
    <p>1. 输入地址 (每行一个):</p>
    <textarea id="addrInput" placeholder="例如:
701 Centennial Blvd, Warman
Midtown Plaza, Saskatoon
810 Circle Dr, Saskatoon"></textarea>
    
    <div class="btn-group">
        <button class="btn-blue" onclick="startGeocoding()">第一步：检查地址准确度</button>
        <button class="btn-green" onclick="calculateRoute()">第二步：规划最优路线</button>
    </div>
    
    <div id="status">等待输入...</div>
    <div id="routeInfo" style="margin-top:20px; font-size: 13px; color: #555;"></div>
</div>

<div id="map"></div>

<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDgv1VsFfJ0tWfyzewmvEsPIlzHa67y17w&libraries=places"></script>

<script>
    let map, directionsService, directionsRenderer;
    let markers = [];

    // 初始化地图，默认中心设在 Saskatoon
    function initMap() {
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 11,
            center: { lat: 52.1332, lng: -106.6700 },
            mapTypeControl: false
        });
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            map: map,
            panel: document.getElementById('routeInfo')
        });
    }
    window.onload = initMap;

    // 第一步：地址转坐标
    async function startGeocoding() {
        const input = document.getElementById('addrInput').value;
        const addresses = input.split('\n').filter(a => a.trim() !== '');
        const status = document.getElementById('status');
        
        if (addresses.length === 0) {
            status.innerText = "❌ 请先输入地址";
            return;
        }

        status.innerText = "⏳ 正在校准定位...";
        clearMap();

        const geocoder = new google.maps.Geocoder();
        for (let addr of addresses) {
            // 限制在加拿大萨省范围内搜索，确保定位准确
            geocoder.geocode({ 
                address: addr, 
                componentRestrictions: { country: 'CA', administrativeArea: 'SK' } 
            }, (results, status) => {
                if (status === "OK") {
                    const marker = new google.maps.Marker({
                        map: map,
                        position: results[0].geometry.location,
                        title: addr
                    });
                    markers.push(marker);
                    map.panTo(results[0].geometry.location);
                }
            });
        }
        status.innerText = `✅ 已成功定位 ${addresses.length} 个地址`;
    }

    // 第二步：路径优化
    function calculateRoute() {
        if (markers.length < 2) {
            alert("请至少定位两个点！");
            return;
        }

        const status = document.getElementById('status');
        status.innerText = "⏳ 正在计算最合理路线(避开拥堵)...";

        // 提取起点、终点和中间点
        const origin = markers[0].getPosition();
        const destination = markers[markers.length - 1].getPosition();
        const waypoints = [];

        // 注意：Google 网页基础版单次请求最多支持 25 个点
        for (let i = 1; i < markers.length - 1; i++) {
            waypoints.push({ location: markers[i].getPosition(), stopover: true });
        }

        const request = {
            origin: origin,
            destination: destination,
            waypoints: waypoints,
            optimizeWaypoints: true, // 这是核心：自动排序，不走回头路
            travelMode: google.maps.TravelMode.DRIVING,
            drivingOptions: {
                departureTime: new Date(Date.now()), // 考虑实时路况
                trafficModel: 'bestguess'
            }
        };

        directionsService.route(request, (result, status) => {
            if (status === 'OK') {
                directionsRenderer.setDirections(result);
                document.getElementById('status').innerText = "⭐ 路线规划完成！已按最优顺序排列。";
            } else {
                document.getElementById('status').innerText = "❌ 规划失败: " + status;
            }
        });
    }

    function clearMap() {
        markers.forEach(m => m.setMap(null));
        markers = [];
        directionsRenderer.setDirections({routes: []});
    }
</script>

</body>
</html>
