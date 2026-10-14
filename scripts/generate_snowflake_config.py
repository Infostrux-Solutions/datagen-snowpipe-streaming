"""Fill the account URL and private key into the sink template. Output is git-ignored."""
import re
from _common import ACCOUNT, KEY_PATH, ROOT

body = re.sub(r"-----[A-Z ]+-----|\s", "", KEY_PATH.read_text())  # connector wants the bare key body
text = (ROOT / "connect" / "snowflake-sink.template.json").read_text()
text = text.replace("__PRIVATE_KEY__", body).replace("<your-account>", ACCOUNT)
(ROOT / "connect" / "snowflake-sink.generated.json").write_text(text)
print("wrote connect/snowflake-sink.generated.json")
