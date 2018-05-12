import io

from jinja2 import nodes
from jinja2.ext import Extension

from jenkins_jobs import formatter, local_yaml, utils


class TraditionalJJBTemplateExtension(Extension):

    tags = set(['include_jjb'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        args = [parser.parse_expression(),
                nodes.ContextReference()]
        return nodes.CallBlock(self.call_method('_render_template', args),
                               [], [], []).set_lineno(lineno)

    def _render_template(self, template_path, context, caller):
        # Use the search path in the Jinja environment to find the template
        template = self.environment.select_template([template_path])

        # But don't use Jinja to render it, read it in ourselves
        with io.open(template.filename, 'r', encoding='utf-8') as fp:
            data = utils.wrap_stream(fp).read()
        return formatter.deep_format(data.decode('utf-8'), context)
