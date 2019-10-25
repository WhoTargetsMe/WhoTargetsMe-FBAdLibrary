from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import requests
import io
import os
import boto3
import json
from botocore.exceptions import NoCredentialsError
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

# DRIVER_PATH = '/usr/local/bin/chromedriver'
# wd = webdriver.Chrome(executable_path=DRIVER_PATH)

def upload_to_aws(img, bucket, f_name, creds):
    s3 = boto3.client('s3', aws_access_key_id=creds['access_key'],\
        aws_secret_access_key=creds['secret_key'],\
        region_name='eu-central-1')
    try:
        in_mem_file = io.BytesIO()
        img.save(in_mem_file, "JPEG")
        in_mem_file.seek(0)
        s3.upload_fileobj(in_mem_file, bucket, f_name)
        print('Uploaded file', f_name)
        return f_name
    except FileNotFoundError:
        print('The file is not found', f_name)
        return False
    except NoCredentialsError:
        print('NoCredentialsError', f_name)
        return False

def persist_image(url:str, post_id:str, page_id:str, creds:dict, i:int):
    # folder_path = '/Users/evgenia/Documents/img_test'
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        f_name = str(page_id) + '_' + str(post_id) + '_' + str(i) + '.jpg'
        # file_path = os.path.join(folder_path, f_name)
        # with open(file_path, 'wb') as f:
        #     image.save(f, "JPEG", quality=95)
        # print(f"SUCCESS - saved {url} - as {file_path}")

        uploaded = upload_to_aws(image, 'fblibclone', f_name, creds)
        return uploaded

    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

# extract json with ad_info out of script text
def get_json(txt):
    for i in range(len(txt)):
        try:
            return json.loads(txt[:i])
        except:
            continue

def get_and_load_images_to_s3(post_id, page_id, creds):
    www_links = set()
    url = 'https://www.facebook.com/ads/archive/render_ad/?id=' + str(post_id) + '&access_token=' + str(creds['long_token'])
    # Get additional info about ad
    r = requests.get(url).text
    ad_info = None
    start = r.find('{"adCard":')
    page_profile_picture_url = None
    if start != -1:
        ad_info = get_json(r[start:])
        t = '"page_profile_picture_url":"'
        s = r.find(t) + len(t)
        e = r[s:].find('",')

        page_profile_picture_url = r[s:s+e]
        if page_profile_picture_url and len(page_profile_picture_url) > 0:
            page_profile_picture_url = page_profile_picture_url.replace('\\', '')

    # Get images links
    driver = webdriver.Chrome()
    driver.get(url)
    sleep(5)

    driver.implicitly_wait(300)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    images = soup.find_all('img')
    videos = soup.find_all('video')
    print('Found in SOUP=', len(images), 'page_id=', page_id, 'post_id=', post_id)

    for img in images:
        src = img['src']
        if src and src.find('facebook.com/security') == -1:
            if src != page_profile_picture_url:
                print('FOUND   src ----', src)
                print('PROFILE src ----', page_profile_picture_url)
                www_links.add(src)

    for vid in videos:
        src = vid['poster']
        if src:
            www_links.add(src)
    i = 0
    aws_links = []
    for src in www_links:
        uploaded = persist_image(src, post_id, page_id, creds, i)
        if uploaded:
            aws_link = 'https://fblibclone.s3.eu-central-1.amazonaws.com/' + uploaded
            aws_links.append(aws_link)
            i += 1
    driver.quit()
    return aws_links, www_links, ad_info
