import hashlib
import platform

system = platform.system()
node = platform.node()

total = str(dict(system=system, node=node))

platform_hash_digest = hashlib.md5(total.encode('utf-8')).hexdigest()

print(repr(platform_hash_digest))
