# Description: Extracts the data from a TCX file

from xml.etree import ElementTree as ET
import pandas as pd
import os

class TCX:
    def __init__(self, tcx_file=None, data_dir="./data"):
        if tcx_file is None:
            self.tcx_file = os.path.join(data_dir, [f for f in os.listdir(data_dir) if f.endswith(".tcx")][0])
        else:
            self.tcx_file = tcx_file

        self.data = self.extract_data()

    def extract_data(self):
        data = self.parse_tcx()
        df = pd.DataFrame(data)
        return df

    def get_info(self):
        if self.data is None:
            raise Exception("No data found. Please run extract_data() first.")

        print("Number of trackpoints: ", len(self.data))


    def parse_tcx(self):
        tree = ET.parse(self.tcx_file)
        root = tree.getroot()

        # Get the namespace
        ns = root.tag.split("}")[0] + "}"

        # Get the activity
        activity = root.find(f"{ns}Activities/{ns}Activity")
        activity_id = activity.find(f"{ns}Id").text

        trackpoints = activity.findall(f"{ns}Lap/{ns}Track/{ns}Trackpoint")
        data = []

        if len(trackpoints) == 0:
            print("No trackpoints found in the TCX file")
            return

        for trackpoint in trackpoints:
            trackpoint_info = {}

            # Get the time
            time = trackpoint.find(f"{ns}Time").text

            if time is None:
                continue

            for child in trackpoint:
                data_field = child.tag.split("}")[1]

                if data_field == "Position":
                    trackpoint_info["Latitude"] = child.find(f"{ns}LatitudeDegrees").text
                    trackpoint_info["Longitude"] = child.find(f"{ns}LongitudeDegrees").text
                elif data_field == "HeartRateBpm":
                    trackpoint_info["HeartRate"] = child.find(f"{ns}Value").text
                elif data_field == "Extensions":
                    tpx_child = child[0]

                    # Check if there are any extensions (speed, cadence, etc.)
                    if tpx_child is not None:
                        for tpx in tpx_child:
                            data_field = tpx.tag.split("}")[1]
                            trackpoint_info[data_field] = tpx.text
                else:
                    trackpoint_info[data_field] = child.text    
            data.append(trackpoint_info)
        return data


if __name__ == "__main__":
    tcx = TCX()
    print(tcx.tcx_file)

    df = tcx.extract_data()
    df.to_csv("data.csv", index=False)





