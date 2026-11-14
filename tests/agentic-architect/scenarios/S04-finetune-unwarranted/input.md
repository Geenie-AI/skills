I want a fine-tuned model for our code-review agent. It runs in Claude Code on our private Go repo (`ledgerd`) and keeps missing things our senior maintainers always catch. I have eight examples of a diff, what the reviewer said, and what the maintainer said instead, in `fixtures/artifacts/review-examples.md`. The repo is in the working directory; our conventions are in `CONTRIBUTING.md`.

Can you set up the fine-tune?
