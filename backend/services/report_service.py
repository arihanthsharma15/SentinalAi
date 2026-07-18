from datetime import datetime


class ReportService:
    """
    Generate summary statistics and PDF investigation reports.
    """

    @staticmethod
    def generate_statistics(records):
        """
        Build a risk distribution summary for flagged records.
        """
        total = len(records or [])
        high = 0
        medium = 0
        low = 0

        for record in records or []:
            risk_score = getattr(getattr(record, "gemmaAnalysis", None), "risk_score", None)

            if risk_score is None:
                low += 1
            elif risk_score >= 80:
                high += 1
            elif risk_score >= 50:
                medium += 1
            else:
                low += 1

        return {
            "total_flagged": total,
            "high": high,
            "medium": medium,
            "low": low,
        }

    @staticmethod
    def _safe_ai_summary(records):
        """
        Return a stable summary text even if the AI service is unavailable.
        """
        stats = ReportService.generate_statistics(records)

        summary = [
            "Executive Summary:",
            f"- Total flagged records: {stats['total_flagged']}",
            f"- High risk: {stats['high']}",
            f"- Medium risk: {stats['medium']}",
            f"- Low risk: {stats['low']}",
        ]

        try:
            from services.gemma_service import GemmaService
            if hasattr(GemmaService, "generate_report"):
                generated = GemmaService.generate_report(records)
                if generated:
                    return generated
        except Exception:
            pass

        summary.append(
            "Review the detailed findings table below for record-level recommendations."
        )
        return "\n".join(summary)

    @staticmethod
    def generate_pdf(records, output_path="Compliance_Report.pdf"):
        """
        Generate a PDF report for the supplied flagged records.
        Falls back to a plain-text report if reportlab is unavailable.
        """
        stats = ReportService.generate_statistics(records)
        ai_summary = ReportService._safe_ai_summary(records)

        try:
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            doc = SimpleDocTemplate(output_path)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(
                Paragraph(
                    "<b>SentinelAI Compliance Investigation Report</b>",
                    styles["Title"],
                )
            )
            elements.append(Spacer(1, 20))
            elements.append(
                Paragraph(
                    f"Generated: {datetime.now()}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 15))

            elements.append(
                Paragraph(
                    "<b>Executive Statistics</b>",
                    styles["Heading2"],
                )
            )
            elements.append(
                Paragraph(
                    f"Total Flagged Records : {stats['total_flagged']}",
                    styles["Normal"],
                )
            )
            elements.append(
                Paragraph(
                    f"High Risk : {stats['high']}",
                    styles["Normal"],
                )
            )
            elements.append(
                Paragraph(
                    f"Medium Risk : {stats['medium']}",
                    styles["Normal"],
                )
            )
            elements.append(
                Paragraph(
                    f"Low Risk : {stats['low']}",
                    styles["Normal"],
                )
            )
            elements.append(Spacer(1, 20))

            elements.append(
                Paragraph(
                    "<b>AI Executive Summary</b>",
                    styles["Heading2"],
                )
            )
            elements.append(
                Paragraph(
                    ai_summary,
                    styles["BodyText"],
                )
            )
            elements.append(Spacer(1, 20))

            elements.append(
                Paragraph(
                    "<b>Detailed Findings</b>",
                    styles["Heading2"],
                )
            )

            table_data = [["ID", "Type", "Risk", "Category", "Recommendation"]]

            for record in records or []:
                gemma_analysis = getattr(record, "gemmaAnalysis", None)
                table_data.append(
                    [
                        getattr(record, "id", ""),
                        getattr(record, "type", ""),
                        str(getattr(gemma_analysis, "risk_score", "")),
                        getattr(gemma_analysis, "risk_category", ""),
                        getattr(gemma_analysis, "recommended_action", ""),
                    ]
                )

            table = Table(table_data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ]
                )
            )

            elements.append(table)
            doc.build(elements)
            return output_path

        except Exception:
            report_lines = [
                "SentinelAI Compliance Investigation Report",
                f"Generated: {datetime.now()}",
                f"Total Flagged Records : {stats['total_flagged']}",
                f"High Risk : {stats['high']}",
                f"Medium Risk : {stats['medium']}",
                f"Low Risk : {stats['low']}",
                "",
                "AI Executive Summary:",
                ai_summary,
                "",
                "Detailed Findings:",
            ]

            for record in records or []:
                gemma_analysis = getattr(record, "gemmaAnalysis", None)
                report_lines.append(
                    "- "
                    f"ID={getattr(record, 'id', '')}, "
                    f"Type={getattr(record, 'type', '')}, "
                    f"Risk={getattr(gemma_analysis, 'risk_score', '')}, "
                    f"Category={getattr(gemma_analysis, 'risk_category', '')}, "
                    f"Recommendation={getattr(gemma_analysis, 'recommended_action', '')}"
                )

            with open(output_path, "w", encoding="utf-8") as report_file:
                report_file.write("\n".join(report_lines))

            return output_path
