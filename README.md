To recreate the issue:

Using Python `3.11.6`

Create virtual env
```
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

Install requirements
```
pip install -r requirements.txt
```

The relevant data payload on line 53

```
    data = {
        'name': video_title,
        'description': video_description,
        'privacy': {
            'view': 'anybody',
            'comments': 'nobody'
        }
    }

```

Update the `env` file with your API keys.  If storing your keys on 1password update the secret paths and run:

```
op run --env-file="./env" python3 ./yt-to-vimeo.py
```

Otherwise load your envirnment, for example:

```
source env
python3 ./yt-to-vimeo.py
```

Run the script which takes the file from the `youtube-embed.txt` file and copies it to vimeo.  The video should be public but comments disabled. 

