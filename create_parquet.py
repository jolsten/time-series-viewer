import pathlib

import numpy as np
import polars as pl


def main():
    df = pl.DataFrame({"time": np.array([], dtype="datetime64[us]")})
    for file in pathlib.Path("data").glob("*/**.csv"):
        new = pl.read_csv(file, try_parse_dates=True).rename(
            {"value": file.stem, "timestamp": "time"}
        )
        df = df.join(new, on="time", how="full", coalesce=True)
    df.write_parquet("data/artificial.parquet")


if __name__ == "__main__":
    main()
