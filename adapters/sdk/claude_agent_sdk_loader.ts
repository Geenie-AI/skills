/**
 * Load one of this repository's skills into a Claude Agent SDK agent.
 *
 *   npm install @anthropic-ai/claude-agent-sdk zod
 *   npx tsx adapters/sdk/claude_agent_sdk_loader.ts <skill-name> "<request for the skill>"
 *
 * SKILL.md becomes the appended system prompt; `read_skill_file` serves the
 * skill's reference files on demand. Set SKILL_DIR to use a skill folder
 * outside this repository. Checked against
 * https://code.claude.com/docs/en/agent-sdk/typescript on 2026-11-14.
 */

import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const here = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(here, "../..");

function skillDir(name: string): string {
  const dir = resolve(process.env.SKILL_DIR ?? resolve(REPO_ROOT, "skills", name));
  if (!existsSync(resolve(dir, "SKILL.md"))) {
    console.error(`no SKILL.md under ${dir}`);
    process.exit(2);
  }
  return dir;
}

function loadSkillBody(dir: string): string {
  let text = readFileSync(resolve(dir, "SKILL.md"), "utf8");
  if (text.startsWith("---")) {
    const end = text.indexOf("\n---\n");
    if (end !== -1) text = text.slice(end + 5);
  }
  return text.trim();
}

function resolveInside(root: string, relative: string): string {
  const target = resolve(root, relative);
  if (target !== root && !target.startsWith(root + "/")) {
    throw new Error(`path escapes the skill folder: ${relative}`);
  }
  return target;
}

async function main(name: string, request: string): Promise<void> {
  const dir = skillDir(name);
  const readSkillFile = tool(
    "read_skill_file",
    `Read a file that the ${name} skill references by relative path, for example reference/<file>.md or templates/<file>.md.`,
    { path: z.string() },
    async ({ path }) => {
      try {
        return { content: [{ type: "text", text: readFileSync(resolveInside(dir, path), "utf8") }] };
      } catch (err) {
        return { content: [{ type: "text", text: `error: ${(err as Error).message}` }], isError: true };
      }
    },
  );
  const skillServer = createSdkMcpServer({ name: "skill", version: "1.0.0", tools: [readSkillFile] });
  const preamble =
    `You are running the ${name} skill. When the skill says to read one of its files, call the read_skill_file tool with that relative path. ` +
    "Treat the current working directory as the user's project and write output files where the skill says, relative to it.\n\n";

  for await (const message of query({
    prompt: request,
    options: {
      cwd: process.cwd(),
      systemPrompt: { type: "preset", preset: "claude_code", append: preamble + loadSkillBody(dir) },
      mcpServers: { skill: skillServer },
      allowedTools: ["mcp__skill__read_skill_file", "Read", "Write", "Edit", "Glob", "Grep"],
      permissionMode: "acceptEdits",
    },
  })) {
    if (message.type === "result" && "result" in message) {
      console.log(message.result);
    }
  }
}

const [skillName, ...rest] = process.argv.slice(2);
const request = rest.join(" ");
if (!skillName || !request) {
  console.error('usage: claude_agent_sdk_loader.ts <skill-name> "<request for the skill>"');
  process.exit(2);
}
main(skillName, request).catch((err) => {
  console.error(err);
  process.exit(1);
});
