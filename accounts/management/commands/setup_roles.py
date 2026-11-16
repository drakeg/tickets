from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.roles import ROLE_PERMISSIONS


class Command(BaseCommand):
    help = 'Create team groups and add default permissions without changing users or removing grants.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show planned grants without saving.')

    @transaction.atomic
    def handle(self, *args, **options):
        permissions = {
            f'{permission.content_type.app_label}.{permission.codename}': permission
            for permission in Permission.objects.select_related('content_type')
        }
        required = set().union(*ROLE_PERMISSIONS.values())
        missing = required - permissions.keys()
        if missing:
            raise CommandError('Run migrations before role setup. Missing permissions: ' + ', '.join(sorted(missing)))

        for name, grants in ROLE_PERMISSIONS.items():
            if options['dry_run']:
                self.stdout.write(f'{name}: would ensure {len(grants)} default permissions')
            else:
                group, created = Group.objects.get_or_create(name=name)
                group.permissions.add(*(permissions[key] for key in sorted(grants)))
                self.stdout.write(f'{name}: {"created" if created else "updated"}; {len(grants)} default permissions ensured')
        self.stdout.write('Users, memberships, staff flags and existing permission grants are unchanged.')
