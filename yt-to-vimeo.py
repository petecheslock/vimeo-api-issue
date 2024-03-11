
import re
import pytube
import os
import vimeo
import logging
import requests
import csv
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def write_url_mapping(source_url, destination_url, path):
    file_path = os.path.join(path, 'url_mapping.csv')
    try:
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([source_url, destination_url])
        logger.info(f'Successfully wrote mapping: {source_url} to {destination_url} in {file_path}')
    except Exception as e:
        logger.error(f'Error writing to file {file_path}: {e}')

def download_thumbnail(youtube, path):
    video_id = youtube.video_id
    thumbnail_url = f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg'
    response = requests.get(thumbnail_url)
    if response.status_code != 200:
        thumbnail_url = youtube.thumbnail_url
        response = requests.get(thumbnail_url)
    file_path = os.path.join(path, f"{youtube.title.replace('/', '-')}_thumbnail.jpg")
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path

def upload_thumbnail(client, video_uri, thumbnail_path):
    with open(thumbnail_path, 'rb') as file:
        client.put(f'{video_uri}/pictures', data=file, params={'active': 'true'})

def extract_urls(file_name):
    with open(file_name, 'r') as file:
        data = file.read()
        url_pattern = re.compile(r'https://www.youtube.com/embed/[a-zA-Z0-9_-]{11}')
        urls = re.findall(url_pattern, data)
        return urls

def upload_to_vimeo(client, video_path, video_title, video_description, thumbnail_path):
    data = {
        'name': video_title,
        'description': video_description,
        'privacy': {
            'view': 'anybody',
            'comments': 'nobody'
        }
    }

    logger.info(f'Uploading video: {video_path} with data: {json.dumps(data)}')
    uri = client.upload(video_path, data=data)

    logger.info(f'Successfully uploaded {video_title} to {uri}')

    video_response = client.get(uri + '?fields=link')
    video_link = video_response.json().get('link')

    logger.info(f'Request made to {uri}?fields=link')
    logger.info(f'Response received: {video_response.json()}')
    if 'Request-Hash' in video_response.headers:
        logger.info(f'Request-Hash: {video_response.headers["Request-Hash"]}')

    if not os.path.isfile(thumbnail_path):
        logger.error(f'Thumbnail file does not exist: {thumbnail_path}')
        return video_link

    try:
        with open(thumbnail_path, 'rb') as file:
            logger.info(f'Uploading thumbnail: {thumbnail_path}')
            response = client.post(f'{uri}/pictures', data=file, params={'active': 'true'})
            if response.status_code != 201:
                logger.error(f'Error uploading thumbnail. Status code: {response.status_code}, Response: {response.text}')
            else:
                logger.info(f'Successfully uploaded thumbnail for {video_title}')
                logger.info(f'Request made to {uri}/pictures with data: {file}')
                logger.info(f'Response received: {response.json()}')
                if 'Request-Hash' in response.headers:
                    logger.info(f'Request-Hash: {response.headers["Request-Hash"]}')
    except Exception as e:
        logger.error(f'Error uploading thumbnail: {e}')

    return video_link

def download_videos(urls, path):
    for url in urls:
        try:
            youtube = pytube.YouTube(url)
            video = youtube.streams.get_highest_resolution()
            video_path = video.download(path)
            safe_title = youtube.title.replace("/", "-")
            print(f'Downloaded video: {safe_title}')
            thumbnail_path = download_thumbnail(youtube, path)
            write_video_info(safe_title, youtube.description, path)
            client = vimeo.VimeoClient(
                token=os.environ['VIMEO_ACCESS_TOKEN'],
                key=os.environ['VIMEO_CLIENT_ID'],
                secret=os.environ['VIMEO_CLIENT_SECRET']
            )
            vimeo_url = upload_to_vimeo(client, video_path, safe_title, youtube.description, thumbnail_path)
            write_url_mapping(url, vimeo_url, path)
        except Exception as e:
            print(f'Error downloading video: {url}. Error: {e}')
            logger.exception(f'Error downloading video: {url}. Error: {e}')

def write_video_info(title, description, path):
    safe_file_name = f"{title}.txt".replace("/", "-")
    file_path = os.path.join(path, safe_file_name)
    with open(file_path, 'w') as file:
        file.write(f"Title: {title}\nDescription: {description}")

def main():
    file_name = 'youtube-embed.txt'
    output_path = '/Users/petecheslock/Desktop/youtube'
    urls = extract_urls(file_name)
    download_videos(urls, output_path)

if __name__ == '__main__':
    main()
