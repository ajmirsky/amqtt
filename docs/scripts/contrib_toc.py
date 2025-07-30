from hashlib import sha256
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def generate_contrib_index():
    doc_root = Path(__file__).parent.parent.resolve()

    template_file = doc_root / 'plugins' / 'contrib.md.jinja'
    contrib_plugins_dir = doc_root / 'plugins/contrib'
    output_file = doc_root / 'dist' / 'contrib.md'

    with open(output_file, "r") as f:
        old_content = f.read()

        doc_root = Path(__file__).parent.parent.resolve()

        environment = Environment(loader=FileSystemLoader(doc_root / "plugins"))
        template = environment.get_template("contrib.md.jinja")

        dist_root = doc_root / "dist"


        files = sorted(contrib_plugins_dir.glob("*.md"))

        plugin_list = [ file.name for file in files ]

        content = template.render(
            plugins=plugin_list,
        )

        if sha256(old_content.encode()).digest() == sha256(content.encode()).digest():
            print(">>>> generated file not changed")
            return  # no change

    print(">>>>>> generating new file")

    fn_contrib = dist_root / "contrib.md"

    with fn_contrib.open(mode="w", encoding="utf-8") as message:
        message.write(content)

generate_contrib_index()
