import os
import json
import time

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from urllib.request import urlopen

dir_name = "img"

def imgList(foldername, fulldir = True, suffix=".jpg"):
    """Returns list of jpg files in directory"""
    file_list_tmp = os.listdir(foldername)
    file_list = []
    if fulldir:
        for item in file_list_tmp:
            if item.endswith(suffix):
                file_list.append(os.path.join(foldername, item))
    else:
        for item in file_list_tmp:
            if item.endswith(suffix):
                file_list.append(item)
    return file_list

def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None

def _convert_to_degrees(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

    return lat, lon

def delay():
    time.sleep(.1)

def getplace(lat, lon):
    """Determines city, country from lat, long"""
    url = "http://maps.googleapis.com/maps/api/geocode/json?"
    url += "latlng=%s,%s&sensor=false" % (lat, lon)
    # print (url)
    v = urlopen(url).read()
    v = v.decode("utf-8")
    j = json.loads(v)

    delay()

    # check status code is OK, not OVER_QUERY_LIMIT
    result_status = j['status']
    # print (result_status)

    if result_status == 'OK':
        components = j['results'][0]['address_components']
        route = area = city = country = None
        for c in components:
            # if "route" in c['types']:
            #     route = c['long_name']
            if "locality" in c['types']:
                route = c['long_name']
            # if "locality" in c['types']:
            #     city = c['long_name']
            if "administrative_area_level_1" in c['types']:
                city = c['long_name']
            if "country" in c['types']:
                country = c['long_name']
        return route, city, country

def writeHTML():
        f.write("<li>" + "\n")
        f.write("    <img src ='" + dir_name + "/" + img_filename + "'>" + "\n")
        if route:
            f.write("    <p>" + route + ", " + city + ", " + country + "</p>" + "\n")
        else:
            f.write("    <p>" + city + ", " + country + "</p>" + "\n")
        f.write("</li>" + "\n")


####################
# Application ######
####################

if __name__ == "__main__":

    f = open(dir_name+".html", "w")
    doc = open(dir_name+".txt", "w")

    for img_filename in imgList("./" + dir_name):
        fp = open(img_filename, "rb")
        im = Image.open(fp)
        exif_data = get_exif_data(im)
        img_filename = img_filename.lstrip("./").replace(dir_name+"/", "")
        lat = get_lat_lon(exif_data)[0]
        lon = get_lat_lon(exif_data)[1]
        if lat and lon:
            route = (getplace((lat),(lon)))[0]
            city = (getplace((lat),(lon)))[1]
            country = (getplace((lat),(lon)))[2]
            if route:
                print (img_filename + ", Route: " + route + ", City: "+ city + ", Country: " + country)
                doc.write("Image: " + img_filename + ", Route: " + route + ", City: "+ city + ", Country: " + country + "\n")

            writeHTML()

    f.close()
    doc.close()
