from .base import Base
from ..binding_config import BindingConfig

directives = [
    "default_src",
    "script_src",
    "style_src",
    "img_src",
    "connect_src",
    "font_src",
    "object_src",
    "media_src",
    "frame_src",
    "sandbox",
    "report_uri",
    "child_src",
    "form_action",
    "frame_ancestors",
    "plugin_types",
    "base_uri",
    "report_to",
    "worker_src",
    "manifest_src",
    "prefetch_src",
    "navigate_to",
]


class CSP(Base):
    header_name = "content-security-policy"
    default_src = None
    script_src = None
    style_src = None
    img_src = None
    connect_src = None
    font_src = None
    object_src = None
    media_src = None
    frame_src = None
    sandbox = None
    report_uri = None
    child_src = None
    form_action = None
    frame_ancestors = None
    plugin_types = None
    base_uri = None
    report_to = None
    worker_src = None
    manifest_src = None
    prefetch_src = None
    navigate_to = None

    def __init__(self, environment):
        super().__init__(environment)

    def configure(
        self,
        default_src=None,
        script_src=None,
        style_src=None,
        img_src=None,
        connect_src=None,
        font_src=None,
        object_src=None,
        media_src=None,
        frame_src=None,
        sandbox=None,
        report_uri=None,
        child_src=None,
        form_action=None,
        frame_ancestors=None,
        plugin_types=None,
        base_uri=None,
        report_to=None,
        worker_src=None,
        manifest_src=None,
        prefetch_src=None,
        navigate_to=None,
    ):
        self.default_src = default_src
        self.script_src = script_src
        self.style_src = style_src
        self.img_src = img_src
        self.connect_src = connect_src
        self.font_src = font_src
        self.object_src = object_src
        self.media_src = media_src
        self.frame_src = frame_src
        self.sandbox = sandbox
        self.report_uri = report_uri
        self.child_src = child_src
        self.form_action = form_action
        self.frame_ancestors = frame_ancestors
        self.plugin_types = plugin_types
        self.base_uri = base_uri
        self.report_to = report_to
        self.worker_src = worker_src
        self.manifest_src = manifest_src
        self.prefetch_src = prefetch_src
        self.navigate_to = navigate_to

    def set_headers_for_input_output(self, input_output):
        parts = []
        for variable_name in directives:
            value = getattr(self, variable_name)
            if not value:
                continue
            header_key_name = variable_name.replace("_", "-")
            parts.append(f"{header_key_name} {value}")
        if not parts:
            return
        header_value = "; ".join(parts)
        input_output.set_header(self.header_name, header_value)


def csp(
    default_src=None,
    script_src=None,
    style_src=None,
    img_src=None,
    connect_src=None,
    font_src=None,
    object_src=None,
    media_src=None,
    frame_src=None,
    sandbox=None,
    report_uri=None,
    child_src=None,
    form_action=None,
    frame_ancestors=None,
    plugin_types=None,
    base_uri=None,
    report_to=None,
    worker_src=None,
    manifest_src=None,
    prefetch_src=None,
    navigate_to=None,
):
    for variable_name in directives:
        value = locals()[variable_name]
        if value is not None and type(value) != str:
            actual_type = type(value)
            raise ValueError(
                f"Invalid configuration value for CSP: {variable_name} should be a string but instead is '{actual_type}'"
            )
    return BindingConfig(
        CSP,
        default_src=default_src,
        script_src=script_src,
        style_src=style_src,
        img_src=img_src,
        connect_src=connect_src,
        font_src=font_src,
        object_src=object_src,
        media_src=media_src,
        frame_src=frame_src,
        sandbox=sandbox,
        report_uri=report_uri,
        child_src=child_src,
        form_action=form_action,
        frame_ancestors=frame_ancestors,
        plugin_types=plugin_types,
        base_uri=base_uri,
        report_to=report_to,
        worker_src=worker_src,
        manifest_src=manifest_src,
        prefetch_src=prefetch_src,
        navigate_to=navigate_to,
    )
