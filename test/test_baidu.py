# encoding=utf-8
from geopy.geocoders import BaiduV2
geolocator = BaiduV2('4Yg3dtCIaTO7ZORFbiGKW49d')
location = geolocator.geocode(u'江苏省南京市栖霞区栖霞街道红梅村村委会')
print location.latitude, location.longitude
print geolocator.reverse(location.point, pois=1)
