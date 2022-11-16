# Generated by Django 3.2.16 on 2022-11-16 17:00

import core.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('location', '0008_add_enrollment_officer_gql_query_location_right'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerformanceCriteria',
            fields=[
                ('id', models.SmallIntegerField(db_column='ID', primary_key=True, serialize=False)),
                ('date_from', core.fields.DateField(blank=True, db_column='StartDate', null=True)),
                ('date_to', core.fields.DateField(blank=True, db_column='EndDate', null=True)),
                ('promptness', models.IntegerField(db_column='PromptnessInvoiceSubmission')),
                ('degree_of_rejection', models.DecimalField(blank=True, db_column='DegreeofInvoiceRejection', decimal_places=2, max_digits=18, null=True)),
                ('medecine_availability', models.IntegerField(blank=True, db_column='MedecineAvailability', null=True)),
                ('qualified_personnel', models.IntegerField(blank=True, db_column='QualifiedPersonel', null=True)),
                ('garbagecan_availability', models.IntegerField(blank=True, db_column='GarbagecanAvailable', null=True)),
                ('rooms_cleaness', models.IntegerField(blank=True, db_column='RoomCleaness', null=True)),
                ('waste_separation', models.IntegerField(blank=True, db_column='WasteSeparationSystem', null=True)),
                ('functionals_toilets', models.IntegerField(blank=True, db_column='FunctionalToilets', null=True)),
                ('sterilization_tools', models.IntegerField(blank=True, db_column='SterilizationTools', null=True)),
                ('health_facility', models.ForeignKey(blank=True, db_column='HFID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='location.healthfacility')),
            ],
            options={
                'db_table': 'tblPerformanceCriteria',
                'managed': True,
            },
        ),
    ]