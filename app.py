from flask import Flask, render_template, request, Response
import yt_dlp
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/formats", methods=["POST"])
def formats():
    url = request.form["url"]
    ydl_opts = {"quiet": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Extract formats with useful info
            video_formats = []
            for f in info["formats"]:
                if f.get("vcodec") != "none" or f.get("acodec") != "none":
                    filesize = f.get("filesize") or f.get("filesize_approx")
                    video_formats.append({
                        "format_id": f["format_id"],
                        "resolution": f.get("resolution", "audio-only"),
                        "ext": f.get("ext"),
                        "fps": f.get("fps", ""),
                        "filesize": round(filesize/(1024*1024), 2) if filesize else "Unknown",
                        "acodec": f.get("acodec"),
                        "vcodec": f.get("vcodec"),
                    })

        return render_template(
            "choose_format.html",
            formats=video_formats,
            video_url=url,
            title=info.get("title", "Video"),
            thumbnail=info.get("thumbnail"),
            duration=info.get("duration")
        )
    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    format_id = request.form["format_id"]

    ydl_opts = {"format": format_id, "quiet": True}

    def generate():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info["url"]
                filename = info.get("title", "video") + f".{info.get('ext', 'mp4')}"

            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
        except Exception as e:
            yield f"Error: {str(e)}".encode()

    return Response(
        generate(),
        headers={
            "Content-Disposition": f"attachment; filename=video.mp4",
            "Content-Type": "video/mp4"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

