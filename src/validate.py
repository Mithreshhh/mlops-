import os
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.checkpoint.checkpoint import Checkpoint
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student-mat.csv")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "monitoring")
REPORT_PATH = os.path.join(REPORT_DIR, "validation_report.html")


def build_html_report(checkpoint_result) -> str:
    described = checkpoint_result.describe_dict()
    overall_success = described["success"]
    validations = described["validation_results"][0]
    stats = validations["statistics"]
    expectations = validations["expectations"]

    passed = stats["successful_expectations"]
    total_exp = stats["evaluated_expectations"]
    failed = total_exp - passed
    pass_pct = (passed / total_exp * 100) if total_exp else 0

    rows = ""
    for i, exp in enumerate(expectations):
        exp_type = exp.get("expectation_type", exp.get("type", "unknown"))
        kwargs = exp.get("kwargs", {})
        column = kwargs.get("column", "N/A")
        success = exp["success"]
        result = exp.get("result", {})

        friendly_name = (
            exp_type.replace("expect_column_values_to_", "")
            .replace("expect_column_", "")
            .replace("_", " ")
            .title()
        )

        if success:
            badge = '<span class="badge pass">PASS</span>'
            row_class = "row-pass"
        else:
            badge = '<span class="badge fail">FAIL</span>'
            row_class = "row-fail"

        if "element_count" in result:
            unexpected = result.get("unexpected_count", 0)
            total = result["element_count"]
            unexpected_pct = result.get("unexpected_percent", 0.0)
            if unexpected == 0:
                detail = f'<span class="detail-ok">{total} rows checked &mdash; all valid</span>'
            else:
                detail = f'<span class="detail-bad">{unexpected} of {total} invalid ({unexpected_pct:.2f}%)</span>'
        else:
            detail = '<span class="detail-ok">OK</span>' if success else '<span class="detail-bad">Failed</span>'

        constraint = ""
        if "min_value" in kwargs and "max_value" in kwargs:
            constraint = f'<code>{kwargs["min_value"]} &le; x &le; {kwargs["max_value"]}</code>'
        elif "min_value" in kwargs:
            constraint = f'<code>x &ge; {kwargs["min_value"]}</code>'
        elif "max_value" in kwargs:
            constraint = f'<code>x &le; {kwargs["max_value"]}</code>'
        elif "not_null" in exp_type.lower() or "to_not_be_null" in exp_type:
            constraint = "<code>NOT NULL</code>"

        rows += f"""
            <tr class="{row_class}">
                <td><strong>{column}</strong></td>
                <td>{friendly_name}</td>
                <td>{constraint}</td>
                <td class="center">{badge}</td>
                <td>{detail}</td>
            </tr>"""

    if overall_success:
        status_class = "status-pass"
        status_icon = "&#10003;"
        status_text = "All Validations Passed"
    else:
        status_class = "status-fail"
        status_icon = "&#10007;"
        status_text = "Failures Detected"

    stat_cards = f"""
        <div class="stat-card">
            <div class="stat-number">{total_exp}</div>
            <div class="stat-label">Total Checks</div>
        </div>
        <div class="stat-card card-pass">
            <div class="stat-number">{passed}</div>
            <div class="stat-label">Passed</div>
        </div>
        <div class="stat-card card-fail">
            <div class="stat-number">{failed}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{pass_pct:.0f}%</div>
            <div class="stat-label">Pass Rate</div>
        </div>"""

    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Validation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 40px 24px;
        }}
        .container {{ max-width: 960px; margin: 0 auto; }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 32px;
        }}
        .header h1 {{
            font-size: 1.8em;
            font-weight: 700;
            color: #f8fafc;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            color: #94a3b8;
            font-size: 0.95em;
            margin-top: 6px;
        }}

        /* Status banner */
        .status-banner {{
            text-align: center;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 24px;
            font-size: 1.25em;
            font-weight: 600;
        }}
        .status-pass {{
            background: linear-gradient(135deg, #065f46, #047857);
            border: 1px solid #10b981;
        }}
        .status-fail {{
            background: linear-gradient(135deg, #7f1d1d, #991b1b);
            border: 1px solid #ef4444;
        }}
        .status-banner .icon {{ font-size: 1.4em; margin-right: 8px; }}

        /* Stat cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }}
        .card-pass {{ border-color: rgba(16,185,129,0.3); }}
        .card-fail {{ border-color: rgba(239,68,68,0.3); }}
        .stat-number {{ font-size: 2em; font-weight: 700; color: #f8fafc; }}
        .card-pass .stat-number {{ color: #34d399; }}
        .card-fail .stat-number {{ color: #f87171; }}
        .stat-label {{ color: #94a3b8; font-size: 0.85em; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}

        /* Table */
        .table-wrapper {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{
            background: rgba(255,255,255,0.06);
            color: #94a3b8;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            padding: 14px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        td {{
            padding: 14px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            font-size: 0.92em;
        }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .row-fail {{ background: rgba(239,68,68,0.05); }}
        .center {{ text-align: center; }}
        code {{
            background: rgba(255,255,255,0.08);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #a5b4fc;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.78em;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .badge.pass {{
            background: rgba(16,185,129,0.15);
            color: #34d399;
            border: 1px solid rgba(16,185,129,0.3);
        }}
        .badge.fail {{
            background: rgba(239,68,68,0.15);
            color: #f87171;
            border: 1px solid rgba(239,68,68,0.3);
        }}

        /* Detail text */
        .detail-ok {{ color: #94a3b8; }}
        .detail-bad {{ color: #fbbf24; }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 32px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.06);
            color: #64748b;
            font-size: 0.82em;
        }}
        .footer span {{ color: #94a3b8; }}

        @media (max-width: 640px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            td, th {{ padding: 10px 12px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Data Validation Report</h1>
            <p class="subtitle">student-mat.csv &mdash; Great Expectations Suite</p>
        </div>

        <div class="status-banner {status_class}">
            <span class="icon">{status_icon}</span> {status_text}
        </div>

        <div class="stats-grid">{stat_cards}
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Column</th>
                        <th>Check</th>
                        <th>Constraint</th>
                        <th class="center">Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>{rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <span>{timestamp}</span> &nbsp;&bull;&nbsp;
            Great Expectations v{gx.__version__} &nbsp;&bull;&nbsp;
            Python 3.12
        </div>
    </div>
</body>
</html>"""
    return html


def validate():
    df = pd.read_csv(DATA_PATH, sep=";")

    context = gx.get_context()

    data_source = context.data_sources.add_pandas("pandas")
    data_asset = data_source.add_dataframe_asset(name="student_data")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("student_batch")

    suite = context.suites.add(ExpectationSuite(name="student_suite"))

    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="G3", min_value=0, max_value=20
        )
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="age", min_value=15, max_value=22
        )
    )
    for col in ["G1", "G2", "G3"]:
        suite.add_expectation(
            gx.expectations.ExpectColumnValuesToNotBeNull(column=col)
        )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="studytime", min_value=1, max_value=4
        )
    )

    validation_definition = context.validation_definitions.add(
        ValidationDefinition(
            name="student_validation",
            data=batch_definition,
            suite=suite,
        )
    )

    checkpoint = context.checkpoints.add(
        Checkpoint(
            name="student_checkpoint",
            validation_definitions=[validation_definition],
        )
    )

    result = checkpoint.run(batch_parameters={"dataframe": df})

    os.makedirs(REPORT_DIR, exist_ok=True)
    html = build_html_report(result)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    described = result.describe_dict()
    stats = described["validation_results"][0]["statistics"]
    print(f"Validation {'PASSED' if described['success'] else 'FAILED'}")
    print(f"  {stats['successful_expectations']}/{stats['evaluated_expectations']} expectations passed")
    print(f"Report saved to: {os.path.abspath(REPORT_PATH)}")


if __name__ == "__main__":
    validate()
