import base64
import json
import os
import pathlib
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI





class UpstageParser:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        self.schema_client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1/information-extraction/schema-generation"
        )
        self.extraction_client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1/information-extraction"
        )

    def encode_img_to_base64(self, img_bytes: bytes) -> str:
        base64_data = base64.b64encode(img_bytes).decode('utf-8')
        return base64_data

    def get_schema(self, img_bytes: bytes) -> Dict[str, Any]:
        base64_data = self.encode_img_to_base64(img_bytes)
        schema_response = self.schema_client.chat.completions.create(
            model="information-extract",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_data}"}
                        }
                    ]
                }
            ],
        )
        schema = json.loads(schema_response.choices[0].message.content)
        return schema

    def load_default_schema(self) -> Dict[str, Any]:
        schema_path = pathlib.Path(__file__).parent / "default_schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract(self, img_bytes: bytes, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        base64_data = self.encode_img_to_base64(img_bytes)
        if schema is None:
            schema = self.load_default_schema()
        extraction_response = self.extraction_client.chat.completions.create(
            model="information-extract",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_data}"}
                        }
                    ]
                }
            ],
            response_format=schema,
        )
        extracted_info = json.loads(extraction_response.choices[0].message.content)
        return extracted_info


## USAGE
    # parser = UpstageParser()
    # with open("./jr.png", "rb") as img_file:
    #     img_bytes = img_file.read()
    # get schema json of the document(auto schema mode)
    # schema = parser.get_schema(img_bytes)
    # print("Schema:")
    # print(json.dumps(schema, indent=2))
    # fix the schema
    # # extracted_info = parser.extract(img_bytes, schema)
    # extracted_info = parser.extract(img_bytes)
    # print(json.dumps(extracted_info, indent=2))
