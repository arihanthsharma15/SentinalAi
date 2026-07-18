from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors

from services.gemma_service import GemmaService


class ReportService:
    """
    Generates Compliance Investigation Reports.
    """

    @staticmethod
    def generate_statistics(records):
        """
        Generate summary statistics.
        """

        total = len(records)

        high = 0
        medium = 0
        low = 0

        for record in records:

            score = record.gemmaAnalysis.risk_score

            if score >= 80:
                high += 1
            elif score >= 50:
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
    def generate_pdf(records, output_path="Compliance_Report.pdf"):
        """
        Generate PDF report.
        """

        stats = ReportService.generate_statistics(records)

        # ----------------------------
        # AI Executive Summary
        # ----------------------------

        ai_summary = GemmaService.generate_report(records)

        # ----------------------------
        # PDF
        # ----------------------------

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

        # ----------------------------
        # Statistics
        # ----------------------------

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

        # ----------------------------
        # AI Summary
        # ----------------------------

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

        # ----------------------------
        # Detailed Findings
        # ----------------------------

        elements.append(
            Paragraph(
                "<b>Detailed Findings</b>",
                styles["Heading2"],
            )
        )

        table_data = [
            [
                "ID",
                "Type",
                "Risk",
                "Category",
                "Recommendation",
            ]
        ]

        for record in records:

            table_data.append(
                [
                    record.id,
                    record.type,
                    str(record.gemmaAnalysis.risk_score),
                    record.gemmaAnalysis.risk_category,
                    record.gemmaAnalysis.recommended_action,
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