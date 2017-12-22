from . import messages, commands, actions


def create_endpoints(plugin):
    messages.create_endpoints(plugin)
    commands.create_endpoints(plugin)
    actions.create_endpoints(plugin)
