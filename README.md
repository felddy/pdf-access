# pdf-access #

[![GitHub Build Status](https://github.com/felddy/pdf-access/workflows/build/badge.svg)](https://github.com/felddy/pdf-access/actions)
[![CodeQL](https://github.com/felddy/pdf-access/workflows/CodeQL/badge.svg)](https://github.com/felddy/pdf-access/actions/workflows/codeql-analysis.yml)
[![Coverage Status](https://coveralls.io/repos/github/felddy/pdf-access/badge.svg?branch=develop)](https://coveralls.io/github/felddy/pdf-access?branch=develop)

pdf-access makes pdf documents more accessible to screen readers and other
assistive technologies.

It uses a toml configuration file to specify a plan, match certain documents,
and apply a list of actions to remediate a document.

Here is an example of a toml file that will unlock and remove text that is
preventing a screen reader from reading the documents authored by Mom.

Other documents will be trimmed down to a single page compressed.

```toml
#----------------- Sources -----------------

[sources.my_pdfs]
in_path = "./originals"
out_path = "./accessible"

#----------------- Plans -------------------

[plans.unlock-compress]
actions = ["clear_encoding_differences"]
# match documents from Mom
metadata_search = { "author" = "Mom" }
passwords = ["c@11-y0ur-m0+h3r", "w3@r-c13@n-und3rw34r"]
post_process = ["gs-compress"]

[plans.compress-and-trim]
actions = ["single-page"]
# match everything else
metadata_search = {}
post_process = ["gs-compress"]

#----------------- Actions -----------------

[actions.clear_encoding_differences]
name = "Clear encoding differences"
function = "clear-encoding-differences"

[actions.single-page]
name = "Keep one page"
function = "keep-pages"
args.pages = [0]
```

To run the plan, you would use the following command:

```bash
pdf-access config.toml
```

The files in the `./originals` directory would be processed and the results
would be placed in the `./accessible` directory.

## Installation ##

```bash
pip install git+https://github.com/felddy/pdf-access.git
```

## Contributing ##

We welcome contributions!  Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for
details.

## License ##

This project is in the worldwide [public domain](LICENSE).

This project is in the public domain within the United States, and
copyright and related rights in the work worldwide are waived through
the [CC0 1.0 Universal public domain
dedication](https://creativecommons.org/publicdomain/zero/1.0/).

All contributions to this project will be released under the CC0
dedication. By submitting a pull request, you are agreeing to comply
with this waiver of copyright interest.
