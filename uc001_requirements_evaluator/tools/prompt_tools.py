import vertexai
from vertexai.preview import prompts as prompt_mgmt
from vertexai.preview.prompts import Prompt
from vertexai.generative_models._generative_models import _proto_to_dict
from uc001_requirements_evaluator.constants import PROJECT_ID, LOCATION

_initialized = False

def _init() -> None:
    global _initialized
    if not _initialized:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        _initialized = True

def get_prompt(key: str) -> str:
    """
    Fetches the current text (latest version) of the prompt resource whose
    display_name matches `key` (e.g. "UC001_evaluator"), without going
    through prompt_mgmt.get().

    prompt_mgmt.get() re-parses the resource's full generationConfig/tools
    into strongly-typed protos, which raises a protobuf ParseError as soon as
    Vertex AI Studio has saved a preview field (e.g. generationConfig.
    thinkingConfig.thinkingLevel, tools[].googleMaps.groundingTypes) that
    predates this pinned SDK's compiled proto definitions. We only need the
    prompt text, so fetch the raw dataset dict instead and pull it straight
    out of promptMessage.contents, skipping that conversion entirely.
    """
    _init()
    prompt_id = list_prompt_ids(key)[0]
    
    prompt = Prompt()
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/datasets/{prompt_id}"
    dataset_dict = _proto_to_dict(prompt._dataset_client.get_dataset(name=name))

    prompt_message = dataset_dict["metadata"]["promptApiSchema"]["multimodalPrompt"]["promptMessage"]
    contents = prompt_message.get("contents", [])
    if not contents:
        raise ValueError(f"Prompt {prompt_id!r} has no prompt text.")

    prompt_val = "".join(part["text"] for part in contents[0].get("parts", []) if "text" in part)
    print(prompt_val)
    return prompt_val


def list_prompt_ids(key: str) -> list[str]:
    """
    Finds prompt resources in the project's Prompt Management store whose
    display_name exactly matches `key` (e.g. "UC001_evaluator"). Returns the
    matching prompt_ids — normally zero or one, but a list in case more than
    one resource was saved under the same display_name.
    """
    _init()
    return [prompt.prompt_id for prompt in prompt_mgmt.list() if prompt.display_name == key]
