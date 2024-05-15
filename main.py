from moviepy.editor import VideoFileClip, AudioFileClip
from datetime import datetime
import os
import cv2
from video import Video
from tcx_exporter import TCX
import numpy as np

def overlay_video(path, output_path, created_at, df):
    cap = cv2.VideoCapture(path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, codec, fps, (frame_width, frame_height))


    if created_at < df.iloc[0]['Time']:
        print("activity recorded after video")
    else:
        print("activity recorded before video")
        # search activity data for the closest timestamp to the video created_at
        start_index_activity = next(x[0] for x in enumerate(df['Time']) if x[1] > created_at)
        # truncate the dataframe to start from the closest timestamp
        df = df.iloc[start_index_activity:]


    # Define the bounds of your map, which could be the min/max of your lat/longs or a predefined range
    min_lat = min(lat for lat, lon in df[['Latitude', 'Longitude']].values)
    max_lat = max(lat for lat, lon in df[['Latitude', 'Longitude']].values)
    min_lon = min(lon for lat, lon in df[['Latitude', 'Longitude']].values)
    max_lon = max(lon for lat, lon in df[['Latitude', 'Longitude']].values)

    # Define the size of the map in pixels or as a percentage of the video frame
    map_width, map_height = 300, 300 # must be nxn pixels to avoid distortion
    map_pos = (50, 120)  # Position of the map in the video frame

    data_time_offset = 0
    frame_count = 0
    track = []
    while True:
        ret, frame = cap.read()
        frame_count += 1 
        if not ret:
            break

        timestamp = frame_count / fps + created_at

        if data_time_offset > 0 and data_time_offset < len(df) - 1:
            frame = overlay_data(ret, frame, df.iloc[data_time_offset])
            frame = draw_track(ret, frame, track)


        # align the activity data with the video
        while timestamp > df.iloc[data_time_offset]['Time']:
            data_time_offset += 1
            coords = latlon_to_pixels(df.iloc[data_time_offset]['Latitude'], df.iloc[data_time_offset]['Longitude'], min_lat, max_lat, min_lon, max_lon, map_width, map_height)
            pos = (coords[0] + map_pos[0], coords[1] + map_pos[1])
            track.append(pos)


        out.write(frame)
        cv2.imshow("Video", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cap.release()
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


def overlay_data(ret, frame, data):
    formatted_time = datetime.fromtimestamp(data['Time']).strftime("%Y-%m-%d %H:%M:%S")
    text_color = (255, 255, 255)
    bg_color = (0, 0, 0, 128)  # Semi-transparent background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    margin = 10

    texts = [
        f"Heart Rate: {data['HeartRate']} bpm",
        f"Speed: {data['Speed']} kts"
    ]

    y0, dy = 50, 50
    for i, text in enumerate(texts):
        y = y0 + i * dy
        (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        frame = cv2.rectangle(frame, (50 - margin, y - h - margin), (50 + w + margin, y + margin), bg_color, -1)
        frame = cv2.putText(frame, text, (50, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
    return frame

def draw_track(ret, frame, track):
    track_color = (0, 0, 0, 0)  # Green color for track
    thickness = 2
    frame = cv2.polylines(frame, [np.array(track)], False, track_color, thickness)
    if track:
        current_pos = track[-1]
        frame = cv2.circle(frame, current_pos, 5, track_color, -1)  # Marker for current position
    return frame

def latlon_to_pixels(lat, lon, min_lat, max_lat, min_lon, max_lon, image_width, image_height):
    # Map latitude to the y coordinate (inverted as pixel coords increase from top to bottom)
    pixel_y = int((lat - min_lat) / (max_lat - min_lat) * image_height)
    # Map longitude to the x coordinate
    pixel_x = int((lon - min_lon) / (max_lon - min_lon) * image_width)
    return (pixel_x, image_height - pixel_y)  # Return the (x, y) tuple


def merge_audio(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = VideoFileClip(audio_path).audio
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(output_path, codec='libx264')


if __name__ == "__main__":
    tcx = TCX()
    tcx.get_info()
    df = tcx.extract_data()



    if not os.path.exists("./output/raw.mp4"):
        videos = Video(data_dir="./data/videos")
        video_path = videos.concat_videos()
    else:
        video_path = "./output/raw.mp4"

    cap = cv2.VideoCapture(video_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.set(fps, 30)

    created_at = "2024-05-11 14:44:42"
    #created_at = "2024-05-11 14:55:27" # debug
    # to unix timestamp
    
    created_at = int(datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").timestamp())

    #time data '2024-05-11T14:47:27.000Z'
    df['Time'] = df['Time'].apply(lambda x: x.replace('T', ' ').replace('.000Z', ''))
    df['Time'] = df['Time'].apply(lambda x: int(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").timestamp()))


    # round speed to 2 decimal places
    df['Speed'] = df['Speed'].apply(lambda x: round(float(x), 2))

    # convert lat and lon to float
    df['Latitude'] = df['Latitude'].apply(lambda x: float(x))
    df['Longitude'] = df['Longitude'].apply(lambda x: float(x))


    overlay_video(video_path, "./output/overlay_video.mp4", created_at, df)

    merge_audio("./output/overlay_video.mp4", "./output/raw.mp4", "./output/final_video.mp4")

