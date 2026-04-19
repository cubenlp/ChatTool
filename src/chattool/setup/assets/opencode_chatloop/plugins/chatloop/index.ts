import { appendFile, mkdir, readFile, stat, unlink, writeFile } from "fs/promises"
import { dirname, join, resolve } from "path"
import { tool, type Plugin } from "@opencode-ai/plugin"

type State = {
  active: boolean
  sessionId?: string
  projectPath?: string
  iteration: number
  maxIterations: number
  initialMessage?: string
}

const STATE_FILE = "chatloop.local.md"
const EVENTS_FILE = "chatloop.events.log"
const COMPLETE_RE = /<complete>DONE<\/complete>/i

const statePath = (projectPath: string) => join(projectPath, ".opencode", STATE_FILE)
const eventsPath = (projectPath: string) => join(projectPath, EVENTS_FILE)

const parseStoredString = (value?: string) => {
  if (!value) return undefined
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

const readState = async (projectPath: string): Promise<State> => {
  try {
    const text = await readFile(statePath(projectPath), "utf-8")
    const body = text.split(/^---$/m)[2] ?? ""
    const active = /active:\s*true/.test(text)
    const sessionId = text.match(/sessionId:\s*(.+)$/m)?.[1]?.trim()
    const projectPath = text.match(/projectPath:\s*(.+)$/m)?.[1]?.trim()
    const initialMessage = parseStoredString(text.match(/initialMessage:\s*(.+)$/m)?.[1]?.trim())
    const iteration = Number(text.match(/iteration:\s*(\d+)/m)?.[1] ?? 0)
    const maxIterations = Number(text.match(/maxIterations:\s*(\d+)/m)?.[1] ?? 20)
    return {
      active,
      sessionId,
      projectPath: projectPath || body.trim() || undefined,
      initialMessage,
      iteration,
      maxIterations,
    }
  } catch {
    return { active: false, iteration: 0, maxIterations: 20 }
  }
}

const writeState = async (projectPath: string, state: State) => {
  await mkdir(dirname(statePath(projectPath)), { recursive: true })
  await writeFile(
    statePath(projectPath),
    `---\nactive: ${state.active}\niteration: ${state.iteration}\nmaxIterations: ${state.maxIterations}\n${state.sessionId ? `sessionId: ${state.sessionId}\n` : ""}${state.projectPath ? `projectPath: ${state.projectPath}\n` : ""}${state.initialMessage ? `initialMessage: ${JSON.stringify(state.initialMessage)}\n` : ""}---\n\n${state.projectPath ?? ""}`,
    "utf-8",
  )
}

const clearState = async (projectPath: string) => {
  await unlink(statePath(projectPath)).catch(() => {})
}

const exists = async (path: string) => {
  try {
    await stat(path)
    return true
  } catch {
    return false
  }
}

const resolveProjectPath = async (directory: string) => {
  let current = resolve(directory)
  while (true) {
    const prd = join(current, "PRD.md")
    if (await exists(prd)) {
      return { projectPath: current, prdPath: prd }
    }
    const parent = dirname(current)
    if (parent === current) {
      throw new Error(`No PRD.md found in ${resolve(directory)} or its parent directories. ChatLoop requires a project root with PRD.md.`)
    }
    current = parent
  }
}

const tryResolveProjectPath = async (directory: string) => {
  try {
    return await resolveProjectPath(directory)
  } catch {
    return undefined
  }
}

const getLastAssistantText = async (client: any, sessionId: string) => {
  const response = await client.session.messages({
    path: { id: sessionId },
    query: { limit: 10 },
  })
  const messages = response.data ?? []
  const assistantMessages = messages.filter((msg: any) => msg.info?.role === "assistant")
  const lastAssistant = assistantMessages[assistantMessages.length - 1]
  if (!lastAssistant) return ""
  return (lastAssistant.parts || [])
    .filter((part: any) => part.type === "text")
    .map((part: any) => part.text ?? "")
    .join("\n")
}

const appendEvent = async (projectPath: string, sessionId: string, level: string, event: string, detail: string) => {
  const target = eventsPath(projectPath)
  await mkdir(dirname(target), { recursive: true })
  const line = `${new Date().toISOString()} | ${level.padEnd(5)} | ${event} | session=${sessionId} | ${detail}\n`
  await appendFile(target, line, "utf-8")
}

const buildFreshStartPrompt = async (projectPath: string, iteration: number, initialMessage?: string) => {
  const optionalFiles = ["memory.md", "progress.md"]
    .map((name) => join(projectPath, name))
    .filter((_) => true)
  return [
    `Fresh start for iteration ${iteration}.`,
    "Read PRD.md from scratch before doing anything else.",
    "If memory.md or progress.md exist and are useful, re-read them from scratch as well.",
    "Do not rely on prior chat context. Use the current filesystem state as the source of truth.",
    initialMessage?.trim() ? `Original instruction:\n${initialMessage}` : "",
    "If the PRD is already satisfied, output exactly <complete>DONE</complete> on its own line.",
    `Project path: ${projectPath}`,
    `Required entry file: ${join(projectPath, "PRD.md")}`,
    optionalFiles.length ? `Optional files to inspect if useful: ${optionalFiles.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n\n")
}

const sendPrompt = async (client: any, sessionId: string, prompt: string) => {
  await client.session.promptAsync({
    path: { id: sessionId },
    body: { parts: [{ type: "text", text: prompt }] },
  })
}

const formatStatus = async (directory: string, sessionId?: string) => {
  try {
    const { projectPath, prdPath } = await resolveProjectPath(directory)
    const state = await readState(projectPath)
    const lines = [
      "ChatLoop status:",
      "- Loaded: yes (this command is available)",
      `- Project root: ${projectPath}`,
      `- PRD entry: ${prdPath}`,
      `- State file: ${statePath(projectPath)}`,
      `- Events file: ${eventsPath(projectPath)}`,
      `- Completion marker: <complete>DONE</complete>`,
      `- Active: ${state.active ? "yes" : "no"}`,
    ]
    if (state.sessionId) {
      lines.push(`- Last session: ${state.sessionId}`)
    }
    if (sessionId) {
      lines.push(`- Current session: ${sessionId}`)
    }
    if (state.projectPath) {
      lines.push(`- Stored project root: ${state.projectPath}`)
    }
    if (state.active) {
      lines.push(`- Iteration: ${state.iteration}/${state.maxIterations}`)
    }
    lines.push("- Use /chatloop to start, /chatloop-stop to stop, /chatloop-help for workflow details.")
    return lines.join("\n")
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return [
      "ChatLoop status:",
      "- Loaded: yes (this command is available)",
      `- Active project: not found`,
      `- Reason: ${message}`,
      "- Run /chatloop inside a project directory that contains PRD.md or a subdirectory beneath it.",
    ].join("\n")
  }
}

const chatloop: Plugin = async (ctx) => {
  const start = tool({
    description: "Start PRD-driven chat loop in the current directory and send the user's message verbatim as the initial instruction",
    args: {
      message: tool.schema.string().optional().describe("Initial user message to forward verbatim"),
      maxIterations: tool.schema.number().optional().describe("Maximum loop iterations"),
    },
    async execute({ message = "", maxIterations = 20 }, context) {
      const { projectPath, prdPath } = await resolveProjectPath(ctx.directory)
      const state: State = {
        active: true,
        sessionId: context.sessionID,
        projectPath,
        initialMessage: message,
        iteration: 1,
        maxIterations,
      }
      await writeState(projectPath, state)
      await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.start", `project=${projectPath} cwd=${resolve(ctx.directory)} maxIterations=${maxIterations}`)
      if (message.trim()) {
        await sendPrompt(ctx.client, context.sessionID, message)
        await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.initial_message", "forwarded user message verbatim")
      } else {
        const prompt = await buildFreshStartPrompt(projectPath, 1)
        await sendPrompt(ctx.client, context.sessionID, prompt)
        await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.initial_prompt", "started with PRD fresh-start prompt")
      }
      return [
        "ChatLoop started.",
        `- Project root: ${projectPath}`,
        `- PRD entry: ${prdPath}`,
        `- State file: ${statePath(projectPath)}`,
        `- Events file: ${eventsPath(projectPath)}`,
        `- Completion marker: <complete>DONE</complete>`,
      ].join("\n")
    },
  })

  const stop = tool({
    description: "Stop chat loop",
    args: {},
    async execute(_args, context) {
      const resolved = await tryResolveProjectPath(ctx.directory)
      if (!resolved) return "No active ChatLoop project found from the current directory."
      const { projectPath } = resolved
      const state = await readState(projectPath)
      if (state.sessionId && state.sessionId !== context.sessionID) return "No active ChatLoop in this session."
      await clearState(projectPath)
      if (context.sessionID) await appendEvent(projectPath, context.sessionID, "INFO", "chatloop.stop", "stopped by user")
      return "ChatLoop stopped."
    },
  })

  const help = tool({
    description: "Explain how chatloop works",
    args: {},
    async execute() {
      return [
        "ChatLoop usage:",
        "- /chatloop <message> starts a PRD-driven loop in the current directory or the nearest parent that contains PRD.md.",
        "- The initial user message is forwarded verbatim when provided.",
        "- On each idle checkpoint, ChatLoop restarts from scratch by asking the model to re-read PRD.md and optional memory/progress files.",
        "- If the task is complete, the model must output <complete>DONE</complete>.",
        "- State is written to .opencode/chatloop.local.md under the resolved project root.",
        "- Event records are appended to chatloop.events.log in the resolved project root.",
        "- Use /chatloop-status to verify the resolved project root, state file, and events file.",
      ].join("\n")
    },
  })

  const status = tool({
    description: "Show chatloop status and debug paths",
    args: {},
    async execute(_args, context) {
      return formatStatus(ctx.directory, context.sessionID)
    },
  })

  return {
    tool: {
      chatloop: start,
      "chatloop-status": status,
      "chatloop-stop": stop,
      "chatloop-help": help,
    },
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const resolved = await tryResolveProjectPath(ctx.directory)
      if (!resolved) return
      const { projectPath } = resolved
      const state = await readState(projectPath)
      if (!state.active || !state.sessionId || state.sessionId !== event.properties.sessionID) return
      if (state.iteration >= state.maxIterations) {
        await appendEvent(projectPath, event.properties.sessionID, "WARN", "chatloop.max_iterations", `iteration=${state.iteration}`)
        await clearState(projectPath)
        return
      }

      const lastText = await getLastAssistantText(ctx.client, event.properties.sessionID)
      if (COMPLETE_RE.test(lastText)) {
        await appendEvent(projectPath, event.properties.sessionID, "INFO", "chatloop.complete", "assistant emitted completion marker")
        await clearState(projectPath)
        return
      }

      const next = { ...state, iteration: state.iteration + 1 }
      await writeState(projectPath, next)
      const prompt = await buildFreshStartPrompt(state.projectPath || projectPath, next.iteration, state.initialMessage)
      await appendEvent(projectPath, event.properties.sessionID, "INFO", "chatloop.idle", `restarting fresh iteration=${next.iteration}`)
      await sendPrompt(ctx.client, event.properties.sessionID, prompt)
    },
  }
}

export default { id: "local.chatloop", server: chatloop }
