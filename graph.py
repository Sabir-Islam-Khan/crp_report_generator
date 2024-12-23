import json
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

# print(plt.style.available)
# exit()

# Create output directory
OUTPUT_DIR = 'graphs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read JSON data
with open('reports/comprehensive_report.json', 'r') as file:
    data = json.load(file)

def setup_plot_style():
    plt.style.use('seaborn-v0_8-pastel')
    sns.set_palette("husl")

def save_plot(filename):
    plt.tight_layout()
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

def plot_class_distribution():
    labels = ['On Time', 'Late', 'Extra Class']
    values = [
        data['past_classes']['entry_type_distribution']['on_time'],
        data['past_classes']['entry_type_distribution']['late'],
        data['past_classes']['entry_type_distribution']['EXTRA_CLASS']
    ]
    
    plt.figure(figsize=(10, 8))
    colors = ['#2ecc71', '#e74c3c', '#3498db']  # green, red, blue
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors)
    plt.title('Distribution of Class Types')
    save_plot('class_distribution.png')

def plot_top_courses():
    courses_df = pd.DataFrame(data['past_classes']['all_courses'])
    top_10 = courses_df.nlargest(10, 'class_count')
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_10, x='course_code', y='class_count')
    plt.xticks(rotation=45, ha='right')
    plt.title('Top 10 Courses by Number of Classes')
    plt.xlabel('Course Code')
    plt.ylabel('Number of Classes')
    save_plot('top_10_courses.png')

def plot_course_durations():
    courses_df = pd.DataFrame(data['past_classes']['all_courses'])
    
    # Separate theory and lab courses
    theory_courses = courses_df[courses_df['class_type'] == 'theory'].nlargest(10, 'avg_duration')
    lab_courses = courses_df[courses_df['class_type'] == 'lab'].nlargest(10, 'avg_duration')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Theory courses plot
    sns.barplot(data=theory_courses, x='course_code', y='avg_duration', ax=ax1)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
    ax1.set_title('Top 10 Theory Courses by Average Duration')
    ax1.set_xlabel('Course Code')
    ax1.set_ylabel('Average Duration (minutes)')
    
    # Lab courses plot
    sns.barplot(data=lab_courses, x='course_code', y='avg_duration', ax=ax2)
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
    ax2.set_title('Top 10 Lab Courses by Average Duration')
    ax2.set_xlabel('Course Code')
    ax2.set_ylabel('Average Duration (minutes)')
    
    save_plot('course_durations.png')

def plot_ontime_vs_late():
    total = data['past_classes']['total_classes']
    ontime = data['past_classes']['on_time_classes']
    late = data['past_classes']['late_classes']
    
    plt.figure(figsize=(8, 6))
    plt.bar(['On Time', 'Late'], [ontime, late])
    plt.title('On-Time vs Late Classes')
    plt.ylabel('Number of Classes')
    save_plot('ontime_vs_late.png')

def plot_top_teachers():
    teachers_df = pd.DataFrame(data['teacher_usage']['all_teachers_metrics'])
    top_10_teachers = teachers_df.nlargest(10, 'total_classes')
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_10_teachers, x='first_name', y='total_classes')
    plt.xticks(rotation=45, ha='right')
    plt.title('Top 10 Teachers by Total Classes')
    plt.xlabel('Teacher Name')
    plt.ylabel('Number of Classes')
    save_plot('top_teachers.png')

def plot_most_missed_classes():
    teachers_df = pd.DataFrame(data['missed_classes']['teachers_with_most_missed'])
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=teachers_df, x='first_name', y='missed_count')
    plt.xticks(rotation=45, ha='right')
    plt.title('Teachers with Most Missed Classes')
    plt.xlabel('Teacher Name')
    plt.ylabel('Number of Missed Classes')
    save_plot('most_missed_classes.png')

