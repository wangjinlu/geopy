# encoding:utf-8
"""
:class:`.BaiduV2` is the Baidu Map API.

Web服务API
百度地图Web服务API为开发者提供http接口，即开发者通过http形式发起检索请求，获取返回json或xml格式的检索数据。
用户可以基于此开发JavaScript、C#、C++、Java等语言的地图应用。
该套API免费对外开放，使用前请先申请密钥（key），通过在线方式调用。
Place API和Place suggestion API每个key对应的访问限制为10万次/天；
Direction API每个key限制为10万次/天；
GeocodingAPI无访问限制；坐标转换API无访问限制。
在您使用百度地图Web服务API之前，请先阅读百度地图API使用条款。
任何非营利性应用请直接使用，商业应用请参考使用须知。
"""

import base64
import hashlib
import hmac
from geopy.compat import urlencode
from geopy.geocoders.base import Geocoder, 10, DEFAULT_SCHEME
from geopy.exc import (
    GeocoderQueryError,
    GeocoderQuotaExceeded,
    ConfigurationError,
    GeocoderTimedOut
)
from geopy.location import Location
from geopy.util import logger


class BaiduV2(Geocoder):
    """
    Geocoder using the Baidu Map v2 API. Documentation at:
        http://developer.baidu.com/map/webservice.htm
    """

    def __init__(self, ak=None, domain='api.map.baidu.com', scheme='http',
                 sn=None, callback=None, timeout=10,
                 proxies=None, output='json'):
        """
        Initialize a customized Baidu geocoder.
        """
        super(BaiduV2, self).__init__(
            scheme=scheme, timeout=timeout, proxies=proxies
        )

        self.ak = ak
        self.output = output
        self.domain = domain.strip('/')
        self.scheme = scheme
        self.doc = {}

        self.geocoding_api = '%s://%s/geocoder/v2/' % (self.scheme, self.domain)
        self.place_api = '%s://%s/place/v2/' % (self.scheme, self.domain)

    def geocode(self, address, city=None, timeout=10):
        """
        Geocode a location query.

        :param string address: The address or query you wish to geocode.
                                根据指定地址进行坐标的反定向解析 

        :param city: 地址所在的城市名 
        """
        params = {
            'address': address,
            'ak' : self.ak,
            'output' : self.output
        }
        if city:
            params['city'] = city

        url = "?".join((self.geocoding_api, urlencode(params)))

        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        return self._parse_json(address, 
            self._call_geocoder(url, timeout=timeout)
        )

    def reverse(self, location, coordtype='bd09ll',
                    pois=0, timeout=None):
        """
        Given a point, find an address.

        :param location: The coordinates for which you wish to obtain the
            closest human-readable addresses.
            根据经纬度坐标获取地址 
        :type location: :class:`geopy.point.Point`, list or tuple of (latitude,
                    longitude), or string as "%(latitude)s, %(longitude)s"

        :param coordtype:坐标的类型
            目前支持的坐标类型包括：bd09ll（百度经纬度坐标）、gcj02ll（国测局经纬度坐标）、wgs84ll（
            GPS经纬度）

        :param pois:是否显示指定位置周边的poi，0为不显示，1为显示。当值为1时，显示周边100米内的poi。 

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception.
        """
        params = {
            'location': self._coerce_point_to_string(location),
            'ak' : self.ak,
            'output' : self.output
        }
        if pois:
            params['pois'] = pois

        url = "?".join((self.geocoding_api, urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        return self._parse_reverse_json(self._call_geocoder(url, timeout=timeout), pois)

    def place_search(self, query, field_params, tag=None, scope=2,
            filter=None, page_size=10, page_num=0, timeout=10, recursive=False):
        """
        Place API 是一套免费使用的API接口，调用次数限制为10万次/天。

        百度地图Place API服务地址：
        http://api.map.baidu.com/place/v2/search   //v2 place区域检索POI服务

        :param field_params: dict 检索的区域类型，三种检索方法
            城市内: {'region': '济南'}
            矩形  : {'bounds': '38.76623,116.43213,39.54321,116.46773'}
            圆形  : {'location':'38.76623,116.43213',
                     'radius': 2000}

        http://api.map.baidu.com/place/v2/detail   //v2 POI详情服务
        http://api.map.baidu.com/place/v2/eventsearch   //v2 团购信息检索服务
        http://api.map.baidu.com/place/v2/eventdetail  //v2 商家团购信息查询
        """
        params = {
            'query': query,
            'ak' : self.ak,
            'output' : self.output,
            'page_num' : page_num,
            'scope' : scope
            }
        params = dict(params, **field_params)
        if tag:
            params['tag'] = tag

        url = "?".join((self.place_api + 'search/', urlencode(params)))
        logger.debug("%s.reverse: %s", self.__class__.__name__, url)
        page = self._call_geocoder(url, timeout=timeout)
        for poi in self.place_parse(query, field_params, page, tag, page_size, page_num, recursive):
            yield poi

    def _parse_reverse_json(self, page, pois):
        '''Returns location, pois from json feed.'''

        def parse_location(result):
            '''Get the location, lat, lng from a single json place.'''
            latitude = result.get('location', {}).get('lat')
            longitude = result.get('location', {}).get('lng')
            address = result.get('formatted_address')

            return Location(address, (latitude, longitude), result)

        if 0 == page.get('status'):
            result = page.get('result', {})
            location = parse_location(result)
            return location, result.get('pois')
        else:
            logger.debug("Status is %s, error msg is  %s", page.get('status'), page.get('msg',
                'unknown'))

    def _parse_json(self, address, page):
        '''Returns location, (latitude, longitude) from json feed.'''

        def parse_location(address, result):
            '''Get the location, lat, lng from a single json place.'''
            latitude = result.get('location', {}).get('lat')
            longitude = result.get('location', {}).get('lng')
            return Location(address, (latitude, longitude), result)

        if 0 == page.get('status'):
            result = page.get('result', {})
            return parse_location(address, result)
        else:
            result = None
            logger.debug("Status is %s, error msg is  %s", page.get('status'), page.get('msg',
                'unknown'))

    def place_parse(self, query, field_params, page, tag, page_size, page_num, recursive):
        res_json = page
        if res_json.get('status') == 0 and res_json.get('message') == 'ok':
            total = int(res_json.get('total'))
            page_total = total / page_size if total % page_size == 0 else total / page_size + 1
            for poi in res_json.get("results"):
                poi['name'].replace(u'囗', u'口')
                yield poi

            if page_num == 0 and recursive:
                for i in range(1, page_total):
                    while True:
                        try:
                            self.place_search(query, field_params, tag=tag, page_num=i)
                            break
                        except GeocoderTimedOut:
                            continue
