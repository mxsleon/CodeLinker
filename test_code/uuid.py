import hashlib

sha256_hash = hashlib.new('sha256')
sha256_hash.update(b'mxs123')
print(sha256_hash.hexdigest())