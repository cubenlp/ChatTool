import { mkdir, readFile, readdir, stat, writeFile, unlink } from "fs/promises"
import { basename, dirname, join, relative, resolve, sep } from "path"
import { tool, type Plugin } from "@opencode-ai/plugin"

type Mode = "single-task" | "multi-task"
type Phase = "working" | "review" | "project-review"

type State = {
  active: boolean
  sessionId?: string
  projectPath?: string
  mode?: Mode
  phase?: Phase
  activeTask?: string
  initialMessage?: string
  iteration: number
  maxIterations: number
}

const STATE_FILE = "chatloop.local.md"
const DEFAULT_MAX_ITERATIONS = 25
const TASK_PROTOCOL_FILES = ["TASK.md", "review.md", "memory.md", "progress.md"] as const
const REVIEW_PASS_RE = /^REVIEW:\s*PASS\s*$/im
const REVIEW_FAIL_RE = /^REVIEW:\s*FAIL\s*$/im
const PROJECT_COMPLETE_RE = /^PROJECT STATUS:\s*COMPLETE\s*$/im
const ACTIVE_TASK_RE = /^ACTIVE TASK:\s*(.+)\s*$/im
const WRITE_BLOCK_RE = /^<<WRITE:\s*(.+?)\s*>>\n([\s\S]*?)^<<END WRITE>>\s*$/gim

const statePath = (directory: string) => join(directory, ".opencode", STATE_FILE)

