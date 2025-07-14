import os

filename = "resulsts.txt"

def batch(resulst):
    if(os.path.exists(filename)):
        os.remove(filename)
        with open(filename) as f:
            for category, rank, url, score in resulst:
                line = f"{category}\t{rank}\t{url}\t{score: .3f}\n"
                f.write(line)