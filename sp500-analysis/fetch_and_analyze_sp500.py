"""
S&P 500 (^GSPC) 2000-01-01 ~ 현재 데이터를 yfinance로 수집/클렌징하고
파이썬 Pandas로 다각도 분석한다.
- 데이터 클렌징
- 다각도 분석 (연도별/월별 수익률, 이동평균, 변동성, 최대낙폭 등)
- 전체 기간 종가 라인 그래프 출력
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import yfinance as yf

TICKER = "^GSPC"  # S&P 500 지수
START_DATE = "2000-01-01"

BASE_DIR = Path(__file__).resolve().parent
RAW_CSV_PATH = BASE_DIR / "sp500_raw_yfinance.csv"
CLEANED_CSV_PATH = BASE_DIR / "sp500_cleaned_2000.csv"
CHART_PATH = BASE_DIR / "sp500_close_full_period_2000.png"


def fetch_data(ticker: str, start: str) -> pd.DataFrame:
    df = yf.download(ticker, start=start, progress=False, auto_adjust=False)
    if df.empty:
        raise RuntimeError(f"yfinance에서 {ticker} 데이터를 가져오지 못했습니다.")

    # 단일 티커 요청이라도 MultiIndex 컬럼으로 오는 버전 대응
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.to_csv(RAW_CSV_PATH)
    print(f"원본 데이터 저장 완료: {RAW_CSV_PATH} ({len(df)}행)")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df.index.name = "date"
    df = df[["open", "high", "low", "close", "volume"]].copy()

    before = len(df)
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[~df.index.duplicated(keep="first")]
    after = len(df)
    if before != after:
        print(f"[클렌징] 결측/중복 제거: {before} -> {after} 행")

    invalid = df[df["high"] < df["low"]]
    if len(invalid):
        print(f"[클렌징] 고가<저가 이상치 {len(invalid)}건 발견 -> 제거")
        df = df.drop(invalid.index)

    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
    df = df.sort_index()
    return df


def run_analysis(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("1) 데이터 개요")
    print("=" * 60)
    print(f"기간: {df.index.min().date()} ~ {df.index.max().date()}")
    print(f"총 거래일 수: {len(df)}일")
    print(df[["open", "high", "low", "close"]].describe().round(2))

    print("\n" + "=" * 60)
    print("2) 일간 수익률 기반 통계")
    print("=" * 60)
    daily_return = df["close"].pct_change() * 100
    print(f"일평균 수익률: {daily_return.mean():.4f}%")
    print(f"일간 변동성(표준편차): {daily_return.std():.4f}%")
    best_day = daily_return.idxmax()
    worst_day = daily_return.idxmin()
    print(f"최고 상승일: {best_day.date()} ({daily_return[best_day]:.2f}%)")
    print(f"최고 하락일: {worst_day.date()} ({daily_return[worst_day]:.2f}%)")

    print("\n" + "=" * 60)
    print("3) 연도별 분석 (연초 대비 연말 수익률, 연중 최고/최저가)")
    print("=" * 60)
    yearly = df.groupby(df.index.year).agg(
        연시가=("open", "first"),
        연종가=("close", "last"),
        연최고=("high", "max"),
        연최저=("low", "min"),
    )
    yearly["연수익률(%)"] = ((yearly["연종가"] / yearly["연시가"]) - 1) * 100
    print(yearly.round(2))

    print("\n" + "=" * 60)
    print("4) 월별 평균 종가 및 월간 수익률 (최근 12개월)")
    print("=" * 60)
    monthly_close = df["close"].resample("ME").last()
    monthly_return = monthly_close.pct_change() * 100
    monthly_summary = pd.DataFrame(
        {"월말종가": monthly_close, "월수익률(%)": monthly_return}
    ).round(2)
    print(monthly_summary.tail(12))

    print("\n" + "=" * 60)
    print("5) 이동평균 (최근 5거래일)")
    print("=" * 60)
    df["MA50"] = df["close"].rolling(50).mean()
    df["MA100"] = df["close"].rolling(100).mean()
    df["MA200"] = df["close"].rolling(200).mean()
    print(df[["close", "MA50", "MA100", "MA200"]].tail(5).round(2))

    print("\n" + "=" * 60)
    print("6) 최대 낙폭 (Maximum Drawdown) — 닷컴버블/금융위기/코로나 등")
    print("=" * 60)
    cumulative_max = df["close"].cummax()
    drawdown = (df["close"] / cumulative_max - 1) * 100
    mdd_date = drawdown.idxmin()
    print(f"최대 낙폭(MDD): {drawdown.min():.2f}% (발생일: {mdd_date.date()})")
    top5 = drawdown.nsmallest(5)
    print("낙폭 상위 5개 시점:")
    print(top5.round(2))

    print("\n" + "=" * 60)
    print("7) 전체 기간 총 수익률")
    print("=" * 60)
    total_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    n_years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = ((df["close"].iloc[-1] / df["close"].iloc[0]) ** (1 / n_years) - 1) * 100
    print(f"총 수익률: {total_return:.2f}%  (연평균 성장률 CAGR: {cagr:.2f}%)")


def plot_full_period_close(df: pd.DataFrame, out_path: Path) -> None:
    """종가 기준 전체 기간 라인 그래프"""
    fig, ax = plt.subplots(figsize=(14, 6.5), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(
        df.index,
        df["close"],
        color="#1f5fbf",
        linewidth=1.3,
        solid_capstyle="round",
    )

    ax.set_title(
        "S&P 500 (^GSPC) 종가 추이 — "
        f"{df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}",
        fontsize=14,
        fontweight="bold",
        pad=14,
        loc="left",
    )
    ax.set_xlabel("날짜")
    ax.set_ylabel("종가")

    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    ax.grid(True, axis="y", color="#e3e3e3", linewidth=0.8)
    ax.grid(False, axis="x")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#cccccc")

    ax.margins(x=0.01)
    fig.tight_layout()
    fig.savefig(out_path, facecolor="white")
    print(f"\n라인 그래프 저장 완료: {out_path}")


def main() -> None:
    plt.rcParams["font.family"] = [
        "AppleGothic",
        "Malgun Gothic",
        "NanumGothic",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False

    raw = fetch_data(TICKER, START_DATE)
    df = clean_data(raw)
    df.to_csv(CLEANED_CSV_PATH)
    print(f"클렌징된 데이터 저장 완료: {CLEANED_CSV_PATH}\n")

    run_analysis(df)
    plot_full_period_close(df, CHART_PATH)


if __name__ == "__main__":
    main()