const parseStoredString = (value?: string) => {
  if (!value) return undefined
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

const readState = async (directory: string): Promise<State> => {
  try {
    const text = await readFile(statePath(directory), "utf-8")
    const body = text.split(/^---$/m)[2] ?? ""
    const active = /active:\s*true/.test(text)
    const sessionId = text.match(/sessionId:\s*(.+)$/m)?.[1]?.trim()
    const projectPath = text.match(/projectPath:\s*(.+)$/m)?.[1]?.trim()
    const mode = text.match(/mode:\s*(.+)$/m)?.[1]?.trim() as Mode | undefined
    const phase = text.match(/phase:\s*(.+)$/m)?.[1]?.trim() as Phase | undefined
    const activeTask = text.match(/activeTask:\s*(.+)$/m)?.[1]?.trim()
    const initialMessage = parseStoredString(text.match(/initialMessage:\s*(.+)$/m)?.[1]?.trim())
    const iteration = Number(text.match(/iteration:\s*(\d+)/m)?.[1] ?? 0)
    const maxIterations = Number(text.match(/maxIterations:\s*(\d+)/m)?.[1] ?? DEFAULT_MAX_ITERATIONS)
    return { active, sessionId, projectPath: projectPath || body.trim() || undefined, mode, phase, activeTask, initialMessage, iteration, maxIterations }
  } catch {
    return { active: false, iteration: 0, maxIterations: DEFAULT_MAX_ITERATIONS }
  }
}

const writeState = async (directory: string, state: State) => {
  await mkdir(dirname(statePath(directory)), { recursive: true })
  await writeFile(
    statePath(directory),
    `---\nactive: ${state.active}\niteration: ${state.iteration}\nmaxIterations: ${state.maxIterations}\n${state.sessionId ? `sessionId: ${state.sessionId}\n` : ""}${state.projectPath ? `projectPath: ${state.projectPath}\n` : ""}${state.mode ? `mode: ${state.mode}\n` : ""}${state.phase ? `phase: ${state.phase}\n` : ""}${state.activeTask ? `activeTask: ${state.activeTask}\n` : ""}${state.initialMessage ? `initialMessage: ${JSON.stringify(state.initialMessage)}\n` : ""}---\n\n${state.projectPath ?? ""}`,
  )
}

const clearState = async (directory: string) => {
  await unlink(statePath(directory)).catch(() => {})
}

const isSafeRelativePath = (value: string) => {
  const trimmed = value.trim()
  if (!trimmed) return false
  if (trimmed.startsWith("/") || trimmed.startsWith("~")) return false
  if (trimmed.includes("..")) return false
  return true
}

const parseWriteBlocks = (text: string) => {
  const blocks: Array<{ path: string; content: string }> = []
  for (const match of text.matchAll(WRITE_BLOCK_RE)) {
    const path = match[1]?.trim() || ""
    const content = (match[2] || "").replace(/\s+$/, "")
    if (!isSafeRelativePath(path)) continue
    blocks.push({ path, content })
  }
  return blocks
}

const applyWriteBlocks = async (root: string, text: string) => {
  const blocks = parseWriteBlocks(text)
  for (const block of blocks) {
    const full = resolve(root, block.path)
    const rel = relative(root, full)
    if (rel.startsWith("..") || rel.startsWith(sep)) continue
    await mkdir(dirname(full), { recursive: true })
    await writeFile(full, block.content + (block.content.endsWith("\n") ? "" : "\n"), "utf-8")
  }
  return blocks.length
}

const normalizeProjectPath = (directory: string, text: string) => {
  const cleaned = text.trim().replace(/^['"]|['"]$/g, "")
  return resolve(directory, cleaned || ".")
}

const readOptional = async (path: string) => {
  try {
    return (await readFile(path, "utf-8")).trim()
  } catch {
    return ""
  }
}

const exists = async (path: string) => {
  try {
    await stat(path)
    return true
  } catch {
    return false
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

const parseReviewDecision = (text: string) => {
  if (REVIEW_PASS_RE.test(text)) return "pass"
  if (REVIEW_FAIL_RE.test(text)) return "fail"
  return undefined
}

const parseProjectDecision = (text: string, taskDirs: string[]) => {
  if (PROJECT_COMPLETE_RE.test(text)) return { kind: "complete" as const }
  const match = text.match(ACTIVE_TASK_RE)
  if (!match) return undefined
  const name = match[1].trim()
  const exact = taskDirs.find((task) => task === name)
  if (exact) return { kind: "task" as const, task: exact }
  const folded = taskDirs.find((task) => task.toLowerCase() === name.toLowerCase())
  if (folded) return { kind: "task" as const, task: folded }
  return { kind: "unknown" as const, task: name }
}

const listTaskDirs = async (projectPath: string) => {
  const tasksDir = join(projectPath, "tasks")
  try {
    const entries = await readdir(tasksDir)
    const names: string[] = []
    for (const entry of entries.sort()) {
      const full = join(tasksDir, entry)
      const info = await stat(full)
      if (info.isDirectory()) names.push(entry)
    }
    return names
  } catch {
    return []
  }
}

const pickTaskFromText = (text: string, taskDirs: string[]) => {
  if (!text) return undefined
  const lines = text.split(/\r?\n/)
  for (const line of lines) {
    const normalized = line.trim().toLowerCase()
    if (!normalized) continue
    if (!normalized.includes("active task") && !normalized.includes("current task")) continue
    const value = line.split(":").slice(1).join(":").trim()
    if (!value) continue
    const exact = taskDirs.find((task) => task === value)
    if (exact) return exact
    const byBase = taskDirs.find((task) => task.toLowerCase() === value.toLowerCase())
    if (byBase) return byBase
  }
  return undefined
}

const detectMode = async (projectPath: string): Promise<Mode> => {
  if (await exists(join(projectPath, "TASK.md"))) return "single-task"
  if (await exists(join(projectPath, "PROJECT.md"))) return "multi-task"
  throw new Error(
    `No TASK.md or PROJECT.md found in ${projectPath}. Start chatloop from a project directory.`,
  )
}

const chooseActiveTask = async (projectPath: string) => {
  const taskDirs = await listTaskDirs(projectPath)
  if (taskDirs.length === 0) throw new Error(`No task directories found under ${join(projectPath, "tasks")}.`)
  const reviewText = await readOptional(join(projectPath, "review.md"))
  const progressText = await readOptional(join(projectPath, "progress.md"))
  const hinted = pickTaskFromText(reviewText, taskDirs) || pickTaskFromText(progressText, taskDirs)
  if (hinted) return hinted
  return taskDirs[0]
}

const buildSingleTaskReviewPrompt = async (taskPath: string, iteration: number) => {
  const parts = await Promise.all(
    TASK_PROTOCOL_FILES.map(async (name) => [name, await readOptional(join(taskPath, name))] as const),
  )
  const partMap = Object.fromEntries(parts)
  const workContext = [["TASK.md", partMap["TASK.md"]], ["memory.md", partMap["memory.md"]], ["progress.md", partMap["progress.md"]]].filter(([, text]) => text)
  const content = workContext.map(([name, text]) => `## ${name}\n${text}`).join("\n\n")
  const reviewText = partMap["review.md"] || ""
  return [
    `You are at a review checkpoint for single-task work in ${basename(taskPath)}.`,
    `This is iteration ${iteration}.`,
    "Read review.md now. Use it to decide whether the task should continue or exit.",
    "If review fails, return to TASK.md, memory.md, and progress.md, then continue the same task.",
    "If review passes, write the required acceptance artifacts described in review.md, then stop.",
    "At the end of this review response, output exactly one line: REVIEW: PASS or REVIEW: FAIL.",
    "If REVIEW: PASS and review.md requires file outputs, include them using this exact format:",
    "<<WRITE: relative/path.md>>\n...file content...\n<<END WRITE>>",
    content ? `# Current Task Context\n\n${content}` : "",
    reviewText ? `# review.md\n\n${reviewText}` : "",
  ].filter(Boolean).join("\n\n")
}

const buildProjectReviewPrompt = async (projectPath: string, iteration: number, previousTask?: string) => {
  const projectParts = await Promise.all(
    ["PROJECT.md", "review.md", "progress.md"].map(async (name) => [name, await readOptional(join(projectPath, name))] as const),
  )
  const projectText = projectParts.filter(([, text]) => text).map(([name, text]) => `## ${name}\n${text}`).join("\n\n")
  const taskDirs = await listTaskDirs(projectPath)
  const taskList = taskDirs.map((task) => `- ${task}`).join("\n")
  return [
    `You are at a project review checkpoint for ${basename(projectPath)}.`,
    `This is iteration ${iteration}.`,
    previousTask ? `The previous active task was ${previousTask}.` : "",
    "Read project-level review.md now to decide the next active task or whether the entire project is complete.",
    "This is the outer loop. A task loop break returns here; only a project-level completion exits the whole /chatloop-project run.",
    "If the project should continue, output exactly one line: ACTIVE TASK: <task-name>.",
    "If the project is complete, output exactly one line: PROJECT STATUS: COMPLETE.",
    "If PROJECT STATUS: COMPLETE and review.md requires final file outputs, include them using:",
    "<<WRITE: relative/path.md>>\n...file content...\n<<END WRITE>>",
    projectText ? `# Project Context\n\n${projectText}` : "",
    taskList ? `# Available Tasks\n\n${taskList}` : "",
  ].filter(Boolean).join("\n\n")
}

const buildMultiTaskTaskReviewPrompt = async (projectPath: string, activeTask: string, iteration: number) => {
  const activeTaskPath = join(projectPath, "tasks", activeTask)
  const taskParts = await Promise.all(
    TASK_PROTOCOL_FILES.map(async (name) => [name, await readOptional(join(activeTaskPath, name))] as const),
  )
  const taskText = taskParts.filter(([, text]) => text).map(([name, text]) => `## ${activeTask}/${name}\n${text}`).join("\n\n")
  return [
    `You are at a task review checkpoint for ${activeTask} inside project ${basename(projectPath)}.`,
    `This is iteration ${iteration}.`,
    "Read this task's review.md now. If review fails, continue the same task. If review passes, complete required acceptance artifacts and stop this task loop.",
    "A successful task review only breaks the inner task loop and returns control to the outer project review.",
    "At the end of this review response, output exactly one line: REVIEW: PASS or REVIEW: FAIL.",
    "If REVIEW: PASS and review.md requires file outputs, include them using:",
    "<<WRITE: relative/path.md>>\n...file content...\n<<END WRITE>>",
    taskText,
  ].filter(Boolean).join("\n\n")
}

const buildReviewPrompt = async (projectPath: string, mode: Mode, iteration: number, activeTask?: string) => {
  if (mode === "single-task") return buildSingleTaskReviewPrompt(projectPath, iteration)
  if (activeTask) return buildMultiTaskTaskReviewPrompt(projectPath, activeTask, iteration)
  return buildProjectReviewPrompt(projectPath, iteration)
}

const sendPrompt = async (client: any, sessionId: string, prompt: string) => {
  await client.session.promptAsync({
    path: { id: sessionId },
    body: { parts: [{ type: "text", text: `Let's start\n\n${prompt}` }] },
  })
}

const chatloop: Plugin = async (ctx) => {
  const log = (message: string) => ctx.client.app.log({ body: { service: "chatloop", level: "info", message } })

  const startTask = tool({
    description: "Start single-task chat loop from the current directory and send the user's message verbatim",
    args: {
      message: tool.schema.string().optional().describe("User message to forward verbatim"),
      maxIterations: tool.schema.number().optional().describe("Maximum auto-loop iterations"),
    },
    async execute({ message = "", maxIterations = DEFAULT_MAX_ITERATIONS }, context) {
      const path = normalizeProjectPath(ctx.directory, ".")
      const mode = await detectMode(path)
      if (mode !== "single-task") return "Current directory is not a single-task project. Use /chatloop-project for PROJECT.md based projects."
      if (!message.trim()) return "ChatLoop requires a message when starting a single-task project."
      await writeState(ctx.directory, {
        active: true,
        sessionId: context.sessionID,
        projectPath: path,
        mode,
        phase: "working",
        initialMessage: message,
        iteration: 0,
        maxIterations,
      })
      await sendPrompt(ctx.client, context.sessionID, message)
      log(`started loop with ${path}`)
      return `ChatLoop started for project ${path} (${mode}).`
    },
  })

  const startProject = tool({
    description: "Start multi-task project chat loop from the current directory and use project review to choose tasks",
    args: {
      message: tool.schema.string().optional().describe("User message to forward verbatim once a task is selected"),
      maxIterations: tool.schema.number().optional().describe("Maximum auto-loop iterations"),
    },
    async execute({ message = "", maxIterations = DEFAULT_MAX_ITERATIONS }, context) {
      const path = normalizeProjectPath(ctx.directory, ".")
      const mode = await detectMode(path)
      if (mode !== "multi-task") return "Current directory is not a PROJECT.md based project. Use /chatloop for single-task projects."
      if (!message.trim()) return "ChatLoop project mode requires a message so the selected task can continue with your original instruction."
      const activeTask = await chooseActiveTask(path)
      await writeState(ctx.directory, {
        active: true,
        sessionId: context.sessionID,
        projectPath: path,
        mode,
        phase: "working",
        activeTask,
        initialMessage: message,
        iteration: 0,
        maxIterations,
      })
      await sendPrompt(ctx.client, context.sessionID, message)
      log(`started project loop with ${path}`)
      return `ChatLoop project mode started for ${path}.`
    },
  })

  const stop = tool({
    description: "Stop chat loop",
    args: {},
    async execute(_args, context) {
      const state = await readState(ctx.directory)
      if (state.sessionId && state.sessionId !== context.sessionID) return "No active ChatLoop in this session."
      await clearState(ctx.directory)
      log("stopped loop")
      return "ChatLoop stopped."
    },
  })

  const help = tool({
    description: "Explain how chatloop works",
    args: {},
    async execute() {
      return [
        "ChatLoop usage:",
        "- /chatloop <message> starts a loop in the current single-task project and forwards your message verbatim.",
        "- /chatloop-project <message> starts a project-level loop in the current PROJECT.md based project.",
        "- /chatloop-stop stops the current loop.",
        "- /chatloop only works in a directory with TASK.md.",
        "- /chatloop-project only works in a directory with PROJECT.md.",
        "- Single-task mode: your message is sent verbatim, then idle triggers review -> continue or exit.",
        "- Project mode: your message starts the first active task directly -> task review -> back to project review.",
        "- Project mode uses two break levels: task review PASS breaks the inner task loop; project review COMPLETE breaks the outer project loop.",
      ].join("\n")
    },
  })

  return {
    tool: {
      chatloop: startTask,
      "chatloop-project": startProject,
      "chatloop-stop": stop,
      "chatloop-help": help,
    },
    event: async ({ event }) => {
      if (event.type !== "session.idle") return
      const state = await readState(ctx.directory)
      if (!state.active || !state.sessionId || state.sessionId !== event.properties.sessionID) return
      if (state.iteration >= state.maxIterations) {
        await clearState(ctx.directory)
        return
      }

      const lastText = await getLastAssistantText(ctx.client, event.properties.sessionID)
      const next = { ...state, iteration: state.iteration + 1 }
      const mode = state.mode || (await detectMode(state.projectPath || ctx.directory))

      if (mode === "single-task") {
        if (state.phase === "review") {
          const decision = parseReviewDecision(lastText)
          if (decision === "pass") {
            await applyWriteBlocks(state.projectPath || ctx.directory, lastText)
            await clearState(ctx.directory)
            return
          }
          if (decision !== "fail") {
            const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration)
            await writeState(ctx.directory, { ...next, phase: "review" })
            await sendPrompt(ctx.client, event.properties.sessionID, prompt)
            return
          }
          await writeState(ctx.directory, { ...next, phase: "working" })
          if (state.initialMessage?.trim()) await sendPrompt(ctx.client, event.properties.sessionID, state.initialMessage)
          return
        }
        const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration)
        await writeState(ctx.directory, { ...next, phase: "review" })
        await sendPrompt(ctx.client, event.properties.sessionID, prompt)
        return
      }

      if (state.phase === "project-review") {
        const taskDirs = await listTaskDirs(state.projectPath || ctx.directory)
        const decision = parseProjectDecision(lastText, taskDirs)
        if (decision?.kind === "complete") {
          await applyWriteBlocks(state.projectPath || ctx.directory, lastText)
          await clearState(ctx.directory)
          return
        }
        if (!decision || decision.kind === "unknown") {
          const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration)
          await writeState(ctx.directory, { ...next, phase: "project-review", activeTask: undefined })
          await sendPrompt(ctx.client, event.properties.sessionID, prompt)
          return
        }
        const activeTask = decision.task
        await writeState(ctx.directory, { ...next, phase: "working", activeTask })
        if (state.initialMessage?.trim()) await sendPrompt(ctx.client, event.properties.sessionID, state.initialMessage)
        return
      }

      if (state.phase === "review") {
        const decision = parseReviewDecision(lastText)
        if (decision === "pass") {
          const taskRoot = join(state.projectPath || ctx.directory, "tasks", state.activeTask || "")
          await applyWriteBlocks(taskRoot, lastText)
          const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration)
          await writeState(ctx.directory, { ...next, phase: "project-review", activeTask: undefined })
          await sendPrompt(ctx.client, event.properties.sessionID, prompt)
          return
        }
        if (decision !== "fail") {
          const activeTask = state.activeTask || (await chooseActiveTask(state.projectPath || ctx.directory))
          const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration, activeTask)
          await writeState(ctx.directory, { ...next, phase: "review", activeTask })
          await sendPrompt(ctx.client, event.properties.sessionID, prompt)
          return
        }
        await writeState(ctx.directory, { ...next, phase: "working", activeTask: state.activeTask })
        if (state.initialMessage?.trim()) await sendPrompt(ctx.client, event.properties.sessionID, state.initialMessage)
        return
      }

      const activeTask = state.activeTask || (await chooseActiveTask(state.projectPath || ctx.directory))
      const prompt = await buildReviewPrompt(state.projectPath || ctx.directory, mode, next.iteration, activeTask)
      await writeState(ctx.directory, { ...next, phase: "review", activeTask })
      await sendPrompt(ctx.client, event.properties.sessionID, prompt)
    },
  }
}

export default { id: "local.chatloop", server: chatloop }
