"""Download French's three-factor monthly series and freeze a defined window."""

from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
)
START_DATE = "2025-07-01"
END_DATE = "2026-06-30"


def main():
    response = requests.get(URL, timeout=60)
    response.raise_for_status()
    with ZipFile(BytesIO(response.content)) as archive:
        source = archive.read(archive.namelist()[0]).decode("utf-8-sig")
    lines = source.splitlines()
    # 法国教授的数据同时包含月度与年度表；只选六位年月的月度行。
    rows = [
        line
        for line in lines
        if line.split(",", 1)[0].strip().isdigit() and len(line.split(",", 1)[0].strip()) == 6
    ]
    frame = pd.read_csv(StringIO("month,mktrf,SMB,HML,rf\n" + "\n".join(rows)))
    frame["date"] = pd.to_datetime(
        frame.pop("month").astype(str), format="%Y%m"
    ) + pd.offsets.MonthEnd(0)
    frame = frame.loc[frame.date.between(START_DATE, END_DATE), ["date", "SMB", "HML"]].copy()
    # 原始文件单位为百分数，除以 100 后与 HW1 的小数收益率一致。
    frame[["SMB", "HML"]] = frame[["SMB", "HML"]].apply(pd.to_numeric) / 100
    expected = pd.date_range(START_DATE, END_DATE, freq="ME")
    if frame.date.duplicated().any() or not frame.date.reset_index(drop=True).equals(
        pd.Series(expected)
    ):
        raise ValueError("Official series does not contain the expected 12 monthly observations")
    frame.to_csv(Path(__file__).parent / "french_factors.csv", index=False, float_format="%.8f")
    print(
        f"Official factors: {len(frame)} months, {frame.date.min().date()} to {frame.date.max().date()}"
    )


if __name__ == "__main__":
    main()
