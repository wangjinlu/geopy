# encoding=utf-8
from geopy.geocoders import BaiduV2
geolocator = BaiduV2('4Yg3dtCIaTO7ZORFbiGKW49d')
#location = geolocator.geocode(u'新疆维吾尔自治区乌鲁木齐市达坂城区阿克苏乡牧业一队')
#print location.latitude, location.longitude
#print geolocator.reverse(location.point, pois=1)
#for poi in geolocator.place_search(query=u'购物', field_params={'bounds':'38.76623,116.43213,39.54321,116.46773'}, scope=2):
#    print poi
location = geolocator.geocode(u'新疆维吾尔自治区')
print location.latitude, location.longitude