def generate_teacher_table():
    teachers_df = pd.DataFrame(data['teacher_usage']['all_teachers_metrics'])
    teachers_df = teachers_df.sort_values('total_classes', ascending=False)
    
    # Calculate totals
    total_row = ['TOTAL',
                 f"{teachers_df['total_classes'].sum():.0f}",
                 f"{teachers_df['late_classes'].sum():.0f}", 
                 f"{teachers_df['missed_classes'].sum():.0f}",
                 f"{(teachers_df['late_classes'].sum() / teachers_df['total_classes'].sum() * 100):.1f}%"]
    
    # Prepare data for PDF
    data_rows = []
    headers = ['#', 'Teacher Name', 'Total Classes', 'Late Classes', 'Missed Classes', 'Late %']
    data_rows.append(headers)
    
    for idx, row in teachers_df.iterrows():
        data_rows.append([
            str(len(data_rows)),  # Add index number
            f"{row['first_name']} {row['last_name']}",
            f"{row['total_classes']:.0f}",
            f"{row['late_classes']:.0f}",
            f"{row['missed_classes']:.0f}",
            f"{row['late_percentage']:.1f}%"
        ])
    data_rows.append(['', 'TOTAL',  # Empty string for index in total row
                     f"{teachers_df['total_classes'].sum():.0f}",
                     f"{teachers_df['late_classes'].sum():.0f}", 
                     f"{teachers_df['missed_classes'].sum():.0f}",
                     f"{(teachers_df['late_classes'].sum() / teachers_df['total_classes'].sum() * 100):.1f}%"])

    # Create PDF
    pdf_path = os.path.join(OUTPUT_DIR, 'teacher_metrics.pdf')
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Create table
    table = Table(data_rows, repeatRows=1)
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Bold for totals
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ]))
    
    # Build PDF
    doc.build([table])
    print(f"Teacher metrics PDF generated at: {pdf_path}")

