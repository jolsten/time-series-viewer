import numpy as np
import polars as pl


def square_wave(x: float) -> int:
    return 1 if x > 0 else -1


def main():
    time = pl.datetime_range(
        np.datetime64("2025-01-01", "ns"),
        np.datetime64("2025-01-31", "ns"),
        interval="1s",
        eager=True,
    )
    df = pl.DataFrame({"time": time})
    df = df.with_row_index()
    df = df.with_columns(
        [
            (pl.col("index") * 2 * np.pi / 86400).sin().alias("sin"),
            (pl.col("index") * 2 * np.pi / 86400).cos().alias("cos"),
        ]
    )
    df = df.with_columns(
        [
            (pl.col("sin") + pl.lit((np.random.rand(df.height) - 0.5) * 0.1)).alias(
                "noisy-sin"
            ),
            (pl.col("cos") + pl.lit((np.random.rand(df.height) - 0.5) * 0.1)).alias(
                "noisy-cos"
            ),
            pl.col("sin")
            .map_elements(square_wave, return_dtype=pl.Int8)
            .alias("sin_square"),
            pl.col("cos")
            .map_elements(square_wave, return_dtype=pl.Int8)
            .alias("cos_square"),
        ]
    )
    print(df.head(60))
    df.drop_in_place("index")
    df.write_parquet("data/big.parquet")
    df.write_csv("data/big.csv")


if __name__ == "__main__":
    main()
