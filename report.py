import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class ClassUsageReporter:
    def __init__(self, past_classes_csv, missed_classes_csv, teachers_csv):
        """
        Initialize the reporter with CSV file paths
        
        Args:
            past_classes_csv (str): Path to Past_Classes CSV
            missed_classes_csv (str): Path to Missed_Classes CSV
            teachers_csv (str): Path to Teachers CSV
        """
        self.past_classes = pd.read_csv(past_classes_csv, parse_dates=['created_at', 'start_time', 'end_time', 'date_taken'])
        self.missed_classes = pd.read_csv(missed_classes_csv, parse_dates=['created_at', 'date_missed'])
        self.teachers = pd.read_csv(teachers_csv)
        
    def generate_comprehensive_report(self, output_dir='reports'):
        """
        Generate a comprehensive report on class usage
        
        Args:
            output_dir (str): Directory to save report files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate individual reports
        past_classes_report = self._past_classes_analysis()
        missed_classes_report = self._missed_classes_analysis()
        teacher_usage_report = self._teacher_usage_analysis()
        
        # Combine reports
        comprehensive_report = {
            'past_classes': past_classes_report,
            'missed_classes': missed_classes_report,
            'teacher_usage': teacher_usage_report
        }
        
        # Save JSON report
        import json
        with open(os.path.join(output_dir, 'comprehensive_report.json'), 'w') as f:
            json.dump(comprehensive_report, f, indent=4, default=str)
        
        # Generate visualizations
        self._create_visualizations(comprehensive_report, output_dir)
        
        return comprehensive_report
    
    def _past_classes_analysis(self):
        """
        Analyze past classes data
        
        Returns:
            dict: Comprehensive analysis of past classes
        """
        # Total classes
        total_classes = len(self.past_classes)
        
        # Late and on-time classes
        late_classes = len(self.past_classes[self.past_classes['entry_type'] == 'late'])
        on_time_classes = len(self.past_classes[self.past_classes['entry_type'] == 'on_time'])
        
        # Course distribution
        course_distribution = self.past_classes.groupby('course_code').agg({
            'id': 'count',
            'start_time': [
                ('avg_duration', lambda x: (self.past_classes.loc[x.index, 'end_time'] - self.past_classes.loc[x.index, 'start_time']).mean())
            ]
        }).reset_index()
        course_distribution.columns = ['course_code', 'class_count', 'avg_duration']
        course_distribution = course_distribution.sort_values('class_count', ascending=False).head(20)
        
        # Entry type distribution
        entry_type_distribution = self.past_classes['entry_type'].value_counts()
        
        return {
            'total_classes': total_classes,
            'late_classes': late_classes,
            'on_time_classes': on_time_classes,
            'late_percentage': (late_classes / total_classes) * 100 if total_classes > 0 else 0,
            'entry_type_distribution': entry_type_distribution.to_dict(),
            'top_courses': course_distribution.to_dict(orient='records')
        }
    
    def _missed_classes_analysis(self):
        """
        Analyze missed classes data for active teachers
        
        Returns:
            dict: Comprehensive analysis of missed classes
        """
        # Get active teachers (took at least 5 classes)
        active_teachers = self.past_classes.groupby('employee_id').size()
        active_teachers = active_teachers[active_teachers >= 5].index
        
        # Filter missed classes for active teachers
        active_missed_classes = self.missed_classes[self.missed_classes['employee_id'].isin(active_teachers)]
        
        return {
            'total_missed_classes': len(active_missed_classes),
            'makeup_classes': active_missed_classes['makeup_done'].sum(),
            'makeup_percentage': (active_missed_classes['makeup_done'].sum() / len(active_missed_classes)) * 100 
                if len(active_missed_classes) > 0 else 0,
            'missed_classes_by_course': active_missed_classes['course_code'].value_counts().to_dict()
        }
    
    def _teacher_usage_analysis(self):
        """
        Analyze teacher platform usage
    
        Returns:
            dict: Comprehensive analysis of teacher platform usage
        """
        # Ensure employee_id is the same type in both DataFrames
        # Convert to string to ensure consistency
        self.past_classes['employee_id'] = self.past_classes['employee_id'].astype(str)
        self.teachers['employee_id'] = self.teachers['employee_id'].astype(str)
    
        # Count classes per teacher
        teacher_usage = self.past_classes.groupby('employee_id').agg({
            'id': 'count',
            'entry_type': lambda x: (x == 'late').sum()
        }).reset_index()
        teacher_usage.columns = ['employee_id', 'total_classes', 'late_classes']
    
        # Merge with teacher details
        teacher_usage = teacher_usage.merge(
            self.teachers[['employee_id', 'first_name', 'last_name']], 
            on='employee_id', 
            how='left'
        )
    
        # Calculate late class percentage
        teacher_usage['late_percentage'] = (teacher_usage['late_classes'] / teacher_usage['total_classes']) * 100
    
        # Categorize usage
        def categorize_usage(classes):
            if classes == 0:
                return '0 Classes'
            elif classes <= 10:
                return '1-10 Classes'
            elif classes <= 50:
                return '11-50 Classes'
            elif classes <= 100:
                return '51-100 Classes'
            else:
                return '100+ Classes'
    
        teacher_usage['usage_category'] = teacher_usage['total_classes'].apply(categorize_usage)
    
        # Usage breakdown
        usage_breakdown = teacher_usage['usage_category'].value_counts()
    
        return {
            'total_teachers_used': len(teacher_usage),
            'usage_breakdown': usage_breakdown.to_dict(),
            'top_teachers': teacher_usage.nlargest(10, 'total_classes').to_dict(orient='records'),
            'teachers_with_most_late_classes': teacher_usage.nlargest(10, 'late_classes').to_dict(orient='records')
        }
    
    def _create_visualizations(self, report, output_dir):
        """
        Create visualizations for the report
        
        Args:
            report (dict): Comprehensive report data
            output_dir (str): Directory to save visualizations
        """
        plt.figure(figsize=(16, 10))
        
        # Teacher Usage Breakdown Pie Chart
        plt.subplot(2, 2, 1)
        usage_breakdown = report['teacher_usage']['usage_breakdown']
        plt.pie(
            list(usage_breakdown.values()), 
            labels=list(usage_breakdown.keys()), 
            autopct='%1.1f%%'
        )
        plt.title('Teacher Platform Usage')
        
        # Course Distribution Bar Chart
        plt.subplot(2, 2, 2)
        courses = pd.DataFrame(report['past_classes']['top_courses'])
        sns.barplot(x='course_code', y='class_count', data=courses)
        plt.title('Top Courses by Class Count')
        plt.xticks(rotation=45)
        plt.xlabel('Course Code')
        plt.ylabel('Number of Classes')
        
        # Entry Type Distribution Pie Chart
        plt.subplot(2, 2, 3)
        entry_types = report['past_classes']['entry_type_distribution']
        plt.pie(
            list(entry_types.values()), 
            labels=list(entry_types.keys()), 
            autopct='%1.1f%%'
        )
        plt.title('Class Entry Types')
        
        # Late Classes by Top Courses
        plt.subplot(2, 2, 4)
        late_courses = self.past_classes[self.past_classes['entry_type'] == 'late']
        late_course_dist = late_courses['course_code'].value_counts().head(10)
        sns.barplot(x=late_course_dist.index, y=late_course_dist.values)
        plt.title('Top Courses with Late Classes')
        plt.xticks(rotation=45)
        plt.xlabel('Course Code')
        plt.ylabel('Number of Late Classes')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'usage_visualization.png'))
        plt.close()

def main():
    # CSV file paths (update these to match your file names)
    PAST_CLASSES_CSV = 'Past_Classes.csv'
    MISSED_CLASSES_CSV = 'Missed_Classes.csv'
    TEACHERS_CSV = 'Teachers.csv'
    
    # Create reporter and generate report
    reporter = ClassUsageReporter(
        past_classes_csv=PAST_CLASSES_CSV,
        missed_classes_csv=MISSED_CLASSES_CSV,
        teachers_csv=TEACHERS_CSV
    )
    
    report = reporter.generate_comprehensive_report()
    
    # Pretty print the report
    import json
    print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()