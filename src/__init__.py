import json

with open("/home/ubuntu/.bat/conf.json") as f:
  CONFIG = json.loads(f.read())
