Our EN→DE product copy agent gets the content right but keeps breaking house style. We run it on the OpenAI Responses API with gpt-5. The prompt is in `fixtures/artifacts/style-agent-prompt.md`; it is about 6k tokens now because we added five full worked examples, which helped (style corrections went from roughly 70% of outputs to about 50%) but we are now over our latency and cost ceilings per item. We have 1,200 logged outputs, 600 of which editors have corrected by hand; a sample with the editors' notes is in `fixtures/artifacts/logged-outputs-sample.md`.

What should we do next?
