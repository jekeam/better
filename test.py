try:
    print(0/0)
except Exception as e:
    print(e.__class__.__name__)