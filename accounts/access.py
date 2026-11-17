"""Read-only access summaries; route decorators remain the enforcement boundary."""
from .roles import ROLE_PERMISSIONS


CAPABILITIES = (
    ('Read tickets', ('issues.view_issue',), 'All tickets, including assigned queues.'),
    ('Create tickets', ('issues.view_issue', 'issues.add_issue', 'issues.view_priority'), ''),
    ('Triage tickets', ('issues.view_issue', 'issues.change_issue', 'issues.view_priority'),
     'Change status, assignment and priority.'),
    ('Read projects', ('projects.view_project',), 'All projects.'),
    ('Create projects', ('projects.view_project', 'projects.add_project'), ''),
    ('Read systems', ('inventory.view_server',), 'All inventory systems.'),
    ('Add systems', ('inventory.view_server', 'inventory.add_server',
                     'inventory.view_operating_system', 'inventory.view_vendor', 'inventory.view_cluster'), ''),
    ('Add vendors', ('inventory.view_vendor', 'inventory.add_vendor'), ''),
    ('Read knowledge', ('knowledgebase.view_article',), 'All articles.'),
    ('Publish knowledge', ('knowledgebase.view_article', 'knowledgebase.add_article'), ''),
    ('Publish from a ticket', ('issues.view_issue', 'knowledgebase.view_article', 'knowledgebase.add_article'), ''),
    ('Edit knowledge', ('knowledgebase.view_article', 'knowledgebase.change_article'),
     'Also requires authorship or staff status for the selected article.'),
    ('Delete knowledge', ('knowledgebase.view_article', 'knowledgebase.delete_article'),
     'Also requires authorship or staff status; deletion uses a protected POST.'),
)


def access_summary(user):
    return [{'label': label, 'allowed': user.has_perms(grants), 'note': note}
            for label, grants, note in CAPABILITIES]


def group_summary(group):
    actual = {f'{p.content_type.app_label}.{p.codename}' for p in group.permissions.all()}
    expected = ROLE_PERMISSIONS.get(group.name)
    return {
        'group': group,
        'is_default': expected is not None,
        'capabilities': [{'label': label, 'allowed': set(grants) <= actual, 'note': note}
                         for label, grants, note in CAPABILITIES],
        'missing': sorted(expected - actual) if expected is not None else [],
        'additional': sorted(actual - expected) if expected is not None else [],
        'grants': sorted(actual),
    }
