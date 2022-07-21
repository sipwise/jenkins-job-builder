from dataclasses import dataclass


job_contents_keys = {
    # Same as for macros.
    "parameters",
    "properties",
    "builders",
    "wrappers",
    "triggers",
    "publishers",
    "scm",
    "pipeline-scm",
    "reporters",
    # General.
    "node",
    "jdk",
    "actions",
    "disabled",
    "display-name",
    "block-downstream",
    "block-upstream",
    "auth-token",
    "concurrent",
    "workspace",
    "child-workspace",
    "quiet-period",
    "retry-count",
    "logrotate",
    "raw",
    # Builders.
    "prebuilders",
    "postbuilders",
    # HipChat.
    "hipchat",
    # Notificatoins.
    "notifications",
    # project Flow.
    "dsl",
    "needs-workspace",
    "dsl-file",
    # GithubOrganization.
    "prune-dead-branches",
    "days-to-keep",
    "number-to-keep",
    "periodic-folder-trigger",
    "github-org",
    "script-path",
    # Matrix.
    "execution-strategy",
    "yaml-strategy",
    "p4-strategy",
    "axes",
    # Maven.
    "maven",
    "per-module-email",
    # WorkflowMultiBranch.
    "sandbox",
    "script-id",
    "script-path",
    "prune-dead-branches",
    "days-to-keep",
    "number-to-keep",
    "periodic-folder-trigger",
    # Pipeline.
    "dsl",
    "sandbox",
    # project Workflow.
    "dsl",
    "sandbox",
}

view_contents_keys = {
    # Common.
    "filter-executors",
    "filter-queue",
    # All
    # <nothing>
    # List.
    "job-name",
    "job-filters",
    "width",
    "alignment",
    "columns",
    "regex",
    "recurse",
    # Sectioned.
    "sections",
    # SectionedText.
    "width",
    "alignment",
    "text",
    "style",
    # DeliveryPipeline.
    "aggregated-changes-grouping-pattern",
    "allow-abort",
    "allow-manual-triggers",
    "allow-pipeline-start",
    "allow-rebuild",
    "link-relative",
    "link-to-console-log",
    "max-number-of-visible-pipelines",
    "name",
    "no-of-columns",
    "no-of-pipelines",
    "paging-enabled",
    "show-absolute-date-time",
    "show-aggregated-changes",
    "show-aggregated-pipeline",
    "show-avatars",
    "show-changes",
    "show-description",
    "show-promotions",
    "show-static-analysis-results",
    "show-test-results",
    "show-total-build-time",
    "update-interval",
    "sorting",
    "components",
    "regexps",
    # Nested.
    "views",
    "default-view",
    "columns",
    # Pipeline.
    "first-job",
    "name",
    "no-of-displayed-builds",
    "title",
    "link-style",
    "css-Url",
    "latest-job-only",
    "manual-trigger",
    "show-parameters",
    "parameters-in-headers",
    "start-with-parameters",
    "refresh-frequency",
    "definition-header",
}


def split_contents_params(data, contents_keys):
    contents = {key: value for key, value in data.items() if key in contents_keys}
    params = {key: value for key, value in data.items() if key not in contents_keys}
    return (contents, params)


@dataclass
class Defaults:
    name: str
    params: dict
    contents: dict  # Values that go to job contents.

    @classmethod
    def add(cls, config, roots, expander, params_expander, data):
        d = {**data}
        name = d.pop("name")
        contents, params = split_contents_params(
            d, job_contents_keys | view_contents_keys
        )
        defaults = cls(name, params, contents)
        roots.defaults[name] = defaults

    @classmethod
    def empty(cls):
        return Defaults("empty", params={}, contents={})

    def merged_with_global(self, global_):
        return Defaults(
            name=f"{self.name}-merged-with-global",
            params={**global_.params, **self.params},
            contents={**global_.contents, **self.contents},
        )
