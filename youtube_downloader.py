import re
import os
import time
import argparse
from yt_dlp import YoutubeDL

def get_absolute_path(download_path, filename):
    return os.path.abspath(os.path.join(download_path, filename))

def convert_webm_audio_to_mp3(input_file_path, output_file_path):
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    # Load the WebM file (treat it as an audio file)
    audio = AudioFileClip(input_file_path)

    # Save the audio as an MP3 file
    audio.write_audiofile(output_file_path)

    # Close the audio object
    audio.close()

def _get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

def download_video(url, download_path, clip_media=None, convert_to_mp3=False, cookies_path=None):
    try:
        ydl_opts = {
            'outtmpl': get_absolute_path(download_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]',
            'cookiefile': cookies_path,
        }
        ffmpeg_path = _get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        if convert_to_mp3:
            ydl_opts['format'] = 'bestaudio[ext=webm]/bestaudio'
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = os.path.join(download_path, ydl.prepare_filename(info_dict))            
        if convert_to_mp3:
            output_file_path = os.path.splitext(video_path)[0] + '.mp3'
            convert_webm_audio_to_mp3(video_path, output_file_path)
            os.remove(video_path)
            
    except Exception as e:
        with open('errors.log', 'a') as error_file:
            error_file.write(f"Error: {e}. Skipping video: {url}\n")
        return
        
    if clip_media:
        from clip_media import clip_mp4
        temp_output_path = get_absolute_path(download_path, "temp_" + os.path.basename(video_path))
        clip_mp4(video_path, temp_output_path, clip_media[0], clip_media[1])
        os.remove(video_path)
        os.rename(temp_output_path, video_path)
        
def download_playlist(url, download_path=None, limit=None, convert_to_mp3=False, cookies_path=None):
    try:
        ydl_opts = {
            'extract_flat': True,
            'outtmpl': get_absolute_path(download_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio/best[ext=mp4]',
            'cookiefile': cookies_path,
        }
        ffmpeg_path = _get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        if convert_to_mp3:
            ydl_opts['format'] = 'bestaudio[ext=webm]/bestaudio'

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        if 'entries' in info_dict:
            video_urls = [entry['url'] for entry in info_dict['entries']]
        else:
            return

        if limit:
            video_urls = video_urls[:limit]

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(video_urls)
            
    except Exception as e:
        with open('errors.log', 'a') as error_file:
            error_file.write(f"Error: {e}\n")
            
    if convert_to_mp3:
        for video_url in video_urls:
            try:
                video_title = info_dict.get('entries')[video_urls.index(video_url)]['title']
                video_path = os.path.join(download_path, f"{video_title}.webm")
                output_file_path = os.path.splitext(video_path)[0] + '.mp3'
                convert_webm_audio_to_mp3(video_path, output_file_path)
                os.remove(video_path)
            except Exception as e1:
                try:
                    # Get the info_dict for the current video
                    with YoutubeDL(ydl_opts) as ydl:
                        video_info = ydl.extract_info(video_url, download=False)

                    # Use prepare_filename to get the exact filename
                    video_path = ydl.prepare_filename(video_info)
                    output_file_path = os.path.splitext(video_path)[0] + '.mp3'
                    convert_webm_audio_to_mp3(video_path, output_file_path)
                    os.remove(video_path)
                except Exception as e2:
                    with open('errors.log', 'a') as error_file:
                        error_file.write(f"Error: {e2}\n")
                
def main():
    parser = argparse.ArgumentParser(description='Download YouTube video or playlist.')
    
    parser.add_argument('url', help='URL of the YouTube video or playlist.')
    parser.add_argument('--cookies', help='Path to the cookies file (optional).', default=None)
    parser.add_argument('-p', '--path', help='Path to the download folder (optional).', default=None)
    parser.add_argument('-l', '--limit', type=int, help='Limit the number of videos to download from a playlist (optional).', default=None)
    parser.add_argument('--clip', action='store_true', help='Clip the downloaded video using the specified start and end times (optional).')
    parser.add_argument("-s", "--start", type=int, default=0, help="Start time (in seconds) to clip from. Default is 0.")
    parser.add_argument("-e", "--end", type=int, default=None, help="End time (in seconds) to clip to. Default is the end of the file.")
    parser.add_argument('--mp3', action='store_true', help='Convert the downloaded video to MP3 format and remove the MP4 file (optional).')

    args = parser.parse_args()

    if "list=" in args.url:
        print("Downloading playlist...")
        if not args.path:
            args.path = '../playlist/'
        download_playlist(args.url, args.path, args.limit, args.mp3, args.cookies)
    else:
        print("Downloading video...")
        clip_media = None
        if not args.path:
            args.path = '.'
        if args.clip:
            clip_media = (args.start, args.end)
        download_video(args.url, args.path, clip_media, args.mp3, args.cookies)

if __name__ == "__main__":
    main()