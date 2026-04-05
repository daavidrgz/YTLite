"""Check for new YouTube iOS version via iTunes lookup API."""

import os
import sys
import urllib.request
import json


def main():
    lookup_url = "https://itunes.apple.com/lookup?bundleId=com.google.ios.youtube&country=us"
    resp = urllib.request.urlopen(lookup_url)
    data = json.loads(resp.read())

    if not data.get("results"):
        print("No results from iTunes API", file=sys.stderr)
        sys.exit(1)

    result = data["results"][0]
    version = result["version"]
    last_known = os.environ.get("LAST_KNOWN_VERSION", "")
    force = os.environ.get("FORCE", "false").lower() == "true"

    print(f"Current App Store version: {version}")
    print(f"Last known version: {last_known or '(none)'}")

    should_build = force or version != last_known

    if should_build:
        print(f"New version detected!" if not force else "Force build requested.")
    else:
        print("No new version. Skipping build.")

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"version={version}\n")
            f.write(f"should_build={'true' if should_build else 'false'}\n")
    else:
        print(f"version={version}")
        print(f"should_build={should_build}")


if __name__ == "__main__":
    main()
