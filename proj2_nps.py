#################################
##### Name: Qifan Wu
##### Uniqname: qifanw
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import sys


CACHE_FILENAME = 'national_park_cash.json'
CACHE_DICT = {}
API_key = secrets.API_key

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"a")
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(baseurl, params):
    uniq_key = baseurl
    for k in params.keys():
        uniq_key = uniq_key + '_' + k + '_' + str(params[k])
    return uniq_key


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    base_url = "https://www.nps.gov/index.htm"
    if base_url in CACHE_DICT.keys():
        print("Using Cache")
        soup = BeautifulSoup(CACHE_DICT[base_url], 'html.parser')
    else:
        print("Fetching")
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        CACHE_DICT[base_url] = response.text
        save_cache(CACHE_DICT)

    state_dict = {}
    course_listing_parent = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    course_listing_divs = course_listing_parent.find_all('li', recursive=False)
    for course_listing_div in course_listing_divs:
        course_link_tag = course_listing_div.find('a')
        state_path = course_link_tag['href']
        state_name = course_listing_div.text.strip()
        each_state_url = 'https://www.nps.gov' + state_path
        state_name = state_name.lower()
        state_dict[state_name] = each_state_url
    
    return state_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    if site_url in CACHE_DICT.keys():
        print("Using Cache")
        soup = BeautifulSoup(CACHE_DICT[site_url], 'html.parser')
    else:
        print("Fetching")
        response = requests.get(site_url)
        CACHE_DICT[site_url] = response.text
        save_cache(CACHE_DICT)
        soup = BeautifulSoup(response.text, 'html.parser')

    name = soup.find('a', class_='Hero-title').text.strip()
    category = soup.find('span', class_='Hero-designation').text.strip()
    address = soup.find('span', itemprop='addressLocality').text.strip() + ', ' + soup.find('span', itemprop='addressRegion').text.strip()
    zipcode = soup.find('span', class_='postal-code').text.strip()
    phone = soup.find('span', itemprop='telephone').text.strip()
    # return category, my_type, address
    site_instance = NationalSite(category, name, address, zipcode, phone)
    return site_instance

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    instance_list = []
    response = requests.get(state_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # state_name = soup.find('h1', class_='page-title').text
    course_listing_parent = soup.find('ul', id='list_parks')
    course_listing_divs = course_listing_parent.find_all('li', recursive=False)
    for course_listing_div in course_listing_divs:
        site_url_detail = course_listing_div.find('h3').find('a')['href']
        site_url = 'https://www.nps.gov' + site_url_detail + 'index.htm'
        instance_list.append(get_site_instance(site_url))
    return instance_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    baseurl = 'http://www.mapquestapi.com/search/v2/radius'
    # http://www.mapquestapi.com/search/v2/radius?key=Y7lrm3rdhrvTENDAs8WsapamvF5QqP9k&maxMatches=4
    params = {
        "key": API_key,
        "origin": site_object.zipcode,
        "radius": 10,
        "maxMatches": 10,
        "ambiguities": "ignore",
        "outFormat": "json"
    }
    uniq_key = construct_unique_key(baseurl, params)
    if uniq_key in CACHE_DICT.keys():
        print("Using Cache")
        response = CACHE_DICT[uniq_key]
    else:
        print("Fetching")
        response = requests.get(baseurl, params).json()
        CACHE_DICT[uniq_key] = response
        save_cache(CACHE_DICT)

    return response
    # response = requests.get(baseurl, params)
    # return response.text
    # 

def print_nearby_places(site_object):
    '''
    print the nearby places

    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    None
    '''
    nearby_places_list = get_nearby_places(site_object)["searchResults"]
    print("---------------")
    print(f"Places near {site_object.name}")
    print("---------------")
    for nearby_place in nearby_places_list:
        nearby_place = nearby_place['fields']
        name = nearby_place['name']
        address = nearby_place['address']
        city = nearby_place['city']
        category = nearby_place['group_sic_code_name_ext']
        if category == '':
            category = "no category"
        if address == '':
            address = "no address"
        if city == '':
            city = "no city"
        info = f"- {name} ({category}): {address}, {city}"
        print(info)


if __name__ == "__main__":
    # print(build_state_url_dict())
    # print(get_sites_for_state('https://www.nps.gov/state/az/index.htm')[1].info())
    CACHE_DICT = open_cache()
    states_dict = build_state_url_dict()
    while True:
        search_state = input('Enter a State name (e.g., Michigan, michigan) or "exit":  \n')
        if search_state.lower() in states_dict:
            state_url = states_dict[search_state.lower()]
            instance_list = get_sites_for_state(state_url)
            print("-------------------")
            print(f"List of national sites in {search_state}")
            print("-------------------")
            for index, site in enumerate(instance_list[:10]):
                site_info = f"[{index+1}] {site.info()}"
                print(site_info)

            while True:
                enter_num = input('Choose the number for detail search or enter "exit" or "back": \n')
                if enter_num.lower() == 'exit':
                    sys.exit(0)
                elif enter_num.lower() == 'back':
                    break
                try:
                    num = int(enter_num)
                    if 1 <= num <= len(instance_list):
                        # print("-------------------")
                        # print(f"Places near {instance_list[num-1]}")
                        # print("-------------------")
                        print_nearby_places(instance_list[num-1])
                    else:
                        print("[Error] Invalid input")
                except ValueError:
                    print("[Error] Invalid input")
        elif search_state.lower() == 'exit':
            sys.exit(0)
        else:
            print("[Error] Enter proper state name")
    
    # search_state = 'michigan'
    # state_url = states_dict[search_state]
    # instance_list = get_sites_for_state(state_url)
    # # for index, site in enumerate(instance_list):
    # #     site_info = f"[{index+1}] {site.info()}"
    # #     print(site_info)

    # # print(get_nearby_places(instance_list[1]))
    # print_nearby_places(instance_list[1])
