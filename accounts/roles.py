"""Named group defaults; application route enforcement is tracked separately."""


def permissions_for(app, models, actions):
    return {f'{app}.{action}_{model}' for model in models for action in actions}


INVENTORY_MODELS = ('server', 'operating_system', 'vendor', 'cluster')
READ_INVENTORY = permissions_for('inventory', INVENTORY_MODELS, ('view',))
TICKET_READ = {'issues.view_issue', 'issues.view_priority'}
KNOWLEDGE = {'knowledgebase.view_article', 'knowledgebase.add_article'}

ROLE_PERMISSIONS = {
    'Infrastructure Team': (
        permissions_for('inventory', INVENTORY_MODELS, ('view', 'add', 'change'))
        | TICKET_READ | {'issues.change_issue', 'projects.view_project'} | KNOWLEDGE
    ),
    'Help Desk': (
        READ_INVENTORY | TICKET_READ | {'issues.add_issue', 'issues.change_issue'}
        | {'projects.view_project'} | KNOWLEDGE
    ),
    'Project Manager': (
        permissions_for('projects', ('project', 'task'), ('view', 'add', 'change'))
        | TICKET_READ | KNOWLEDGE
    ),
}
