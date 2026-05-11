NOTE_TOML = '''name = "note"
icon = "📝"
body_model = "file(markdown)"

[[fields]]
name = "title"
type = "string"
required = false

[[fields]]
name = "tags"
type = "array"
required = false
'''

CONTACT_TOML = '''name = "contact"
icon = "👤"
body_model = "null"

[[fields]]
name = "name"
type = "string"
required = true

[[fields]]
name = "email"
type = "string"
required = false

[[fields]]
name = "phone"
type = "string"
required = false

[[fields]]
name = "org"
type = "string"
required = false
'''

BOOKMARK_TOML = '''name = "bookmark"
icon = "🔖"
body_model = "null"

[[fields]]
name = "url"
type = "url"
required = true

[[fields]]
name = "title"
type = "string"
required = false

[[fields]]
name = "tags"
type = "array"
required = false
'''

FILE_TOML = '''name = "file"
icon = "📄"
body_model = "file(binary)"

[[fields]]
name = "tags"
type = "array"
required = false
'''
