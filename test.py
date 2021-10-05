import html


def escape_html(text):
  return html.escape(text)

rawtext = "Hi <: "
escaped = escape_html(rawtext)
print(escaped)
