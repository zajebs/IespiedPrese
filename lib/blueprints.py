def register_blueprints(app):
    blueprint_modules = [
        'account',
        'auth',
        'downloads',
        'index',
        'plans',
        'products',
        'contacts',
        'updatable'
    ]
    
    for module_name in blueprint_modules:
        module = __import__(f'routes.{module_name}', fromlist=[f'{module_name}_bp'])
        blueprint = getattr(module, f'{module_name}_bp')
        app.register_blueprint(blueprint)