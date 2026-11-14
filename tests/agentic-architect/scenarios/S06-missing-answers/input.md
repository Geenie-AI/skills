We want to build an internal helpdesk agent for our HR policy portal. Employees ask HR questions in chat; the agent should answer from our policy pages (about 400 of them, updated quarterly), open a ticket when it cannot answer, and it must never change payroll data. We are on the OpenAI Agents SDK. We expect around 2,000 questions a day.

For the economics: a correct self-service answer saves about $15; a wrong answer that an employee accepts costs around $200 in rework and complaints; an unnecessary ticket costs about $10. We have 30 examples from past tickets of question plus the answer an HR adviser gave.

We are picturing a chatbot with one big prompt, but we are open to whatever works.
