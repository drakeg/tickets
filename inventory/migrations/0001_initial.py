# Generated by Django 2.0.3 on 2018-04-08 02:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cluster_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Operating_System',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('os_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server_name', models.CharField(max_length=50)),
                ('pub_date', models.DateTimeField(verbose_name='date_published')),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Cluster')),
                ('os', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Operating_System')),
            ],
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendor_name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='server',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Vendor'),
        ),
    ]
