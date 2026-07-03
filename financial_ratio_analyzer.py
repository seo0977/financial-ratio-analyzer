"""
financial-ratio-analyzer
--------------------------
일반 기업에 쓰이는 표준 재무비율(차입금비율, 이자보상비율 등)은 금융지주회사처럼
자회사 출자 구조를 가진 기업에는 적합하지 않을 수 있다는 문제의식에서 출발한
재무비율 분석 도구입니다.

배경
----
금융지주회사는 금융당국의 규제(부채비율, 이중레버리지비율)를 받기 때문에,
일반 기업 분석에 쓰이는 차입금비율·이자보상비율·고정장기적합율보다는
"부채비율"과 "이중레버리지비율"을 사용하는 것이 실제로 더 적절한 판단 기준입니다.
(2024년 메리츠금융지주 재무제표 분석 과제에서 이 판단을 직접 내렸던 경험을 코드로
재구성했습니다.)

이 스크립트는 기업이 금융지주회사인지 여부에 따라 적용할 비율 체계를 다르게
선택하고, 지주회사인 경우 이중레버리지비율이 금융당국 규제선(130%) 대비
얼마나 여유가 있는지까지 자동으로 판정합니다.
"""

from dataclasses import dataclass


REGULATORY_LIMIT_DOUBLE_LEVERAGE = 130.0  # 금융당국 규제 마지노선 (%)
WARNING_MARGIN = 10.0  # 규제선까지 여유가 이 %p 이내면 경고


@dataclass
class FinancialStatement:
    company: str
    year: int
    total_liabilities: float     # 부채총계 (억원)
    total_equity: float          # 자본총계 (억원)
    is_financial_holding: bool
    subsidiary_investment: float = None   # 자회사 출자총액 (억원) - 지주회사인 경우 필수
    total_borrowings: float = None        # 차입금 (억원) - 일반기업 분석 시 사용
    operating_income: float = None        # 영업이익 (억원)
    interest_expense: float = None        # 이자비용 (억원)


def analyze(fs: FinancialStatement) -> dict:
    """
    기업 유형에 따라 적용할 비율 체계를 선택하고 계산합니다.
    - 금융지주회사: 부채비율 + 이중레버리지비율 (규제 기준)
    - 일반 기업: 차입금비율 + 이자보상비율 (통상 기준)
    """
    debt_ratio = round(fs.total_liabilities / fs.total_equity, 4)  # 배(x)

    if fs.is_financial_holding:
        if fs.subsidiary_investment is None:
            raise ValueError("금융지주회사 분석에는 subsidiary_investment(자회사 출자총액)가 필요합니다.")

        double_leverage_ratio = round(
            fs.subsidiary_investment / fs.total_equity * 100, 1
        )
        margin_to_limit = round(REGULATORY_LIMIT_DOUBLE_LEVERAGE - double_leverage_ratio, 1)

        return {
            "company": fs.company,
            "year": fs.year,
            "method": "금융지주회사 규제 기준 (부채비율 + 이중레버리지비율)",
            "reason": (
                "금융지주회사는 부채비율과 이중레버리지비율의 규제를 받으므로, "
                "일반적으로 쓰이는 차입금비율·이자보상비율보다 이 두 지표가 "
                "실질적인 재무위험을 더 적절히 반영합니다."
            ),
            "부채비율(배)": debt_ratio,
            "이중레버리지비율(%)": double_leverage_ratio,
            "규제선 대비 여력(%p)": margin_to_limit,
            "경고": margin_to_limit <= WARNING_MARGIN,
        }

    # 일반 기업: 차입금비율 + 이자보상비율
    result = {
        "company": fs.company,
        "year": fs.year,
        "method": "일반 기업 기준 (차입금비율 + 이자보상비율)",
        "부채비율(배)": debt_ratio,
    }
    if fs.total_borrowings is not None:
        result["차입금비율(%)"] = round(fs.total_borrowings / fs.total_equity * 100, 1)
    if fs.operating_income is not None and fs.interest_expense:
        result["이자보상비율(배)"] = round(fs.operating_income / fs.interest_expense, 2)

    return result


def print_report(result: dict):
    print(f"[{result['company']} {result['year']}] {result['method']}")
    if "reason" in result:
        print(f"  판단 근거: {result['reason']}")
    for key, value in result.items():
        if key in ("company", "year", "method", "reason"):
            continue
        print(f"  {key}: {value}")
    if result.get("경고"):
        print(f"  ⚠️ 규제선({REGULATORY_LIMIT_DOUBLE_LEVERAGE}%)까지 여유가 {WARNING_MARGIN}%p 이하로, 선제적 자본 확충 검토 필요")


if __name__ == "__main__":
    # 실제 2024년 재무제표 분석 과제 데이터 (2023 회계연도 기준, 단위: 억원)
    # 부채총계·자회사 출자총액은 원자료에서 별도 확인이 어려운 항목이 있어,
    # 보고서에 명시된 실제 비율(부채비율 9.1252 / 10.3559, 이중레버리지비율
    # 122.4% / 98.3%)로부터 역산한 값을 사용했습니다.
    meritz = FinancialStatement(
        company="메리츠금융지주",
        year=2023,
        total_liabilities=921_306,
        total_equity=100_972,
        is_financial_holding=True,
        subsidiary_investment=123_589,
    )

    hankook = FinancialStatement(
        company="한국금융지주",
        year=2023,
        total_liabilities=941_594,
        total_equity=90_923,
        is_financial_holding=True,
        subsidiary_investment=89_378,
    )

    print_report(analyze(meritz))
    print()
    print_report(analyze(hankook))
