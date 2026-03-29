import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { definePluginEntry } from "openclaw/plugin-sdk/core";

const execFileAsync = promisify(execFile);

type BrainOpsConfig = {
  brainCommand?: string;
  workingDirectory?: string;
  configPath?: string;
};

type ToolSpec = {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  buildArgs: (input: Record<string, unknown>, cfg: BrainOpsConfig) => string[];
};

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function buildSharedArgs(cfg: BrainOpsConfig): string[] {
  const args: string[] = [];
  if (cfg.configPath) {
    args.push("--config", cfg.configPath);
  }
  return args;
}

async function runBrainOps(cfg: BrainOpsConfig, args: string[]) {
  const command = cfg.brainCommand || "brain";
  const cwd = cfg.workingDirectory || process.cwd();
  const { stdout, stderr } = await execFileAsync(command, args, {
    cwd,
    env: {
      ...process.env,
      PYTHONPATH: process.env.PYTHONPATH || "src",
    },
  });

  const trimmed = stdout.trim();
  const parsed = trimmed ? JSON.parse(trimmed) : {};
  return {
    ok: true,
    command,
    args,
    cwd,
    data: parsed,
    stderr: stderr.trim() || undefined,
  };
}

const tools: ToolSpec[] = [
  {
    name: "brain_ops_handle_input",
    description: "Route and execute safe brain-ops actions from natural language.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["text"],
      properties: {
        text: { type: "string", description: "Natural-language user message." },
        useLlm: { type: "boolean", description: "Allow Ollama-assisted routing." },
        dryRun: { type: "boolean", description: "Preview without side effects." },
      },
    },
    buildArgs: (input, cfg) => {
      const text = asString(input.text) || "";
      const args = ["handle-input", text, "--json", ...buildSharedArgs(cfg)];
      if (input.dryRun) args.push("--dry-run");
      if (input.useLlm === true) args.push("--use-llm");
      if (input.useLlm === false) args.push("--no-use-llm");
      return args;
    },
  },
  {
    name: "brain_ops_route_input",
    description: "Classify a natural-language message without side effects.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["text"],
      properties: {
        text: { type: "string", description: "Natural-language user message." },
        useLlm: { type: "boolean", description: "Allow Ollama-assisted routing." },
      },
    },
    buildArgs: (input, cfg) => {
      const text = asString(input.text) || "";
      const args = ["route-input", text, "--json", ...buildSharedArgs(cfg)];
      if (input.useLlm === true) args.push("--use-llm");
      return args;
    },
  },
  {
    name: "brain_ops_daily_summary",
    description: "Write the structured daily summary into the Obsidian daily note.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        date: { type: "string", description: "Date in YYYY-MM-DD format." },
        dryRun: { type: "boolean", description: "Preview without writing to the vault." },
      },
    },
    buildArgs: (input, cfg) => {
      const args = ["daily-summary", "--json", ...buildSharedArgs(cfg)];
      if (asString(input.date)) args.push("--date", String(input.date));
      if (input.dryRun) args.push("--dry-run");
      return args;
    },
  },
  {
    name: "brain_ops_daily_macros",
    description: "Read nutrition totals from SQLite.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        date: { type: "string", description: "Date in YYYY-MM-DD format." },
      },
    },
    buildArgs: (input, cfg) => {
      const args = ["daily-macros", ...buildSharedArgs(cfg)];
      if (asString(input.date)) args.push("--date", String(input.date));
      return args;
    },
  },
  {
    name: "brain_ops_spending_summary",
    description: "Read expense totals from SQLite.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        date: { type: "string", description: "Date in YYYY-MM-DD format." },
      },
    },
    buildArgs: (input, cfg) => {
      const args = ["spending-summary", ...buildSharedArgs(cfg)];
      if (asString(input.date)) args.push("--date", String(input.date));
      return args;
    },
  },
];

export default definePluginEntry({
  id: "brain-ops",
  name: "brain-ops",
  register(api: { config?: BrainOpsConfig; registerTool?: (spec: Record<string, unknown>) => void }) {
    const cfg = api.config || {};

    if (!api.registerTool) {
      throw new Error("OpenClaw registerTool API is unavailable.");
    }

    for (const tool of tools) {
      api.registerTool({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
        async handler(input: Record<string, unknown>) {
          return runBrainOps(cfg, tool.buildArgs(input, cfg));
        },
      });
    }
  },
});
