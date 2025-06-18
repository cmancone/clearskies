import clearskies.configs
import clearskies.parameters_to_properties
from clearskies.security_header import SecurityHeader


class Csp(SecurityHeader):
    header_name = "content-security-policy"
    default_src = clearskies.configs.String()
    script_src = clearskies.configs.String()
    style_src = clearskies.configs.String()
    img_src = clearskies.configs.String()
    connect_src = clearskies.configs.String()
    font_src = clearskies.configs.String()
    object_src = clearskies.configs.String()
    media_src = clearskies.configs.String()
    frame_src = clearskies.configs.String()
    sandbox = clearskies.configs.String()
    report_uri = clearskies.configs.String()
    child_src = clearskies.configs.String()
    form_action = clearskies.configs.String()
    frame_ancestors = clearskies.configs.String()
    plugin_types = clearskies.configs.String()
    base_uri = clearskies.configs.String()
    report_to = clearskies.configs.String()
    worker_src = clearskies.configs.String()
    manifest_src = clearskies.configs.String()
    prefetch_src = clearskies.configs.String()
    navigate_to = clearskies.configs.String()

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

    @clearskies.parameters_to_properties.parameters_to_properties
    def __init__(
        self,
        default_src: str = "",
        script_src: str = "",
        style_src: str = "",
        img_src: str = "",
        connect_src: str = "",
        font_src: str = "",
        object_src: str = "",
        media_src: str = "",
        frame_src: str = "",
        sandbox: str = "",
        report_uri: str = "",
        child_src: str = "",
        form_action: str = "",
        frame_ancestors: str = "",
        plugin_types: str = "",
        base_uri: str = "",
        report_to: str = "",
        worker_src: str = "",
        manifest_src: str = "",
        prefetch_src: str = "",
        navigate_to: str = "",
    ):
        self.finalize_and_validate_configuration()

    def set_headers_for_input_output(self, input_output):
        parts = []
        for variable_name in self.directives:
            value = getattr(self, variable_name)
            if not value:
                continue
            if value.lower().strip() == "self":
                value = "'self'"
            header_key_name = variable_name.replace("_", "-")
            parts.append(f"{header_key_name} {value}")
        if not parts:
            return
        header_value = "; ".join(parts)
        input_output.response_headers.add(self.header_name, header_value)
