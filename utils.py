"""
Utility script for common administrative tasks.
Usage: python utils.py [command] [options]
"""
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal, Student, Attendance, Base, engine
from backend.logger import logger
from shared.face_recognition_service import FaceRecognitionService


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("⚠️  WARNING: This will delete all data!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() == 'yes':
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Creating fresh tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database reset successfully!")
        logger.info("Database reset completed")
    else:
        print("❌ Operation cancelled")


def list_students():
    """List all registered students."""
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        
        if not students:
            print("No students registered yet.")
            return
        
        print(f"\n📚 Total Students: {len(students)}\n")
        print(f"{'ID':<5} {'Name':<30} {'Image Path':<50}")
        print("-" * 85)
        
        for student in students:
            print(f"{student.id:<5} {student.name:<30} {student.image_path:<50}")
    finally:
        db.close()


def export_attendance(output_file: str = "attendance_export.csv"):
    """Export all attendance records to CSV."""
    import csv
    from datetime import datetime
    
    db = SessionLocal()
    try:
        records = db.query(Attendance).all()
        students = {s.id: s.name for s in db.query(Student).all()}
        
        if not records:
            print("No attendance records to export.")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Student ID', 'Student Name', 'Timestamp'])
            
            for record in records:
                writer.writerow([
                    record.id,
                    record.student_id,
                    students.get(record.student_id, 'Unknown'),
                    record.timestamp.isoformat()
                ])
        
        print(f"✅ Exported {len(records)} records to {output_file}")
        logger.info(f"Exported attendance records to {output_file}")
    finally:
        db.close()


def rebuild_face_encodings():
    """Rebuild face encodings from registered student images."""
    db = SessionLocal()
    service = FaceRecognitionService()
    
    try:
        students = db.query(Student).all()
        
        if not students:
            print("No students registered.")
            return
        
        print(f"Rebuilding face encodings for {len(students)} students...")
        success_count = 0
        
        for student in students:
            if os.path.exists(student.image_path):
                if service.add_known_face(student.name, student.image_path):
                    success_count += 1
                    print(f"✅ {student.name}")
                else:
                    print(f"❌ {student.name} - Failed to encode face")
            else:
                print(f"⚠️  {student.name} - Image file not found")
        
        # Save encodings
        if success_count > 0:
            service.save_encodings("face_encodings.pkl")
            print(f"\n✅ Successfully rebuilt {success_count}/{len(students)} face encodings")
            logger.info(f"Rebuilt face encodings for {success_count} students")
        else:
            print("\n❌ No face encodings were generated")
    finally:
        db.close()


def cleanup_temp_files():
    """Clean up temporary files."""
    temp_patterns = ['temp_*.jpg', 'temp_*.png', 'temp_*.jpeg']
    cleaned = 0
    
    for pattern in temp_patterns:
        for temp_file in Path('.').glob(pattern):
            try:
                temp_file.unlink()
                cleaned += 1
                print(f"🗑️  Removed {temp_file}")
            except Exception as e:
                print(f"❌ Failed to remove {temp_file}: {e}")
    
    print(f"\n✅ Cleaned up {cleaned} temporary file(s)")


def show_stats():
    """Show system statistics."""
    db = SessionLocal()
    try:
        student_count = db.query(Student).count()
        attendance_count = db.query(Attendance).count()
        
        print("\n📊 System Statistics")
        print("=" * 40)
        print(f"Total Students:    {student_count}")
        print(f"Total Attendance:  {attendance_count}")
        
        if student_count > 0:
            avg_attendance = attendance_count / student_count
            print(f"Avg per Student:   {avg_attendance:.2f}")
        
        # Database size
        if os.path.exists('attendance.db'):
            db_size = os.path.getsize('attendance.db') / 1024  # KB
            print(f"Database Size:     {db_size:.2f} KB")
        
        print("=" * 40 + "\n")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Student Attendance System - Utility Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  reset-db              Reset the database (WARNING: deletes all data)
  list-students         List all registered students
  export-attendance     Export attendance records to CSV
  rebuild-encodings     Rebuild face encodings from student images
  cleanup               Remove temporary files
  stats                 Show system statistics
  
Examples:
  python utils.py list-students
  python utils.py export-attendance
  python utils.py stats
        """
    )
    
    parser.add_argument(
        'command',
        choices=['reset-db', 'list-students', 'export-attendance', 
                'rebuild-encodings', 'cleanup', 'stats'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='attendance_export.csv',
        help='Output file for export-attendance command'
    )
    
    args = parser.parse_args()
    
    print("\n🔧 Student Attendance System - Utilities\n")
    
    if args.command == 'reset-db':
        reset_database()
    elif args.command == 'list-students':
        list_students()
    elif args.command == 'export-attendance':
        export_attendance(args.output)
    elif args.command == 'rebuild-encodings':
        rebuild_face_encodings()
    elif args.command == 'cleanup':
        cleanup_temp_files()
    elif args.command == 'stats':
        show_stats()


if __name__ == "__main__":
    main()
