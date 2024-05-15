import os
from datetime import datetime
import cv2
import subprocess


class Video:
    def __init__(self, data_dir="./data", output_dir="./output"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.videos = self.get_videos()

    def get_videos(self):
        videos =  [f for f in os.listdir(self.data_dir) if f.endswith(".MP4")]
        if len(videos) == 0:
            raise Exception("No videos found in the data directory")

        # sort videos by title (numerically)
        videos.sort()
        return videos

    def concat_videos(self, output_file="raw.mp4"):
        output_file = os.path.join(self.output_dir, output_file)
        if len(self.videos) == 0:
            raise Exception("No videos found in the data directory")

        full_path_videos = [os.path.join(self.data_dir, video) for video in self.videos]

        # use ffmpeg to concatenate videos
        # ffmpeg -f concat -safe 0 -i mylist.txt -c copy output.mp4
        with open("mylist.txt", "w") as f:
            for video in full_path_videos:
                f.write(f"file '{video}'\n")

        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "mylist.txt", "-c", "copy", output_file])

        return output_file

if __name__ == "__main__":
    video = Video("./data/videos")
    print(video.videos)