def generate_final_report():
    pdf_path = os.path.join(OUTPUT_DIR, 'final_report.pdf')
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        spaceAfter=40,
        alignment=1,
        textColor=colors.HexColor('#2E5A88')
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#333333')
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=20,
        textColor=colors.HexColor('#2E5A88')
    )
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        alignment=1,
        textColor=colors.HexColor('#666666')
    )
    
    # Create story (content)
    story = []
    
    # Add some space at the top
    story.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Main title with blue color
    story.append(Paragraph("CRP USAGE REPORT", title_style))
    
    # Horizontal line
    story.append(Paragraph("<hr width='50%' color='#2E5A88'/>", styles['Normal']))
    
    # Date range with better formatting
    story.append(Paragraph("<br/>", styles['Normal']))
    story.append(Paragraph("Analysis Period", subtitle_style))
    story.append(Paragraph("16 October 2024 - 12 December 2024", meta_style))
    story.append(Paragraph("(1 month 27 days)", meta_style))
    
    # Report metadata
    story.append(Paragraph("<br/><br/>", styles['Normal']))
    story.append(Paragraph("Report Information", subtitle_style))
    story.append(Paragraph(f"Generated on: 12 December 2024 | 9:01 PM", meta_style))
    current_time = datetime.now().strftime("%d %B %Y | %I:%M %p")
    story.append(Paragraph(f"Generated on: {current_time}", meta_style))
    story.append(Paragraph("Generated By: CRP Report Generator v1.0", meta_style))
    story.append(Paragraph("Report Type: Comprehensive Analysis", meta_style))
    
    # Add page break after title page
    story.append(PageBreak())
    
    # Add Summary Section
    story.append(Paragraph("Executive Summary", section_style))
    
    # Overall Statistics
    total_classes = data['past_classes']['total_classes']
    total_teachers = data['teacher_usage']['total_summary']['total_teachers']
    
    # Define summary style with better spacing
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceBefore=12,
        spaceAfter=12,
        bulletIndent=20,
        leftIndent=20
    )
    
    # Format summary sections with proper ReportLab formatting
    overall_stats = f"""
<para>
<b>Overall Statistics</b><br/>

• Total Classes Conducted: {total_classes}<br/>
• Total Teachers: {total_teachers}<br/>
• On-time Classes: {data['past_classes']['on_time_classes']} ({data['past_classes']['entry_type_distribution']['on_time']} classes)<br/>
• Late Classes: {data['past_classes']['late_classes']} ({data['past_classes']['entry_type_distribution']['late']} classes)<br/>
• Extra Classes: {data['past_classes']['entry_type_distribution']['EXTRA_CLASS']} classes<br/>

<br/><b>Course Analysis</b><br/>

• Most Active Course: {data['past_classes']['all_courses'][0]['course_code']} with {data['past_classes']['all_courses'][0]['class_count']} classes<br/>
• Average Theory Class Duration: {data['past_classes']['average_durations'].get('theory', 0):.1f} minutes<br/>
• Average Lab Class Duration: {data['past_classes']['average_durations'].get('lab', 0):.1f} minutes<br/>

<br/><b>Course Analysis</b><br/>

• Most Active Course: {data['past_classes']['all_courses'][0]['course_code']} with {data['past_classes']['all_courses'][0]['class_count']} classes<br/>
• Average Course Duration: {sum(c['avg_duration'] for c in data['past_classes']['all_courses'][:10])/10:.1f} minutes for top 10 courses<br/>

<br/><b>Teacher Performance</b><br/>

• Total Missed Classes: {data['missed_classes']['total_missed_classes']}<br/>
• Top Performing Teacher: {data['teacher_usage']['all_teachers_metrics'][0]['first_name']} {data['teacher_usage']['all_teachers_metrics'][0]['last_name']} with {data['teacher_usage']['all_teachers_metrics'][0]['total_classes']} classes<br/>
• Average Late Percentage: {data['past_classes']['late_percentage']:.1f}%<br/>

<br/><b>Key Findings</b><br/>

• {data['past_classes']['late_percentage']:.1f}% of all classes started late<br/>
• {len([c for c in data['past_classes']['all_courses'] if c['class_count'] > 100])} courses had more than 100 classes<br/>
• Top 10 teachers conducted {sum(t['total_classes'] for t in data['teacher_usage']['all_teachers_metrics'][:10])} classes<br/>
</para>"""

    story.append(Paragraph(overall_stats, summary_style))
    story.append(PageBreak())
    
    # Class Distribution Analysis
    story.append(Paragraph("Class Distribution Analysis", section_style))
    img_path = os.path.join(OUTPUT_DIR, 'class_distribution.png')
    img = Image(img_path, width=300, height=240)
    story.append(img)
    
    img_path = os.path.join(OUTPUT_DIR, 'ontime_vs_late.png')
    img = Image(img_path, width=300, height=240)
    story.append(img)
    story.append(PageBreak())
    
    # Daily Class Trend on separate page
    story.append(Paragraph("Daily Class Trend", section_style))
    img_path = os.path.join(OUTPUT_DIR, 'daily_classes_trend.png')
    img = Image(img_path, width=450, height=250)
    story.append(img)
    story.append(PageBreak())
    
    # Course Analysis
    story.append(Paragraph("Course Analysis", section_style))
    img_path = os.path.join(OUTPUT_DIR, 'top_10_courses.png')
    img = Image(img_path, width=450, height=250)
    story.append(img)
    
    img_path = os.path.join(OUTPUT_DIR, 'course_durations.png')
    img = Image(img_path, width=450, height=250)
    story.append(img)
    story.append(PageBreak())
    
    # Teacher Performance
    story.append(Paragraph("Teacher Performance Analysis", section_style))
    img_path = os.path.join(OUTPUT_DIR, 'top_teachers.png')
    img = Image(img_path, width=450, height=250)
    story.append(img)
    
    img_path = os.path.join(OUTPUT_DIR, 'most_missed_classes.png')
    img = Image(img_path, width=450, height=250)
    story.append(img)
    story.append(PageBreak())
    
    # Teacher Metrics Table
    story.append(Paragraph("Detailed Teacher Metrics", section_style))
    teachers_df = pd.DataFrame(data['teacher_usage']['all_teachers_metrics'])
    teachers_df = teachers_df.sort_values('total_classes', ascending=False)
    
    data_rows = [['#', 'Teacher Name', 'Total Classes', 'Late Classes', 'Missed Classes', 'Late %']]
    
    for idx, row in teachers_df.iterrows():
        data_rows.append([
            str(len(data_rows)),  # Add index number
            f"{row['first_name']} {row['last_name']}",
            f"{row['total_classes']:.0f}",
            f"{row['late_classes']:.0f}",
            f"{row['missed_classes']:.0f}",
            f"{row['late_percentage']:.1f}%"
        ])
    
    total_row = ['TOTAL',
                 f"{teachers_df['total_classes'].sum():.0f}",
                 f"{teachers_df['late_classes'].sum():.0f}", 
                 f"{teachers_df['missed_classes'].sum():.0f}",
                 f"{(teachers_df['late_classes'].sum() / teachers_df['total_classes'].sum() * 100):.1f}%"]
    data_rows.append(['', 'TOTAL',  # Empty string for index in total row
                     f"{teachers_df['total_classes'].sum():.0f}",
                     f"{teachers_df['late_classes'].sum():.0f}", 
                     f"{teachers_df['missed_classes'].sum():.0f}",
                     f"{(teachers_df['late_classes'].sum() / teachers_df['total_classes'].sum() * 100):.1f}%"])
    
    table = Table(data_rows, repeatRows=1, style=TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5A88')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    
    # Build PDF with page numbers
    doc.build(story)
    print(f"Final report generated at: {pdf_path}")

def generate_all_plots():
    try:
        setup_plot_style()
        plot_class_distribution()
        plot_top_courses()
        plot_course_durations()
        plot_ontime_vs_late()
        plot_top_teachers()
        plot_most_missed_classes()
        generate_teacher_table()
        generate_final_report()  # Add this line
        print(f"All outputs generated successfully in '{OUTPUT_DIR}' directory")
    except Exception as e:
        print(f"Error generating outputs: {str(e)}")

if __name__ == "__main__":
    generate_all_plots()