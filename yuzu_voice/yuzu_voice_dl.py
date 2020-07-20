import datetime
import requests
import time
import re
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup


# def read_destination_dir(config_file):
#    with open(config_file, 'r') as reader:
#        print(reader.readline())


def download_file(url, fname):
    # Streaming, so we can iterate over the response.
    req = requests.get(url, stream=True)
    # Total size in bytes.
    total_size = int(req.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    with open(fname, 'wb') as f:
        for data in req.iter_content(block_size):
            t.update(len(data))
            f.write(data)
    t.close()
    if total_size != 0 and t.n != total_size:
        print("ERROR, something went wrong")


def main():
    mp3_regex = r"\/\/[a-zA-Z0-9\/\.-]*park-s3.gsj.mobi[a-zA-Z0-9\/\.-]*\.mp3"
    title_regex = r"新谷ゆづみのひとりゴト。 Vol.[0-9]+"

    # Show Page
    show_page = "https://park.gsj.mobi/program/show/46073"
    # JFN PARK shows list page
    # show_page "https://park.gsj.mobi/?category_id=JF"

    show_title = "新谷ゆづみのひとりゴト。"
    courtesy_delay = 5

    res = requests.get(show_page)
    soup = BeautifulSoup(res.text, 'html.parser')

    # read_destination_dir("doesnot.txt")

    show_list = []
    # make a list of links to show from main page with title show_title
    for tag in soup.find_all('p', class_='timeline_programtitle'):
        if tag.text == show_title:
            parent_tag = tag.findParent('a').attrs['href']
            if 'voice' in parent_tag:
                show_list.append(parent_tag)

    # follow the links and download the shows.
    for show in show_list:
        time.sleep(courtesy_delay)
        r = requests.get(show)
        show_soup = BeautifulSoup(r.text, 'html.parser')

        # Set up the show title
        title_tag = show_soup.find('div', class_='voice_txt')
        # print(title_tag)
        show_title = 'DUMMY'
        show_title_matches = re.search(title_regex, title_tag.text, re.IGNORECASE)
        if show_title_matches:
            show_title = show_title_matches.group()
        else:
            # regular show title was not found then this must me a CM
            cm_tag = show_soup.find('h1')
            show_title = cm_tag.text

        # Set up the show date
        date_tag = show_soup.find('div', class_='voice_date')
        date_list = date_tag.text.strip().split(r'/')
        show_date = datetime.date(int(date_list[0]), int(date_list[1]), int(date_list[2]))
        show_date_string = show_date.strftime("%Y%m%d")

        # Find the picture link
        picture_link = title_tag.findChild('img').attrs['src']

        # Find the mp3 link
        mp3_tag = show_soup.find(text=re.compile("mp3: "))
        search_matches = re.search(mp3_regex, mp3_tag, re.MULTILINE)
        mp3_link = search_matches.group()

        # Check if the files exist if they do not then download.
        mp3_filename = "".join([show_date_string, '_', show_title, r'.mp3'])
        if not Path(mp3_filename).is_file():
            download_file('http:' + mp3_link, mp3_filename)
            print(f"{mp3_filename} downloaded")
        else:
            print(f"{mp3_filename} already exists skipping.")

        picture_filename = "".join([show_date_string, '_', show_title, r'.jpg'])
        if not Path(picture_filename).is_file():
            download_file(picture_link, picture_filename)
            print(f"{picture_filename} downloaded.")
        else:
            print(f"{picture_filename} already exists skipping.")


if __name__ == '__main__':
    main()
