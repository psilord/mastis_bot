
# Some idiotic python introspection stuff for when authors don't write
# documentation about the classes their API creates.

def get_methods(obj):
	object_methods = [method_name for method_name in dir(obj)
						if callable(getattr(obj, method_name))]
	return object_methods

def get_attributes(obj):
	return dir(obj)

def introspect(msg, obj):
	try:
		print(f"{msg} attributes: {get_attributes(obj)}")
	except:
		print(f"{msg} attributes: Not iterable. Sorry.")
		os.exit(1)

	try:
		print(f"{msg} methods: {get_methods(obj)}")
	except:
		print(f"{msg} methods: Not iterable. Sorry.")
		os.exit(1)
