import requests
import geojson
import pandas as pd

# ===================== 配置区（修改这里） =====================
KEY = "TMGBZ-SZKLU-YCEV7-GCP5N-AABVV-5EBVP"
city = "南宁市"
district = "青秀区"
# 关键词：大类+南宁特色细分餐饮，兼顾展示与分类可视化
keywords_list = ["餐饮", "螺蛳粉", "奶茶", "火锅", "烧烤", "小吃快餐", "咖啡甜品"]
page_size = 20  # 腾讯单页最大20条
# ==========================================================

# 存储所有点位，用 (经度,纬度,店名) 做去重标识
all_features = []
unique_sign = set()

for keyword in keywords_list:
    print(f"\n===== 正在抓取：{keyword} =====")
    page_index = 1
    while True:
        # 接口请求参数
        url = "https://apis.map.qq.com/ws/place/v1/search"
        params = {
            "keyword": keyword,
            "region": f"{city}{district}",
            "page_size": page_size,
            "page_index": page_index,
            "key": KEY
        }
        resp = requests.get(url, params=params)
        res_data = resp.json()

        # 请求失败/无数据，跳出当前关键词循环
        if res_data["status"] != 0 or len(res_data.get("data", [])) == 0:
            print(f"【{keyword}】无更多数据或接口报错，结束抓取")
            break

        # 遍历当前页所有POI
        for poi in res_data["data"]:
            lng = poi["location"]["lng"]
            lat = poi["location"]["lat"]
            name = poi["title"]
            # 去重标记：经纬度+店名
            sign = (round(lng, 6), round(lat, 6), name)
            if sign in unique_sign:
                continue  # 重复数据跳过
            unique_sign.add(sign)

            # 构造GeoJSON点要素
            feat = geojson.Feature(
                geometry=geojson.Point((lng, lat)),
                properties={
                    "name": name,
                    "address": poi["address"],
                    "category_all": poi["category"],
                    "search_keyword": keyword,
                    "tel": poi.get("tel", "无")
                }
            )
            all_features.append(feat)

        print(f"【{keyword}】第{page_index}页抓取完成，当前总有效点位：{len(all_features)}")
        page_index += 1

# ---------------------- 导出GeoJSON（WebGIS网页/ArcGIS Online通用） ----------------------
fc = geojson.FeatureCollection(all_features)
with open("青秀区餐饮POI.geojson", "w", encoding="utf-8") as f:
    geojson.dump(fc, f, ensure_ascii=False, indent=2)
print("\n✅ GeoJSON导出完成：青秀区餐饮POI.geojson")

# ---------------------- 导出Excel（方便查看、预处理数据） ----------------------
excel_rows = []
for feat in all_features:
    prop = feat["properties"]
    coord = feat["geometry"]["coordinates"]
    excel_rows.append({
        "经度": coord[0],
        "纬度": coord[1],
        "店名": prop["name"],
        "地址": prop["address"],
        "原始分类": prop["category_all"],
        "检索关键词": prop["search_keyword"],
        "电话": prop["tel"]
    })
df = pd.DataFrame(excel_rows)
df.to_excel("青秀区餐饮POI.xlsx", index=False)
print("✅ Excel表格导出完成：青秀区餐饮POI.xlsx")

print(f"\n===== 全部抓取结束 =====")
print(f"去重后总餐饮点位：{len(all_features)} 条")
print("文件生成：青秀区餐饮POI.geojson / 青秀区餐饮POI.xlsx")