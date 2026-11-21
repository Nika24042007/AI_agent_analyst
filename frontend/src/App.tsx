import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import logo from "./assets/logo.svg";
import uploadIcon from "./assets/upload.svg";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const BACKEND_URL = (
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"
).replace(/\/+$/, "");

type AnswerState = {
  request: string;
  status: "loading" | "success" | "error";
  text: string;
  model?: Record<string, unknown>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text.trim()) {
    throw new Error(`Сервер вернул пустой ответ (HTTP ${response.status})`);
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`Сервер вернул не JSON (HTTP ${response.status})`);
  }
}

function App() {
  const [query, setQuery] = useState("");
  const promptInputRef = useRef<HTMLTextAreaElement>(null);
  const promptFormRef = useRef<HTMLFormElement>(null);
  const [answer, setAnswer] = useState<AnswerState | null>(null);
  const [modelCopyState, setModelCopyState] = useState<
    "idle" | "copied" | "error"
  >("idle");
  const [serverStatus, setServerStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");
  // const [files, setFiles] = useState<File[]>([]); сейчас файлы прикреплять нельзя :(
  // const fileInputRef = useRef<HTMLInputElement>(null);

  // function addFiles(list: FileList | null) {
  //   if (!list?.length) return;
  //   const incoming = Array.from(list);
  //   setFiles((current) => {
  //     const keys = new Set(
  //       current.map((file) => `${file.name}:${file.size}:${file.lastModified}`),
  //     );
  //     const extra = incoming.filter(
  //       (file) => !keys.has(`${file.name}:${file.size}:${file.lastModified}`),
  //     );
  //     return extra.length ? [...current, ...extra] : current;
  //   });
  // }

  // function removeFile(index: number) {
  //   setFiles((current) => current.filter((_, i) => i !== index));
  // }

  useLayoutEffect(() => {
    const promptInput = promptInputRef.current;
    const promptForm = promptFormRef.current;
    if (!promptInput || !promptForm) return;

    const currentHeight = promptInput.getBoundingClientRect().height;
    const currentFormHeight = promptForm.getBoundingClientRect().height;
    promptInput.style.transition = "none";
    promptForm.style.transition = "none";
    promptInput.style.height = "auto";
    const nextHeight = promptInput.scrollHeight;
    promptInput.style.height = `${currentHeight}px`;
    promptForm.style.height = `${currentFormHeight}px`;
    void promptForm.offsetHeight;
    promptInput.style.removeProperty("transition");
    promptForm.style.removeProperty("transition");
    promptInput.style.height = `${nextHeight}px`;
    promptForm.style.height = `${Math.max(
      48,
      currentFormHeight + nextHeight - currentHeight,
    )}px`;

    const bottomOverflow =
      promptInput.getBoundingClientRect().bottom +
      nextHeight -
      currentHeight -
      window.innerHeight +
      24;
    if (bottomOverflow > 0) {
      window.scrollBy({
        top: bottomOverflow,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "auto"
          : "smooth",
      });
    }
  }, [query]);

  useEffect(() => {
    let active = true;

    async function checkServer() {
      setServerStatus("checking");

      try {
        const response = await fetch(`${BACKEND_URL}/api/health`, {
          method: "GET",
          cache: "no-store",
        });
        const data = await readJsonResponse(response);

        if (active) {
          setServerStatus(
            response.ok &&
              isRecord(data) &&
              data.status === "ok"
              ? "online"
              : "offline",
          );
        }
      } catch {
        if (active) {
          setServerStatus("offline");
        }
      }
    }

    checkServer();
    const intervalId = window.setInterval(checkServer, 5000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  async function sendQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const request = query.trim();
    if (!request || answer?.status === "loading") return;

    setModelCopyState("idle");
    setAnswer({ request, status: "loading", text: "" });
    setQuery("");

    try {
      const response = await fetch(`${BACKEND_URL}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: request }),
      });
      const data = await readJsonResponse(response);

      if (!response.ok) {
        const detail =
          isRecord(data) && typeof data.detail === "string"
            ? data.detail
            : "Не удалось отправить запрос";
        throw new Error(detail);
      }

      if (!isRecord(data) || typeof data.interpretation !== "string") {
        throw new Error("Сервер вернул ответ в неизвестном формате");
      }

      setAnswer({
        request,
        status: "success",
        text: data.interpretation,
        model: isRecord(data.model) ? data.model : undefined,
      });
    } catch (error) {
      setAnswer({
        request,
        status: "error",
        text:
          error instanceof Error
            ? error.message
            : "Не удалось получить ответ от сервера",
      });
    }
  }

  async function copyModel(model: Record<string, unknown>) {
    const text = JSON.stringify(model, null, 2);

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        const copied = document.execCommand("copy");
        textarea.remove();
        if (!copied) throw new Error("Не удалось скопировать");
      }
      setModelCopyState("copied");
    } catch {
      setModelCopyState("error");
    }

    window.setTimeout(() => setModelCopyState("idle"), 2000);
  }

  return (
    <main
      className={`home${answer ? " home-with-answer" : query ? " home-with-query" : ""}`}
    >
      <div className="home-prompt">
        <img className="wordmark" src={logo} alt="сурьёзно." />

        <form ref={promptFormRef} className="prompt" onSubmit={sendQuery}>
          {/* <button
            type="button"
            className="prompt-add"
            aria-label="Добавить файлы"
            onClick={() => fileInputRef.current?.click()}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 5v14M5 12h14"
                fill="none"
                stroke="currentColor"
                strokeWidth="3.2"
                strokeLinecap="square"
              />
            </svg>
          </button> */}
          <div className="prompt-field">
            <textarea
              ref={promptInputRef}
              className="prompt-input"
              rows={1}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              disabled={answer?.status === "loading"}
              placeholder="Какой-нибудь промптик сюда напишите..."
              aria-label="Запрос"
              title={query}
            />
            {query ? (
              <button
                className="prompt-send"
                type="submit"
                disabled={answer?.status === "loading"}
                aria-label="Отправить запрос"
              >
                <img src={uploadIcon} alt="" />
              </button>
            ) : null}
          </div>

          {/* <input
            ref={fileInputRef}
            type="file"
            multiple
            hidden
            onChange={(event) => {
              addFiles(event.target.files);
              event.target.value = "";
            }}
          /> */}
        </form>
      </div>

      {answer ? (
        <section
          className={`answer answer-${answer.status}`}
          aria-labelledby="answer-title"
          aria-live="polite"
        >
          <h2 id="answer-title">
            {answer.status === "loading"
              ? "Обрабатываем запрос"
              : answer.status === "error"
                ? "Не удалось получить ответ"
                : "Ответ"}
          </h2>
          <p className="answer-request">{answer.request}</p>
          {answer.status === "loading" ? (
            <p className="answer-text">Пожалуйста, подождите...</p>
          ) : answer.status === "error" ? (
            <p className="answer-text">{answer.text}</p>
          ) : (
            <>
              <div className="answer-text answer-markdown">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ children, ...props }) => (
                      <a {...props} target="_blank" rel="noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {answer.text}
                </ReactMarkdown>
              </div>
              {answer.model ? (
                <div className="answer-model">
                  <div className="answer-model-header">
                    <h3>Модель</h3>
                    <button
                      type="button"
                      className="answer-model-copy"
                      onClick={() => copyModel(answer.model!)}
                      aria-label="Скопировать модель"
                    >
                      {modelCopyState === "copied"
                        ? "Скопировано"
                        : modelCopyState === "error"
                          ? "Ошибка"
                          : "Скопировать"}
                    </button>
                  </div>
                  <pre>{JSON.stringify(answer.model, null, 2)}</pre>
                </div>
              ) : null}
            </>
          )}
        </section>
      ) : null}
      <div
        className={`server-status server-status-${serverStatus}`}
        role="status"
        aria-live="polite"
      >
        <span className="server-status-dot" aria-hidden="true" />
        Сервер:
        {serverStatus === "checking"
          ? " проверка..."
          : serverStatus === "online"
            ? " доступен"
            : " недоступен"}
      </div>

      {/* {files.length > 0 ? (
        <ul className="attachments" aria-label="Прикреплённые файлы">
          {files.map((file, index) => (
            <li key={`${file.name}-${file.size}-${file.lastModified}`}>
              <span title={file.name}>{file.name}</span>
              <button
                type="button"
                aria-label={`Убрать ${file.name}`}
                onClick={() => removeFile(index)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : null} */}
    </main>
  );
}

export default App;
