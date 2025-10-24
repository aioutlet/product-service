# Product Service<p align="center">

  <img alt="GoReleaser Logo" src="https://storage.googleapis.com/trufflehog-static-sources/pixel_pig.png" height="140" />

The `product-service` is a FastAPI-based microservice responsible for managing product catalog data in the AIOutlet platform. It handles product CRUD operations, reviews, ratings, and provides comprehensive product information. <h2 align="center">TruffleHog</h2>

  <p align="center">Find leaked credentials.</p>

**Architecture Pattern**: Publisher-Only (Amazon Catalog Service Pattern)</p>

- Publishes events via HTTP to the message-broker-service---

- Does NOT consume events from other services

- Maintains product catalog data as source of truth<div align="center">

- Other services query this service or consume its events

[![Go Report Card](https://goreportcard.com/badge/github.com/trufflesecurity/trufflehog/v3)](https://goreportcard.com/report/github.com/trufflesecurity/trufflehog/v3)

---[![License](https://img.shields.io/badge/license-AGPL--3.0-brightgreen)](/LICENSE)

[![Total Detectors](https://img.shields.io/github/directory-file-count/trufflesecurity/truffleHog/pkg/detectors?label=Total%20Detectors&type=dir)](/pkg/detectors)

## Features

</div>

- **Product Management**: Create, read, update, and delete products

- **Product Reviews**: User reviews and ratings with moderation---

- **Search & Filtering**: Advanced product search and category filtering

- **Bulk Operations**: Import/export products in bulk# :mag*right: \_Now Scanning*

- **Event Publishing**: Publishes product lifecycle events (created, updated, deleted, price changed)

- **Image Management**: Product image URLs and galleries<div align="center">

- **Admin Operations**: Product statistics and management endpoints

- **Rate Limiting**: Protection against abuse<img src="assets/scanning_logos.svg">

- **JWT Authentication**: Secure endpoints with role-based access

**...and more**

---

</div>

## Architecture

# :loudspeaker: Join Our Community

This service is built with **Python 3.12+** and **FastAPI**, using **MongoDB** for product storage.

Have questions? Feedback? Jump in slack or discord and hang out with us

**Publisher-Only Pattern (Amazon Catalog Service)**:

- Product Service is the **source of truth** for product catalog dataJoin our [Slack Community](https://join.slack.com/t/trufflehog-community/shared_invite/zt-pw2qbi43-Aa86hkiimstfdKH9UCpPzQ)

- Publishes events when products change

- Other services consume these events but don't send events backJoin the [Secret Scanning Discord](https://discord.gg/8Hzbrnkr7E)

- Clean separation of concerns: Products don't depend on other domains

# :tv: Demo

**Events Published**:

````![GitHub scanning demo](https://storage.googleapis.com/truffle-demos/non-interactive.svg)

product.created         → New product added to catalog

product.updated         → Product details changed```bash

product.deleted         → Product removed from catalogdocker run --rm -it -v "$PWD:/pwd" trufflesecurity/trufflehog:latest github --org=trufflesecurity

product.price.changed   → Product price updated```

review.created          → New review posted

review.updated          → Review modified# :floppy_disk: Installation

review.deleted          → Review removed

```Several options available for you:



**Event Consumers** (Other Services):```bash

- **Inventory Service**: Syncs product availability# MacOS users

- **Search Service**: Updates search indexbrew install trufflesecurity/trufflehog/trufflehog

- **Analytics Service**: Tracks product metrics

- **Audit Service**: Logs product changes# Docker

- **Notification Service**: Alerts subscribersdocker run --rm -it -v "$PWD:/pwd" trufflesecurity/trufflehog:latest github --repo https://github.com/trufflesecurity/test_keys



---# Docker for M1 and M2 Mac

docker run --platform linux/arm64 --rm -it -v "$PWD:/pwd" trufflesecurity/trufflehog:latest github --repo https://github.com/trufflesecurity/test_keys

## Project Structure

# Binary releases

```Download and unpack from https://github.com/trufflesecurity/trufflehog/releases

product-service/

├── src/# Compile from source

│   ├── main.py                      # FastAPI application entry pointgit clone https://github.com/trufflesecurity/trufflehog.git

│   ├── tracing_init.py              # OpenTelemetry tracing setupcd trufflehog; go install

│   ├── controllers/                 # Business logic controllers

│   │   ├── product_controller.py# Using installation script

│   │   ├── review_controller.pycurl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

│   │   ├── bulk_product_controller.py# Using installation script to install a specific version

│   │   ├── import_export_controller.pycurl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin <ReleaseTag like v3.56.0>

│   │   └── operational_controller.py```

│   ├── routers/                     # API route definitions

│   │   ├── product_router.py# :closed_lock_with_key: Verifying the artifacts

│   │   ├── review_router.py

│   │   ├── bulk_router.pyChecksums are applied to all artifacts, and the resulting checksum file is signed using cosign.

│   │   ├── import_export_router.py

│   │   └── home_router.pyYou need the following tool to verify signature:

│   ├── models/                      # Pydantic data models

│   │   ├── product.py- [Cosign](https://docs.sigstore.dev/cosign/installation/)

│   │   ├── review.py

│   │   └── product_base.pyVerification steps are as follow:

│   ├── db/                          # Database connections

│   │   └── mongodb.py1. Download the artifact files you want, and the following files from the [releases](https://github.com/trufflesecurity/trufflehog/releases) page.

│   ├── services/                    # External service clients

│   │   ├── message_broker_publisher.py   - trufflehog\_{version}\_checksums.txt

│   │   └── inventory_client.py   - trufflehog\_{version}\_checksums.txt.pem

│   ├── security/                    # Authentication & authorization   - trufflehog\_{version}\_checksums.txt.sig

│   │   └── dependencies.py

│   ├── middlewares/                 # FastAPI middlewares2. Verify the signature:

│   │   └── correlation_id.py

│   ├── observability/               # Logging and monitoring   ```shell

│   │   ├── logging/   cosign verify-blob <path to trufflehog_{version}_checksums.txt> \

│   │   └── tracing/   --certificate <path to trufflehog_{version}_checksums.txt.pem> \

│   ├── validators/                  # Input validation logic   --signature <path to trufflehog_{version}_checksums.txt.sig> \

│   ├── config/                      # Configuration management   --certificate-identity-regexp 'https://github\.com/trufflesecurity/trufflehog/\.github/workflows/.+' \

│   └── utils/                       # Utility functions   --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

├── tests/                           # Unit and integration tests   ```

├── scripts/                         # Deployment and utility scripts

├── Dockerfile                       # Production Docker image3. Once the signature is confirmed as valid, you can proceed to validate that the SHA256 sums align with the downloaded artifact:

├── Dockerfile.api                   # API-specific Docker image

├── requirements.txt                 # Python dependencies   ```shell

└── README.md                        # This file   sha256sum --ignore-missing -c trufflehog_{version}_checksums.txt

```   ```



---Replace `{version}` with the downloaded files version



## Getting Started# :rocket: Quick Start



### Prerequisites## 1: Scan a repo for only verified secrets



- Python 3.12+Command:

- MongoDB 7.0+

- Message Broker Service running (for event publishing)```bash

trufflehog git https://github.com/trufflesecurity/test_keys --only-verified

### Installation```



1. **Clone the repository**:Expected output:

   ```bash

   git clone https://github.com/aioutlet/aioutlet.git```

   cd services/product-service🐷🔑🐷  TruffleHog. Unearth your secrets. 🐷🔑🐷

````

Found verified result 🐷🔑

2. **Create virtual environment**:Detector Type: AWS

   ````bashDecoder Type: PLAIN

   python -m venv venvRaw result: AKIAYVP4CIPPERUVIFXG

   source venv/bin/activate  # On Windows: venv\Scripts\activateLine: 4

   ```Commit: fbc14303ffbf8fb1c2c1914e8dda7d0121633aca
   ````

File: keys

3. **Install dependencies**:Email: counter <counter@counters-MacBook-Air.local>

   ````bashRepository: https://github.com/trufflesecurity/test_keys

   pip install -r requirements.txtTimestamp: 2022-06-16 10:17:40 -0700 PDT

   ```...
   ````

````

4. **Configure environment variables**:

   ```bash## 2: Scan a GitHub Org for only verified secrets

   cp .env.example .env

   # Edit .env with your configuration```bash

   ```trufflehog github --org=trufflesecurity --only-verified

````

5. **Run the service**:

   ````bash## 3: Scan a GitHub Repo for only verified keys and get JSON output

   python -m uvicorn src.main:app --reload --port 8003

   ```Command:
   ````

The service will start on `http://localhost:8003````bash

trufflehog git https://github.com/trufflesecurity/test_keys --only-verified --json

### Environment Variables```

Key environment variables (see `.env.example` for full list):Expected output:

`bash`

# Service Configuration{"SourceMetadata":{"Data":{"Git":{"commit":"fbc14303ffbf8fb1c2c1914e8dda7d0121633aca","file":"keys","email":"counter \u003ccounter@counters-MacBook-Air.local\u003e","repository":"https://github.com/trufflesecurity/test_keys","timestamp":"2022-06-16 10:17:40 -0700 PDT","line":4}}},"SourceID":0,"SourceType":16,"SourceName":"trufflehog - git","DetectorType":2,"DetectorName":"AWS","DecoderName":"PLAIN","Verified":true,"Raw":"AKIAYVP4CIPPERUVIFXG","Redacted":"AKIAYVP4CIPPERUVIFXG","ExtraData":{"account":"595918472158","arn":"arn:aws:iam::595918472158:user/canarytokens.com@@mirux23ppyky6hx3l6vclmhnj","user_id":"AIDAYVP4CIPPJ5M54LRCY"},"StructuredData":null}

SERVICE_NAME=product-service...

PORT=8003```

ENVIRONMENT=development

## 4: Scan a GitHub Repo + its Issues and Pull Requests.

# Database

MONGODB_URI=mongodb://localhost:27017```bash

MONGODB_DB_NAME=product_dbtrufflehog github --repo=https://github.com/trufflesecurity/test_keys --issue-comments --pr-comments

````

# Message Broker (for publishing events)

MESSAGE_BROKER_SERVICE_URL=http://localhost:4000## 5: Scan an S3 bucket for verified keys

MESSAGE_BROKER_API_KEY=your-api-key

```bash

# JWT Authenticationtrufflehog s3 --bucket=<bucket name> --only-verified

JWT_SECRET=your-secret-key```

JWT_ALGORITHM=HS256

## 6: Scan S3 buckets using IAM Roles

# Tracing (Optional)

ENABLE_TRACING=true```bash

OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318trufflehog s3 --role-arn=<iam role arn>

````

---## 7: Scan a Github Repo using SSH authentication in docker

## API Endpoints```bash

docker run --rm -v "$HOME/.ssh:/root/.ssh:ro" trufflesecurity/trufflehog:latest git ssh://github.com/trufflesecurity/test_keys

### Public Endpoints```

- `GET /health` - Health check## 8: Scan individual files or directories

- `GET /health/ready` - Readiness probe

- `GET /health/live` - Liveness probe```bash

- `GET /metrics` - Prometheus metricstrufflehog filesystem path/to/file1.txt path/to/file2.txt path/to/dir

````

### Product Endpoints

## 9: Scan GCS buckets for verified secrets.

- `GET /api/products` - List all products (with pagination)

- `GET /api/products/{id}` - Get product by ID```bash

- `POST /api/products` - Create new product (requires auth)trufflehog gcs --project-id=<project-ID> --cloud-environment --only-verified

- `PUT /api/products/{id}` - Update product (requires auth)```

- `DELETE /api/products/{id}` - Delete product (requires admin)

- `GET /api/products/search` - Search products## 10: Scan a Docker image for verified secrets.

- `GET /api/products/category/{category}` - Get products by category

Use the `--image` flag multiple times to scan multiple images.

### Review Endpoints

```bash

- `GET /api/products/{id}/reviews` - Get product reviewstrufflehog docker --image trufflesecurity/secrets --only-verified

- `POST /api/products/{id}/reviews` - Create review (requires auth)```

- `PUT /api/products/{id}/reviews/{review_id}` - Update review (requires auth)

- `DELETE /api/products/{id}/reviews/{review_id}` - Delete review (requires auth/admin)## 11: Scan in CI



### Admin EndpointsSet the `--since-commit` flag to your default branch that people merge into (ex: "main"). Set the `--branch` flag to your PR's branch name (ex: "feature-1"). Depending on the CI/CD platform you use, this value can be pulled in dynamically (ex: [CIRCLE_BRANCH in Circle CI](https://circleci.com/docs/variables/) and [TRAVIS_PULL_REQUEST_BRANCH in Travis CI](https://docs.travis-ci.com/user/environment-variables/)). If the repo is cloned and the target branch is already checked out during the CI/CD workflow, then `--branch HEAD` should be sufficient. The `--fail` flag will return an 183 error code if valid credentials are found.



- `GET /api/admin/stats` - Product statistics (requires admin)```bash

- `POST /api/admin/products/bulk` - Bulk create products (requires admin)trufflehog git file://. --since-commit main --branch feature-1 --only-verified --fail

- `POST /api/admin/products/export` - Export products (requires admin)```

- `POST /api/admin/products/import` - Import products (requires admin)

# :question: FAQ

---

- All I see is `🐷🔑🐷  TruffleHog. Unearth your secrets. 🐷🔑🐷` and the program exits, what gives?

## Running with Docker  - That means no secrets were detected

- Why is the scan taking a long time when I scan a GitHub org

### Build the image:  - Unauthenticated GitHub scans have rate limits. To improve your rate limits, include the `--token` flag with a personal access token

- It says a private key was verified, what does that mean?

```bash  - Check out our Driftwood blog post to learn how to do this, in short we've confirmed the key can be used live for SSH or SSL [Blog post](https://trufflesecurity.com/blog/driftwood-know-if-private-keys-are-sensitive/)

docker build -t product-service:latest .- Is there an easy way to ignore specific secrets?

```  - If the scanned source [supports line numbers](https://github.com/trufflesecurity/trufflehog/blob/d6375ba92172fd830abb4247cca15e3176448c5d/pkg/engine/engine.go#L358-L365), then you can add a `trufflehog:ignore` comment on the line containing the secret to ignore that secrets.



### Run the container:# :newspaper: What's new in v3?



```bashTruffleHog v3 is a complete rewrite in Go with many new powerful features.

docker run -p 8003:8003 \

  -e MONGODB_URI=mongodb://host.docker.internal:27017 \- We've **added over 700 credential detectors that support active verification against their respective APIs**.

  -e MESSAGE_BROKER_SERVICE_URL=http://host.docker.internal:4000 \- We've also added native **support for scanning GitHub, GitLab, Docker, filesystems, S3, GCS, Circle CI and Travis CI**.

  product-service:latest- **Instantly verify private keys** against millions of github users and **billions** of TLS certificates using our [Driftwood](https://trufflesecurity.com/blog/driftwood) technology.

```- Scan binaries, documents, and other file formats

- Available as a GitHub Action and a pre-commit hook

---

## What is credential verification?

## Testing

For every potential credential that is detected, we've painstakingly implemented programmatic verification against the API that we think it belongs to. Verification eliminates false positives. For example, the [AWS credential detector](pkg/detectors/aws/aws.go) performs a `GetCallerIdentity` API call against the AWS API to verify if an AWS credential is active.

Run tests:

# :memo: Usage

```bash

pytestTruffleHog has a sub-command for each source of data that you may want to scan:

````

- git

Run with coverage:- github

- gitlab

````bash- docker

pytest --cov=src --cov-report=html- S3

```- filesystem (files and directories)

- syslog

---- circleci

- travisci

## Event Publishing- GCS (Google Cloud Storage)



The service publishes events to the message-broker-service:Each subcommand can have options that you can see with the `--help` flag provided to the sub command:



```python```

# Example: Publishing product.created event$ trufflehog git --help

await publisher.publish(usage: TruffleHog git [<flags>] <uri>

    event_type='product.created',

    data={Find credentials in git repositories.

        'productId': product_id,

        'name': product.name,Flags:

        'price': product.price,  -h, --help                Show context-sensitive help (also try --help-long and --help-man).

        'category': product.category      --debug               Run in debug mode.

    },      --trace               Run in trace mode.

    correlation_id=correlation_id      --profile             Enables profiling and sets a pprof and fgprof server on :18066.

)  -j, --json                Output in JSON format.

```      --json-legacy         Use the pre-v3.0 JSON format. Only works with git, gitlab, and github sources.

      --github-actions      Output in GitHub Actions format.

---      --concurrency=8       Number of concurrent workers.

      --no-verification     Don't verify the results.

## Why Publisher-Only?      --only-verified       Only output verified results.

      --filter-unverified   Only output first unverified result per chunk per detector if there are more than one results.

Following **Amazon's Catalog Service pattern**:      --filter-entropy=FILTER-ENTROPY

                                 Filter unverified results with Shannon entropy. Start with 3.0.

1. **Single Source of Truth**: Product Service owns product data      --config=CONFIG            Path to configuration file.

2. **No Circular Dependencies**: Products don't react to other services      --print-avg-detector-time

3. **Simpler Architecture**: Clear unidirectional event flow                                 Print the average time spent on each detector.

4. **Better Scalability**: No need to process incoming events      --no-update           Don't check for updates.

5. **Data Consistency**: Product updates are immediate, not eventual      --fail                Exit with code 183 if results are found.

      --verifier=VERIFIER ...    Set custom verification endpoints.

**What About Stock Status?**      --archive-max-size=ARCHIVE-MAX-SIZE

- Inventory Service owns stock data                                 Maximum size of archive to scan. (Byte units eg. 512B, 2KB, 4MB)

- Frontend/BFF aggregates data from both services      --archive-max-depth=ARCHIVE-MAX-DEPTH

- Product Service doesn't store inventory counts                                 Maximum depth of archive to scan.

      --archive-timeout=ARCHIVE-TIMEOUT

**What About Reviews Updating Ratings?**                                 Maximum time to spend extracting an archive.

- Review Service calls Product Service API directly for immediate consistency      --include-detectors="all"  Comma separated list of detector types to include. Protobuf name or IDs may be used, as well as ranges.

- Product Service then publishes `product.rating.updated` event      --exclude-detectors=EXCLUDE-DETECTORS

                                 Comma separated list of detector types to exclude. Protobuf name or IDs may be used, as well as ranges. IDs defined here take precedence over the include list.

---      --version             Show application version.

  -i, --include-paths=INCLUDE-PATHS

## Contributing                                 Path to file with newline separated regexes for files to include in scan.

  -x, --exclude-paths=EXCLUDE-PATHS

1. Fork the repository                                 Path to file with newline separated regexes for files to exclude in scan.

2. Create a feature branch (`git checkout -b feature/amazing-feature`)      --exclude-globs=EXCLUDE-GLOBS

3. Commit your changes (`git commit -m 'Add amazing feature'`)                                 Comma separated list of globs to exclude in scan. This option filters at the `git log` level, resulting in faster scans.

4. Push to the branch (`git push origin feature/amazing-feature`)      --since-commit=SINCE-COMMIT

5. Open a Pull Request                                 Commit to start scan from.

      --branch=BRANCH            Branch to scan.

---      --max-depth=MAX-DEPTH      Maximum depth of commits to scan.

      --bare                Scan bare repository (e.g. useful while using in pre-receive hooks)

## License

Args:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  <uri>  Git repository URL. https://, file://, or ssh:// schema expected.

````

---

For example, to scan a `git` repository, start with

## Support

````

For issues and questions:$ trufflehog git https://github.com/trufflesecurity/trufflehog.git

- GitHub Issues: https://github.com/aioutlet/aioutlet/issues```

- Documentation: https://docs.aioutlet.com

## S3

---

The S3 source supports assuming IAM roles for scanning in addition to IAM users. This makes it easier for users to scan multiple AWS accounts without needing to rely on hardcoded credentials for each account.

**Built with ❤️ by the AIOutlet Team**

The IAM identity that TruffleHog uses initially will need to have `AssumeRole` privileges as a principal in the [trust policy](https://aws.amazon.com/blogs/security/how-to-use-trust-policies-with-iam-roles/) of each IAM role to assume.

To scan a specific bucket using locally set credentials or instance metadata if on an EC2 instance:

```bash
trufflehog s3 --bucket=<bucket-name>
````

To scan a specific bucket using an assumed role:

```bash
trufflehog s3 --bucket=<bucket-name> --role-arn=<iam-role-arn>
```

Multiple roles can be passed as separate arguments. The following command will attempt to scan every bucket each role has permissions to list in the S3 API:

```bash
trufflehog s3 --role-arn=<iam-role-arn-1> --role-arn=<iam-role-arn-2>
```

Exit Codes:

- 0: No errors and no results were found.
- 1: An error was encountered. Sources may not have completed scans.
- 183: No errors were encountered, but results were found. Will only be returned if `--fail` flag is used.

## :octocat: TruffleHog Github Action

```yaml
- name: TruffleHog
  uses: trufflesecurity/trufflehog@main
  with:
    # Repository path
    path:
    # Start scanning from here (usually main branch).
    base:
    # Scan commits until here (usually dev branch).
    head: # optional
    # Extra args to be passed to the trufflehog cli.
    extra_args: --debug --only-verified
```

The TruffleHog OSS Github Action can be used to scan a range of commits for leaked credentials. The action will fail if
any results are found.

For example, to scan the contents of pull requests you could use the following workflow:

```yaml
name: TruffleHog Secrets Scan
on: [pull_request]
jobs:
  TruffleHog:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: TruffleHog OSS
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --debug --only-verified
```

## Pre-commit Hook

Trufflehog can be used in a pre-commit hook to prevent credentials from leaking before they ever leave your computer.
An example `.pre-commit-config.yaml` is provided (see [pre-commit.com](https://pre-commit.com/) for installation).

```yaml
repos:
  - repo: local
    hooks:
      - id: trufflehog
        name: TruffleHog
        description: Detect secrets in your data.
        entry: bash -c 'trufflehog git file://. --since-commit HEAD --only-verified --fail'
        # For running trufflehog in docker, use the following entry instead:
        # entry: bash -c 'docker run --rm -v "$(pwd):/workdir" -i --rm trufflesecurity/trufflehog:latest git file:///workdir --since-commit HEAD --only-verified --fail'
        language: system
        stages: ['commit', 'push']
```

## Regex Detector (alpha)

Trufflehog supports detection and verification of custom regular expressions.
For detection, at least one **regular expression** and **keyword** is required.
A **keyword** is a fixed literal string identifier that appears in or around
the regex to be detected. To allow maximum flexibility for verification, a
webhook is used containing the regular expression matches.

Trufflehog will send a JSON POST request containing the regex matches to a
configured webhook endpoint. If the endpoint responds with a `200 OK` response
status code, the secret is considered verified.

**NB:** This feature is alpha and subject to change.

## Regex Detector Example

```yaml
# config.yaml
detectors:
  - name: hog detector
    keywords:
      - hog
    regex:
      adjective: hogs are (\S+)
    verify:
      - endpoint: http://localhost:8000/
        # unsafe must be set if the endpoint is HTTP
        unsafe: true
        headers:
          - 'Authorization: super secret authorization header'
```

```
$ trufflehog filesystem /tmp --config config.yaml --only-verified
🐷🔑🐷  TruffleHog. Unearth your secrets. 🐷🔑🐷

Found verified result 🐷🔑
Detector Type: CustomRegex
Decoder Type: PLAIN
Raw result: hogs are cool
File: /tmp/hog-facts.txt
```

## Verification Server Example (Python)

Unless you run a verification server, secrets found by the custom regex
detector will be unverified. Here is an example Python implementation of a
verification server for the above `config.yaml` file.

```python
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

AUTH_HEADER = 'super secret authorization header'


class Verifier(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(405)
        self.end_headers()

    def do_POST(self):
        try:
            if self.headers['Authorization'] != AUTH_HEADER:
                self.send_response(401)
                self.end_headers()
                return

            # read the body
            length = int(self.headers['Content-Length'])
            request = json.loads(self.rfile.read(length))
            self.log_message("%s", request)

            # check the match
            if request['hog detector']['adjective'][-1] == 'cool':
                self.send_response(200)
                self.end_headers()
            else:
                # any other response besides 200
                self.send_response(406)
                self.end_headers()
        except Exception:
            self.send_response(400)
            self.end_headers()


with HTTPServer(('', 8000), Verifier) as server:
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
```

# :heart: Contributors

This project exists thanks to all the people who contribute. [[Contribute](CONTRIBUTING.md)].

<a href="https://github.com/trufflesecurity/trufflehog/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=trufflesecurity/trufflehog" />
</a>

# :computer: Contributing

Contributions are very welcome! Please see our [contribution guidelines first](CONTRIBUTING.md).

We no longer accept contributions to TruffleHog v2, but that code is available in the `v2` branch.

## Adding new secret detectors

We have published some [documentation and tooling to get started on adding new secret detectors](hack/docs/Adding_Detectors_external.md). Let's improve detection together!

# Use as a library

Currently, trufflehog is in heavy development and no guarantees can be made on
the stability of the public APIs at this time.

# License Change

Since v3.0, TruffleHog is released under a AGPL 3 license, included in [`LICENSE`](LICENSE). TruffleHog v3.0 uses none of the previous codebase, but care was taken to preserve backwards compatibility on the command line interface. The work previous to this release is still available licensed under GPL 2.0 in the history of this repository and the previous package releases and tags. A completed CLA is required for us to accept contributions going forward.

# :money_with_wings: Enterprise product

Are you interested in continuously monitoring your Git, Jira, Slack, Confluence, etc.. for credentials? We have an enterprise product that can help. Reach out here to learn more https://trufflesecurity.com/contact/

We take the revenue from the enterprise product to fund more awesome open source projects that the whole community can benefit from.
