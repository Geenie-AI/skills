/**
 * Load one of this repository's skills into an OpenAI Agents SDK (JS) agent.
 *
 *   npm install @openai/agents zod
 *   npx tsx adapters/sdk/openai_agents_loader.ts <skill-name> "<request for the skill>"
 *
 * SKILL.md becomes the agent's instructions; `read_skill_file` serves the
 * skill's reference files on demand; `read_project_file` and `write_file` give
 * the skill file access inside the current working directory. Set SKILL_DIR to
 * use a skill folder outside this repository.
 *
 * verify: import names against https://openai.github.io/openai-agents-js/guides/tools/
 */

import { Agent, run, tool } from "@openai/agents";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const here = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(here, "../..");
const PROJECT_DIR = resolve(process.cwd());

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

function inside(root: string, rel: string): string {
  const target = resolve(root, rel);
  if (target !== root && !target.startsWith(root + "/")) {
    throw new Error(`path escapes ${root}: ${rel}`);
  }
  return target;
}

function buildAgent(name: string): Agent {
  const dir = skillDir(name);

  const readSkillFile = tool({
    name: "read_skill_file",
    description: `Read a file the ${name} skill references by relative path, e.g. reference/<file>.md.`,
    parameters: z.object({ path: z.string() }),
    execute: async ({ path }) => {
      try {
        return readFileSync(inside(dir, path), "utf8");
      } catch (err) {
        return `error: ${(err as Error).message}`;
      }
    },
  });

  const readProjectFile = tool({
    name: "read_project_file",
    description: "Read a file from the user's project by relative path.",
    parameters: z.object({ path: z.string() }),
    execute: async ({ path }) => {
      try {
        return readFileSync(inside(PROJECT_DIR, path), "utf8");
      } catch (err) {
        return `error: ${(err as Error).message}`;
      }
    },
  });

  const writeFile = tool({
    name: "write_file",
    description: "Write a file inside the user's project (path relative to the project root).",
    parameters: z.object({ path: z.string(), content: z.string() }),
    execute: async ({ path, content }) => {
      try {
        const target = inside(PROJECT_DIR, path);
        mkdirSync(dirname(target), { recursive: true });
        writeFileSync(target, content, "utf8");
        return `wrote ${relative(PROJECT_DIR, target)}`;
      } catch (err) {
        return `error: ${(err as Error).message}`;
      }
    },
  });

  const preamble =
    `You are running the ${name} skill. When the skill says to read one of its files, call read_skill_file with that relative path. ` +
    "Use read_project_file to inspect the user's project and write_file to emit every output file where the skill says, relative to the project root.\n\n";

  return new Agent({
    name,
    instructions: preamble + loadSkillBody(dir),
    tools: [readSkillFile, readProjectFile, writeFile],
  });
}

const [skillName, ...rest] = process.argv.slice(2);
const request = rest.join(" ");
if (!skillName || !request) {
  console.error('usage: openai_agents_loader.ts <skill-name> "<request for the skill>"');
  process.exit(2);
}
run(buildAgent(skillName), request)
  .then((result) => console.log(result.finalOutput))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
