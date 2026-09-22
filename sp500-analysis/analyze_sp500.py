"""
Investing.com S&P 500(United States 500) 과거 데이터 분석
- 데이터 클렌징
- 다각도 분석 (연도별/월별 수익률, 이동평균, 변동성, 최대낙폭 등)
- 전체 기간 종가 라인 그래프 출력
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import pandas as pd

# 실행 위치(현재 작업 디렉터리)와 무관하게 항상 이 스크립트 파일 기준으로 경로를 찾는다.
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Investing.com United States 500 과거 데이터.csv"
CLEANED_CSV_PATH = BASE_DIR / "sp500_cleaned.csv"
CHART_PATH = BASE_DIR / "sp500_close_full_period.png"

PRICE_COLUMNS = {"종가": "close", "시가": "open", "고가": "high", "저가": "low"}


def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 날짜: "2026- 09- 21" 형태의 공백 제거 후 파싱
    df["날짜"] = df["날짜"].str.replace(" ", "", regex=False)
    df["date"] = pd.to_datetime(df["날짜"], format="%Y-%m-%d")

    # 가격 컬럼: 천 단위 구분 콤마 제거 후 float 변환
    for col_kr, col_en in PRICE_COLUMNS.items():
        df[col_en] = (
            df[col_kr].astype(str).str.replace(",", "", regex=False).astype(float)
        )

    # 변동 %: "1.58%" -> 1.58
    df["change_pct"] = (
        df["변동 %"].astype(str).str.replace("%", "", regex=False).astype(float)
    )

    # 거래량 컬럼은 전 구간 결측이라 분석에서 제외
    df = df[["date", "open", "high", "low", "close", "change_pct"]]

    # 원본은 최신순(내림차순) 정렬이므로 날짜 오름차순으로 정렬
    df = df.sort_values("date").reset_index(drop=True)

    # 중복 날짜, 결측치 확인 및 제거
    before = len(df)
    df = df.drop_duplicates(subset="date")
    df = df.dropna(subset=["open", "high", "low", "close"])
    after = len(df)
    if before != after:
        print(f"[클렌징] 중복/결측 제거: {before} -> {after} 행")

    # OHLC 논리적 정합성 체크 (고가 >= 저가, 고가 >= 종가/시가, 저가 <= 종가/시가)
    invalid = df[(df["high"] < df["low"])]
    if len(invalid):
        print(f"[클렌징] 고가<저가 이상치 {len(invalid)}건 발견 -> 제거")
        df = df.drop(invalid.index)

    df = df.set_index("date")
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
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()
    df["MA200"] = df["close"].rolling(200).mean()
    print(df[["close", "MA20", "MA50", "MA200"]].tail(5).round(2))

    print("\n" + "=" * 60)
    print("6) 최대 낙폭 (Maximum Drawdown)")
    print("=" * 60)
    cumulative_max = df["close"].cummax()
    drawdown = (df["close"] / cumulative_max - 1) * 100
    mdd_date = drawdown.idxmin()
    print(f"최대 낙폭(MDD): {drawdown.min():.2f}% (발생일: {mdd_date.date()})")

    print("\n" + "=" * 60)
    print("7) 전체 기간 총 수익률")
    print("=" * 60)
    total_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    n_years = (df.index[-1] - df.index[0]).days / 365.25
    cagr = ((df["close"].iloc[-1] / df["close"].iloc[0]) ** (1 / n_years) - 1) * 100
    print(f"총 수익률: {total_return:.2f}%  (연평균 성장률 CAGR: {cagr:.2f}%)")


def plot_full_period_close(df: pd.DataFrame, out_path: str) -> None:
    """종가 기준 전체 기간 라인 그래프"""
    fig, ax = plt.subplots(figsize=(14, 6.5), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(
        df.index,
        df["close"],
        color="#1f5fbf",  # 단일 계열: 진한 블루
        linewidth=1.6,
        solid_capstyle="round",
    )

    ax.set_title(
        "S&P 500 (US 500) 종가 추이 — "
        f"{df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}",
        fontsize=14,
        fontweight="bold",
        pad=14,
        loc="left",
    )
    ax.set_xlabel("날짜")
    ax.set_ylabel("종가")

    ax.xaxis.set_major_locator(mdates.YearLocator())
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

    df = load_and_clean(CSV_PATH)
    df.to_csv(CLEANED_CSV_PATH, encoding="utf-8-sig")
    print(f"클렌징된 데이터 저장 완료: {CLEANED_CSV_PATH}\n")

    run_analysis(df)
    plot_full_period_close(df, CHART_PATH)


if __name__ == "__main__":
    main()
