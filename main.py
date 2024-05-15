from datetime import datetime
import os
import cv2
from video import Video
from tcx_exporter import TCX
import numpy as np

def overlay_video(path, created_at, df):
    cap = cv2.VideoCapture(path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.set(fps, 30)


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
    map_width, map_height = 800, 800

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


        # if video timestamp is greater than the data time
        if timestamp > df.iloc[data_time_offset]['Time']:
            data_time_offset += 1
            coords = latlon_to_pixels(df.iloc[data_time_offset]['Latitude'], df.iloc[data_time_offset]['Longitude'], min_lat, max_lat, min_lon, max_lon, map_width, map_height)
            track.append(coords)

            

        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cap.release()
            break

    cap.release()

def overlay_data(ret, frame, data):
    formatted_time = datetime.fromtimestamp(data['Time']).strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, f"Time: {formatted_time}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Latitude: {data['Latitude']}", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Longitude: {data['Longitude']}", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Heart Rate: {data['HeartRate']} bpm", (50, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Speed: {data['Speed']} kts", (50, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    return frame

def draw_track(ret, frame, track):
    cv2.polylines(frame, [np.array(track)] , False, (0, 0, 0), 2)
    return frame

def latlon_to_pixels(lat, lon, min_lat, max_lat, min_lon, max_lon, image_width, image_height):
    # Map latitude to the y coordinate (inverted as pixel coords increase from top to bottom)
    pixel_y = int((lat - min_lat) / (max_lat - min_lat) * image_height)
    # Map longitude to the x coordinate
    pixel_x = int((lon - min_lon) / (max_lon - min_lon) * image_width)
    return (pixel_x, image_height - pixel_y)  # Return the (x, y) tuple



if __name__ == "__main__":
    tcx = TCX()
    tcx.get_info()
    df = tcx.extract_data()



    videos = Video(data_dir="./data/videos")
    video_path = videos.concat_videos()


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


    overlay_video(video_path, created_at, df)
