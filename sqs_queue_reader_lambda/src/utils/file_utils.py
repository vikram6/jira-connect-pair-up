import os
import pandas as pd


def util_read_csv(folder, filename, file_delimiter=','):
    reqd_file = os.path.join(folder, filename)
    print("Currently reading File {}".format(reqd_file))
    csv_data = pd.read_csv(reqd_file, delimiter=file_delimiter, encoding="utf-8")
    print("Completed reading File {}".format(reqd_file))
    return csv_data