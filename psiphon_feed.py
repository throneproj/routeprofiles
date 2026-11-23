#!/usr/bin/env python3
"""Check that a server_list_compressed is signed with Psiphon's remote server list key.

usage: psiphon_feed.py <server_list_compressed>
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zlib

# The public remote server list key also used by warp-plus, Oblivion and Hiddify.
PUBLIC_KEY = (
    "MIICIDANBgkqhkiG9w0BAQEFAAOCAg0AMIICCAKCAgEAt7Ls+/39r+T6zNW7GiVpJfzq/xvL9SBH5rIFnk0RXYEYavax3WS6HOD35eTAqn8AniOwiH+DOkvgSKF2caqk"
    "/y1dfq47Pdymtwzp9ikpB1C5OfAysXzBiwVJlCdajBKvBZDerV1cMvRzCKvKwRmvDmHgphQQ7WfXIGbRbmmk6opMBh3roE42KcotLFtqp0RRwLtcBRNtCdsrVsjiI1Lqz"
    "/lH+T61sGjSjQ3CHMuZYSQJZo/KrvzgQXpkaCTdbObxHqb6/+i1qaVOfEsvjoiyzTxJADvSytVtcTjijhPEV6XskJVHE1Zgl+7rATr/pDQkw6DPCNBS1+Y6fy7GstZALQ"
    "XwEDN/qhQI9kWkHijT8ns+i1vGg00Mk/6J75arLhqcodWsdeG/M/moWgqQAnlZAGVtJI1OgeF5fsPpXu4kctOfuZlGjVZXQNW34aOzm8r8S0eVZitPlbhcPiR4gT/aSMz"
    "/wd8lZlzZYsje/Jr8u/YtlwjjreZrGRmG8KMOzukV3lLmMppXFMvl4bxv6YFEmIuTsOhbLTwFgh7KYNjodLj/LsqRVfwz31PgWQFTEPICV7GCvgVlPRxnofqKSjgTWI4mxD"
    "hBpVcATvaoBl1L/6WLbFvBsoAUBItWwctO2xalKxF5szhGm8lccoc5MZr8kfE0uxMgsxz4er68iCID+rsCAQM="
)
MIN_ENTRIES = 50


def main():
    with open(sys.argv[1], "rb") as f:
        package = json.loads(zlib.decompress(f.read()))
    # The digest covers the base64 text of the key, not its DER bytes.
    if base64.b64decode(package["signingPublicKeyDigest"]) != hashlib.sha256(PUBLIC_KEY.encode()).digest():
        sys.exit("signed with another key")
    data = package["data"].encode()
    pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(PUBLIC_KEY[i:i + 64] for i in range(0, len(PUBLIC_KEY), 64)) + "\n-----END PUBLIC KEY-----\n"
    with tempfile.TemporaryDirectory() as tmp:
        paths = {name: os.path.join(tmp, name) for name in ("key.pem", "signature", "data")}
        with open(paths["key.pem"], "w") as f:
            f.write(pem)
        with open(paths["signature"], "wb") as f:
            f.write(base64.b64decode(package["signature"]))
        with open(paths["data"], "wb") as f:
            f.write(data)
        subprocess.run(["openssl", "dgst", "-sha256", "-verify", paths["key.pem"], "-signature", paths["signature"], paths["data"]], check=True)
    entries = sum(1 for line in data.splitlines() if line.strip())
    if entries < MIN_ENTRIES:
        sys.exit("only %d server entries" % entries)
    print(entries, "server entries")


if __name__ == "__main__":
    main()
