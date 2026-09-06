# Safe public-data source adapter interface.
#
# Add only lawful/public sources here. Each adapter should return normalized
# public records. Do not implement credential collection, private-chat access,
# privacy bypasses, or hidden personal-data extraction.
#
# Example normalized record:
# {
#     "type": "public_group",
#     "title": "...",
#     "username": "...",
#     "url": "...",
#     "source": "..."
# }
