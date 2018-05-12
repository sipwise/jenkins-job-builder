import io

from jinja2 import nodes
from jinja2.ext import Extension

from jenkins_jobs import formatter, utils


class JJBIncludeRawExtension(Extension):

    tags = set(['jjb_include_raw'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        args = [parser.parse_expression(), nodes.ContextReference()]
        call_block = nodes.CallBlock(
            self.call_method('_render_template', args), [], [], [])
        call_block.set_lineno(lineno)
        return call_block

    def _render_template(self, template_path, context, caller):
        # Use the search path in the Jinja loader to find the template
        template_content, _, _ = self.environment.loader.get_source(
            self.environment, template_path)

        # But don't use Jinja to render it, render it ourselves
        return formatter.deep_format(template_content, context)
