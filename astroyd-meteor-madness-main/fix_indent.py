with open('app/api/v1/endpoints/simulation.py', 'r') as f:
    content = f.read()
with open('app/api/v1/endpoints/simulation.py', 'w') as f:
    f.write(content.expandtabs(4))
