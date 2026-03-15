# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

home_cache = {}
CACHE_TTL = 1800

@app.get("/api/search")
def search_music(query: str):
    try:
        from ytmusicapi import YTMusic
        ytmusic = YTMusic()
        search_results = ytmusic.search(query, filter="songs", limit=12)
        return {"status": "success", "data": format_results(search_results)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stream")
def get_stream_url(videoId: str):
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={videoId}",
                download=False
            )
            url = info.get('url')
            if not url and info.get('formats'):
                # Cari format audio terbaik
                audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if audio_formats:
                    url = audio_formats[-1].get('url')
                else:
                    url = info['formats'][-1].get('url')
            if not url:
                return {"status": "error", "message": "Stream URL not found"}
            return {"status": "success", "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/home")
def get_home_data():
    current_time = time.time()
    if "data" in home_cache and (current_time - home_cache.get("timestamp", 0) < CACHE_TTL):
        return {"status": "success", "data": home_cache["data"]}
    try:
        from ytmusicapi import YTMusic
        ytmusic = YTMusic()
        data = {
            "recent":  format_results(ytmusic.search('lagu indonesia hits terbaru', filter="songs", limit=4)),
            "anyar":   format_results(ytmusic.search('lagu pop indonesia rilis terbaru anyar', filter="songs", limit=8)),
            "gembira": format_results(ytmusic.search('lagu ceria gembira semangat', filter="songs", limit=8)),
            "charts":  format_results(ytmusic.search('top 50 indonesia playlist update', filter="songs", limit=8)),
            "galau":   format_results(ytmusic.search('lagu galau sedih indonesia terpopuler', filter="songs", limit=8)),
            "baru":    format_results(ytmusic.search('lagu viral terbaru 2026', filter="songs", limit=8)),
            "tiktok":  format_results(ytmusic.search('lagu fyp tiktok viral jedag jedug', filter="songs", limit=8)),
            "artists": format_results(ytmusic.search('penyanyi pop indonesia paling hits', filter="songs", limit=8))
        }
        home_cache["data"] = data
        home_cache["timestamp"] = current_time
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/lyrics")
def get_lyrics(video_id: str):
    try:
        from ytmusicapi import YTMusic
        ytmusic = YTMusic()
        watch = ytmusic.get_watch_playlist(video_id)
        lyrics_id = watch.get("lyrics")
        if not lyrics_id:
            return {"status": "error", "message": "No lyrics found"}
        lyrics = ytmusic.get_lyrics(lyrics_id)
        text = lyrics.get("lyrics", "")
        if not text:
            return {"status": "error", "message": "Empty lyrics"}
        return {"status": "success", "data": {"lyrics": text}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def root():
    return {"status": "ok", "message": "Auspoty Music API"}

def format_results(search_results):
    cleaned_results = []
    for item in search_results:
        if 'videoId' in item:
            cleaned_results.append({
                "videoId": item['videoId'],
                "title": item.get('title', 'Unknown Title'),
                "artist": item.get('artists', [{'name': 'Unknown Artist'}])[0]['name'] if item.get('artists') else 'Unknown Artist',
                "thumbnail": item['thumbnails'][-1]['url'] if item.get('thumbnails') else ''
            })
    return cleaned_results

handler = Mangum(app)
