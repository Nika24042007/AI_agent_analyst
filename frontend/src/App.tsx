import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import logo from "./assets/logo.svg";
import uploadIcon from "./assets/upload.svg";
import { BACKEND_URL } from "./config";
import "./App.css";

type AnswerState = {
  request: string;
  status: "loading" | "success" | "error";
  text: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function App() {
  const [query, setQuery] = useState("");
  const promptInputRef = useRef<HTMLTextAreaElement>(null);
  const [answer, setAnswer] = useState<AnswerState | null>(null);
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
    if (!promptInput) return;

    promptInput.style.height = "auto";
    promptInput.style.height = `${promptInput.scrollHeight}px`;
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
        const data = await response.json();

        if (active) {
          setServerStatus(
            response.ok && data.status === "ok" ? "online" : "offline",
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

    setAnswer({ request, status: "loading", text: "" });
    setQuery("");

    try {
      const response = await fetch(`${BACKEND_URL}/api/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: request }),
      });
      const data: unknown = await response.json();

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

      setAnswer({ request, status: "success", text: data.interpretation });
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

  return (
    <main className={`home${answer ? " home-with-answer" : ""}`}>
      <div className="home-prompt">
        <img className="wordmark" src={logo} alt="сурьёзно." />

        <form className="prompt" onSubmit={sendQuery}>
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
                : "Ответ сервера"}
          </h2>
          <p className="answer-request">{answer.request}</p>
          {answer.status === "loading" ? (
            <p className="answer-text">Пожалуйста, подождите...</p>
          ) : (
            <p className="answer-text">{answer.text}</p>
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
