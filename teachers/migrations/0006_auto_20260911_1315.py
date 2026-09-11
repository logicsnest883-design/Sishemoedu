from django.db import migrations


def move_attendance_to_term_3(apps, schema_editor):
    Attendance = apps.get_model("teachers", "Attendance")

    Attendance.objects.filter(
        year=2026,
        term="Term 1",
        week=1,
    ).update(
        term="Term 3"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("teachers", "0005_alter_test_subject_delete_subject"),
    ]

    operations = [
        migrations.RunPython(
            move_attendance_to_term_3,
            migrations.RunPython.noop,
        ),
    ]