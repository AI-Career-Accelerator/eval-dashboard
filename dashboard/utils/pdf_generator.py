"""
PDF Report Generator
Creates executive-ready PDF reports with evaluation results, charts, and metrics.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import plotly.express as px
import pandas as pd
from io import BytesIO
import tempfile
import os

# --- Layout Constants ---
PAGE_MARGIN = 0.5 * inch
PAGE_WIDTH, PAGE_HEIGHT = letter
CONTENT_WIDTH = PAGE_WIDTH - (2 * PAGE_MARGIN)

class PDFReportGenerator:
    """Generate professional, clean PDF reports with comprehensive insights."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Colors
        self.primary_color = colors.HexColor('#2563EB')
        self.accent_color = colors.HexColor('#10B981')
        self.text_primary = colors.HexColor('#111827')
        self.text_secondary = colors.HexColor('#6B7280')
        self.bg_light = colors.HexColor('#F9FAFB')
        
        self._setup_custom_styles()
        self._temp_files = []

    def _setup_custom_styles(self):
        """Setup styles with explicit leading to prevent text overlap."""
        
        # Title
        if 'ReportTitle' in self.styles: self.styles.pop('ReportTitle')
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Normal'],
            fontSize=24,
            leading=30,
            textColor=self.text_primary,
            fontName='Helvetica-Bold',
            spaceAfter=10
        ))

        # Section Header
        if 'SectionHeader' in self.styles: self.styles.pop('SectionHeader')
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=14,
            leading=18,
            textColor=self.primary_color,
            fontName='Helvetica-Bold',
            spaceBefore=15,
            spaceAfter=10,
            textTransform='uppercase'
        ))
        
        # Metric Value (Large)
        if 'MetricVal' in self.styles: self.styles.pop('MetricVal')
        self.styles.add(ParagraphStyle(
            name='MetricVal',
            parent=self.styles['Normal'],
            fontSize=20,
            leading=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Metric Label (Small)
        if 'MetricLab' in self.styles: self.styles.pop('MetricLab')
        self.styles.add(ParagraphStyle(
            name='MetricLab',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            textColor=self.text_secondary,
            alignment=TA_CENTER
        ))

        # Body Text
        if 'CleanBody' in self.styles: self.styles.pop('CleanBody')
        self.styles.add(ParagraphStyle(
            name='CleanBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=15,
            textColor=self.text_primary
        ))

    def _create_metric_box(self, label, value, color=None):
        """Simple vertical stack for a metric."""
        style = self.styles['MetricVal']
        if color:
            style = ParagraphStyle('TempV', parent=style, textColor=color)
        return [
            Paragraph(value, style),
            Paragraph(label, self.styles['MetricLab'])
        ]

    def _create_plotly_image(self, fig):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                path = tmp.name
            fig.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white', 
                margin=dict(l=10,r=10,t=30,b=10),
                font=dict(size=10)
            )
            fig.write_image(path, width=1000, height=500, scale=2, engine='kaleido')
            self._temp_files.append(path)
            return RLImage(path, width=CONTENT_WIDTH, height=3*inch)
        except: return None

    def _cleanup(self):
        for p in self._temp_files:
            try: 
                if os.path.exists(p): os.unlink(p)
            except: pass
        self._temp_files = []

    def generate_model_comparison_report(self, models_df, output_path, title="Model Comparison Analysis"):
        doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN)
        story = []

        # 1. Header
        story.append(Paragraph(title, self.styles['ReportTitle']))
        story.append(Paragraph(f"Comparative Performance Analysis • Generated on {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        # 2. Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        best = models_df.loc[models_df['avg_accuracy'].idxmax()]
        cheap = models_df.loc[models_df['avg_cost'].idxmin()]
        fast = models_df.loc[models_df['avg_latency'].idxmin()]

        summary_data = [[
            self._create_metric_box("Peak Accuracy", f"{best['avg_accuracy']:.1%}"),
            self._create_metric_box("Lowest Cost", f"${cheap['avg_cost']:.4f}", self.accent_color),
            self._create_metric_box("Best Latency", f"{fast['avg_latency']:.2f}s"),
            self._create_metric_box("Models Compared", str(len(models_df)))
        ]]
        
        st_table = Table(summary_data, colWidths=[CONTENT_WIDTH/4]*4)
        st_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.bg_light),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(st_table)
        story.append(Spacer(1, 0.2*inch))

        # 3. Strategic Recommendation
        story.append(Paragraph("Strategic Recommendation", self.styles['SectionHeader']))
        
        # Weighted Score Logic (50% Acc, 30% Cost, 20% Latency)
        m_copy = models_df.copy()
        m_copy['score'] = (
            0.5 * m_copy['avg_accuracy'] + 
            0.3 * (1 - m_copy['avg_cost'] / (m_copy['avg_cost'].max() or 1)) + 
            0.2 * (1 - m_copy['avg_latency'] / (m_copy['avg_latency'].max() or 1))
        )
        rec = m_copy.loc[m_copy['score'].idxmax()]
        
        rec_text = f"""
        <b>Recommended Model: {rec['model_name']}</b><br/>
        Based on a weighted analysis of accuracy, cost, and latency, <b>{rec['model_name']}</b> is the optimal 
        choice for production. It achieves an average accuracy of <b>{rec['avg_accuracy']:.1%}</b> with a 
        competitive cost of <b>${rec['avg_cost']:.4f}</b> per evaluation.
        """
        story.append(Paragraph(rec_text, self.styles['CleanBody']))
        story.append(Spacer(1, 0.2*inch))

        # 4. Cost Impact Analysis
        baseline_model = models_df.loc[models_df['avg_cost'].idxmax()]
        if baseline_model['model_name'] != rec['model_name']:
            story.append(Paragraph("Projected Cost Impact", self.styles['SectionHeader']))
            savings = baseline_model['avg_cost'] - rec['avg_cost']
            annual_savings = savings * 100 * 365 # 100 evals/day
            
            savings_text = f"""
            By migrating from <b>{baseline_model['model_name']}</b> (${baseline_model['avg_cost']:.4f}/eval) 
            to <b>{rec['model_name']}</b> (${rec['avg_cost']:.4f}/eval), you can achieve a savings of 
            <b>${savings:.4f}</b> per evaluation.<br/>
            <b>Projected Annual Savings:</b> ${annual_savings:,.2f} (at 100 evals/day).
            """
            # Draw in a subtle green box
            st_table = Table([[Paragraph(savings_text, self.styles['CleanBody'])]], colWidths=[CONTENT_WIDTH])
            st_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
                ('LEFTPADDING', (0,0), (-1,-1), 15),
                ('RIGHTPADDING', (0,0), (-1,-1), 15),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(st_table)
            story.append(Spacer(1, 0.2*inch))

        # 5. Performance Matrix (Table)
        story.append(Paragraph("Performance Matrix", self.styles['SectionHeader']))
        lb_data = [['RANK', 'MODEL', 'AVG ACC', 'BEST ACC', 'COST', 'LATENCY']]
        models_sorted = models_df.sort_values('avg_accuracy', ascending=False)
        for i, (_, row) in enumerate(models_sorted.iterrows()):
            lb_data.append([
                str(i+1), 
                row['model_name'], 
                f"{row['avg_accuracy']:.1%}", 
                f"{row['best_accuracy']:.1%}",
                f"${row['avg_cost']:.4f}", 
                f"{row['avg_latency']:.2f}s"
            ])
        
        lt = Table(lb_data, colWidths=[CONTENT_WIDTH*0.08, CONTENT_WIDTH*0.37, CONTENT_WIDTH*0.14, CONTENT_WIDTH*0.14, CONTENT_WIDTH*0.14, CONTENT_WIDTH*0.13])
        lt.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('LINEBELOW', (0,0), (-1,0), 1, self.text_primary),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('TEXTCOLOR', (0,0), (-1,0), self.text_secondary),
        ]))
        story.append(lt)

        # 6. Visual Analysis
        story.append(PageBreak())
        story.append(Paragraph("Visual Performance Analysis", self.styles['SectionHeader']))
        img = self._create_plotly_image(px.scatter(
            models_df, 
            x='avg_cost', 
            y='avg_accuracy', 
            text='model_name', 
            size='avg_latency',
            title="Cost vs. Accuracy Trade-off (Size = Latency)",
            labels={'avg_cost': 'Avg Cost ($)', 'avg_accuracy': 'Avg Accuracy'}
        ))
        if img: story.append(img)

        doc.build(story)
        self._cleanup()
        return output_path

    def generate_run_detail_report(self, run, evals_df, cats, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=letter, margin=PAGE_MARGIN)
        story = []
        story.append(Paragraph(f"Evaluation Run: {run['model_name']}", self.styles['ReportTitle']))
        story.append(Paragraph(f"Run ID: {run['id']} • Timestamp: {run['timestamp']}", self.styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        summary_data = [[
            self._create_metric_box("Accuracy", f"{run['accuracy']:.1%}"),
            self._create_metric_box("Avg Latency", f"{run['avg_latency']:.2f}s"),
            self._create_metric_box("Total Cost", f"${run['total_cost']:.4f}"),
            self._create_metric_box("Evaluations", str(len(evals_df)))
        ]]
        st_table = Table(summary_data, colWidths=[CONTENT_WIDTH/4]*4)
        st_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), self.bg_light), 
            ('TOPPADDING', (0,0), (-1,-1), 15), 
            ('BOTTOMPADDING', (0,0), (-1,-1), 15)
        ]))
        story.append(st_table)
        
        if cats:
            story.append(Paragraph("Category Performance", self.styles['SectionHeader']))
            c_data = [['CATEGORY', 'COUNT', 'SCORE', 'LATENCY']]
            for c, m in cats.items():
                c_data.append([c, str(m['count']), f"{m['avg_score']:.1%}", f"{m['avg_latency']:.2f}s"])
            ct = Table(c_data, colWidths=[CONTENT_WIDTH*0.4, CONTENT_WIDTH*0.2, CONTENT_WIDTH*0.2, CONTENT_WIDTH*0.2])
            ct.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
                ('LINEBELOW', (0,0), (-1,0), 1, self.text_primary), 
                ('TOPPADDING', (0,0), (-1,-1), 8), 
                ('BOTTOMPADDING', (0,0), (-1,-1), 8), 
                ('ALIGN', (1,0), (-1,-1), 'RIGHT')
            ]))
            story.append(ct)

        doc.build(story)
        self._cleanup()
        return output_path

def generate_model_comparison_pdf(df):
    gen = PDFReportGenerator()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp: path = tmp.name
    gen.generate_model_comparison_report(df, path)
    with open(path, 'rb') as f: b = BytesIO(f.read())
    try: os.unlink(path)
    except: pass
    return b

def generate_run_detail_pdf(run, df, cats):
    gen = PDFReportGenerator()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp: path = tmp.name
    gen.generate_run_detail_report(run, df, cats, path)
    with open(path, 'rb') as f: b = BytesIO(f.read())
    try: os.unlink(path)
    except: pass
    return b