import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class ClassUsageReporter:
    def __init__(self, past_classes_csv, missed_classes_csv, teachers_csv):
        self.past_classes = pd.read_csv(past_classes_csv, parse_dates=['created_at', 'start_time', 'end_time', 'date_taken'])
        self.missed_classes = pd.read_csv(missed_classes_csv, parse_dates=['created_at', 'date_missed'])
        self.teachers = pd.read_csv(teachers_csv)
        
        # Convert employee_id to string in all dataframes
        self.past_classes['employee_id'] = self.past_classes['employee_id'].astype(str)
        self.missed_classes['employee_id'] = self.missed_classes['employee_id'].astype(str)
        self.teachers['employee_id'] = self.teachers['employee_id'].astype(str)
        
        # Calculate duration and identify lab classes
        self.past_classes['duration'] = (self.past_classes['end_time'] - self.past_classes['start_time']).dt.total_seconds() / 60
        self._identify_lab_classes()
    
    def _identify_lab_classes(self):
        # First identify by duration
        self.past_classes['class_type'] = self.past_classes['duration'].apply(
            lambda x: 'lab' if x >= 150 else 'theory'  # Using 150 minutes as threshold
        )
        
        # Then check for multiple occurrences
        class_counts = self.past_classes.groupby([
            'date_taken', 'section', 'room_id', 'course_code', 'employee_id'
        ]).size().reset_index(name='count')
        
        # Map the counts back to original dataframe
        self.past_classes = self.past_classes.merge(
            class_counts,
            on=['date_taken', 'section', 'room_id', 'course_code', 'employee_id'],
            how='left'
        )
        
        # Update class type if multiple occurrences found
        self.past_classes.loc[self.past_classes['count'] >= 2, 'class_type'] = 'lab'
    
    def _past_classes_analysis(self):
        total_classes = len(self.past_classes)
        late_classes = len(self.past_classes[self.past_classes['entry_type'] == 'late'])
        on_time_classes = len(self.past_classes[self.past_classes['entry_type'] == 'on_time'])
        
        # Separate analysis for theory and lab classes
        course_stats = self.past_classes.groupby(['course_code', 'class_type']).agg({
            'id': 'count',
            'duration': 'mean'
        }).reset_index()
        
        course_stats.columns = ['course_code', 'class_type', 'class_count', 'avg_duration']
        course_stats = course_stats.sort_values(['class_type', 'class_count'], ascending=[True, False])
        
        entry_type_dist = self.past_classes['entry_type'].value_counts()
        
        # Calculate average durations by class type
        avg_durations = self.past_classes.groupby('class_type')['duration'].mean().to_dict()
        
        return {
            'total_classes': total_classes,
            'late_classes': late_classes,
            'on_time_classes': on_time_classes,
            'late_percentage': (late_classes / total_classes) * 100 if total_classes > 0 else 0,
            'entry_type_distribution': {
                'on_time': entry_type_dist.get('on_time', 0),
                'late': entry_type_dist.get('late', 0),
                'EXTRA_CLASS': entry_type_dist.get('extra', 0)
            },
            'all_courses': course_stats.to_dict(orient='records'),
            'average_durations': avg_durations
        }
    
    def _missed_classes_analysis(self):
        teacher_missed = self.missed_classes.merge(
            self.teachers[['employee_id', 'first_name', 'last_name']],
            on='employee_id',
            how='left'
        )
        
        teachers_with_most_missed = teacher_missed.groupby(
            ['employee_id', 'first_name', 'last_name']
        )['id'].count().reset_index(name='missed_count')
        
        teachers_with_most_missed = teachers_with_most_missed.sort_values(
            'missed_count', ascending=False
        )
        
        return {
            'total_missed_classes': len(self.missed_classes),
            'teachers_with_most_missed': teachers_with_most_missed.to_dict(orient='records')
        }
    
    def _teacher_usage_analysis(self):
        teacher_metrics = self.past_classes.merge(
            self.teachers[['employee_id', 'first_name', 'last_name']],
            on='employee_id',
            how='left'
        )
        
        teacher_stats = teacher_metrics.groupby(
            ['employee_id', 'first_name', 'last_name']
        ).agg({
            'id': 'count',
            'entry_type': lambda x: (x == 'late').sum()
        }).reset_index()
        
        teacher_stats.columns = ['employee_id', 'first_name', 'last_name', 'total_classes', 'late_classes']
        
        missed_counts = self.missed_classes.groupby('employee_id')['id'].count().reset_index(name='missed_classes')
        teacher_stats = teacher_stats.merge(missed_counts, on='employee_id', how='left')
        teacher_stats['missed_classes'] = teacher_stats['missed_classes'].fillna(0)
        
        teacher_stats['late_percentage'] = (teacher_stats['late_classes'] / teacher_stats['total_classes']) * 100
        
        return {
            'total_summary': {
                'total_teachers': len(teacher_stats)
            },
            'all_teachers_metrics': teacher_stats.sort_values('total_classes', ascending=False).to_dict(orient='records')
        }
    
    def generate_comprehensive_report(self, output_dir='reports'):
        os.makedirs(output_dir, exist_ok=True)
        
        report = {
            'past_classes': self._past_classes_analysis(),
            'missed_classes': self._missed_classes_analysis(),
            'teacher_usage': self._teacher_usage_analysis()
        }
        
        with open(os.path.join(output_dir, 'comprehensive_report.json'), 'w') as f:
            import json
            json.dump(report, f, indent=4, default=str)
        
        return report

if __name__ == "__main__":
    PAST_CLASSES_CSV = 'Past_Classes.csv'
    MISSED_CLASSES_CSV = 'Missed_Classes.csv'
    TEACHERS_CSV = 'Teachers.csv'
    
    reporter = ClassUsageReporter(
        past_classes_csv=PAST_CLASSES_CSV,
        missed_classes_csv=MISSED_CLASSES_CSV,
        teachers_csv=TEACHERS_CSV
    )
    report = reporter.generate_comprehensive_report()