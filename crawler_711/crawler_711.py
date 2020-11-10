import requests as rq
import pandas as pd
import random
import time
from lxml import etree
from io import BytesIO
from pprint import pprint

class crawler_711:
    def __init__(self, cli=False):
        self.request_url = r'https://emap.pcsc.com.tw/EMapSDK.aspx'
        self._city_info = []
        self._town_info = ''
        self._rd_info = ''
        self._set_city_name()
        if cli: self.cli()

    def cli(self):
        self._set_town_name()
        self._set_rd_name()
        self._show_stores()
        
    def _set_city_name(self):
        def contains(key, df):
            ids = df['cityid']
            names = df['city']
            for id,name in zip(ids, names):
                if id == key: 
                    return [id, name]
            return None

        df = self._city_df()
        pprint(df.set_index('cityid'))
        input_id = input('\ninput cityid: ')
        valid = contains( input_id, df)
        while not valid:
            input_id = input('invalid cityid request...\ninput cityid: ')
            valid = contains( input_id, df)
        self._city_info = valid
    
    def _set_town_name(self):
        df = self._town_df()
        df_range = len(df['town'])
        pprint(df.set_index('townid'))
        input_id = int(input('\ninput townid: '))
        while input_id < 0 or input_id >= df_range:
            input_id = int(input('invalid townid request...\ninput townid: '))
        town_name = df['town'][input_id]
        pprint(town_name)
        self._town_info = town_name

    def _set_rd_name(self):
        df = self._rd_df()
        df_range = len(df['road'])
        pprint(df.set_index('roadid'))
        input_id = int(input('\ninput roadid: '))
        while input_id < 0 or input_id >= df_range:
            input_id = int(input('invalid roadid request...\ninput roadid: '))
        road_name = df['road'][input_id]
        pprint(road_name)
        self._rd_info = road_name

    def _show_stores(self):
        stores = self.get_711_stores()
        pprint(stores)
        


    def _city_df(self):
        df = pd.DataFrame()
        df['cityid'] = [
            '01', '02', '03', '04', '05', '06', '07', '08', '10', '11', 
            '12', '13', '14', '15', '17', '19', '20', '21', '22', 
            '23', '24', '25'
        ]
        df['city'] = [
            "台北市", "基隆市", "新北市", "桃園市", "新竹市", "新竹縣", "苗栗縣",
            "台中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "台南市",
            "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "台東縣", "澎湖縣", "連江縣",
            "金門縣"
        ]
        return df

    def _town_df(self):
        towns = self.get_towns()
        nums_of_towns = len(towns)
        index = [ int(e) for e in range(0, nums_of_towns)]
        df = pd.DataFrame()
        df['townid'] = index
        df['town'] = towns
        return df

    def _rd_df(self):
        rd_names = self.get_rd_names(self._town_info)
        nums_of_rd = len(rd_names)
        index = [ int(e) for e in range(0, nums_of_rd) ]
        df = pd.DataFrame()
        df['roadid'] = index
        df['road'] = rd_names
        return df


    def get_towns(self):
        data = {
            "commandid": "GetTown",
            "cityid": self._city_info[0] 
        }
        response = rq.post(self.request_url, data=data)
        file = BytesIO(response.content)
        tree = etree.parse(file)
        town_names = [e.text for e in tree.xpath('//TownName')]
        return town_names # 回傳為 list , 資料為 選定轄市中每一區的名字
    
    def get_rd_names(self, town_name=None):
        town_name = self._town_info if town_name is None else town_name
        data = {
            "commandid": "SearchRoad",
            "city": self._city_info[1],
            "town": town_name
        }
        response = rq.post(self.request_url, data=data)
        f = BytesIO(response.content)
        tree = etree.parse(f)
        rds = [e.text for e in tree.xpath("//rd_name_1")]
        secs = [e.text if e.text != None else "" for e in tree.xpath("//section_1") ]
        rd_name = [rd + sec for rd, sec in zip(rds, secs) ]
        return rd_name
        
    # 手動輸入搜尋
    def check_input_info(self, input_town, input_rd = None):
        towns = self.get_towns()
        town_result = [r for r in filter(lambda t : input_town in t, towns)]
        list_of_711 = []

        for town in town_result:
            rds = [
                r for r in filter(lambda rd : input_rd in rd, rds)
            ] if input_rd is None else self.get_rd_names(town)
            if input_rd is not None: # 再過濾一次
                rds= [r for r in filter(lambda rd : input_rd in rd, rds)]
            if len(rds) != 0:
                list_of_711.append({
                    "TownName": town,
                    "RoadName": rds
                })
        return list_of_711
    
    def get_711_stores(self, input_town_name=None, input_rd_name=None):
        if input_town_name is None and self._town_info:
            input_town_name = self._town_info 
        if input_rd_name is None and self._rd_info:
            input_rd_name = self._rd_info

        search_info = self.check_input_info(input_town_name, input_rd_name)
        
        # pprint(search_info) #debugging

        store_list = []
        for info in search_info:
            for rd in info["RoadName"]:
                data = {
                    "commandid": "SearchStore",
                    "city": self._city_info[1],
                    "town": info["TownName"],
                    "roadname": rd
                }
                response = rq.post(self.request_url, data=data)
                file = BytesIO(response.content)
                tree = etree.parse(file)
                poi_ids = [e.text.strip() for e in tree.xpath("//POIID")]
                poi_names = [e.text for e in tree.xpath("//POIName")]
                lags = [float(e.text)/1000000 for e in tree.xpath("//X")]
                lons = [float(e.text)/1000000 for e in tree.xpath("//Y")]
                adds = [e.text for e in tree.xpath("//Address")]
                
                for poi_id, poi_name, lag, lon, add in zip(poi_ids, poi_names, lags, lons, adds):
                    store_info = {
                        "POIID": poi_id,
                        "POIName":poi_name,
                        "Lagtitude": lag,
                        "Lontitude": lon,
                        "Address": add
                    }
                    store_list.append(store_info)
        return store_list

