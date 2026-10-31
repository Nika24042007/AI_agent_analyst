import { useRef, useState } from 'react'
import logo from './assets/logo.svg'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [promptFocused, setPromptFocused] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function addFiles(list: FileList | null) {
    if (!list?.length) return
    const incoming = Array.from(list)
    setFiles((current) => {
      const keys = new Set(current.map((file) => `${file.name}:${file.size}:${file.lastModified}`))
      const extra = incoming.filter(
        (file) => !keys.has(`${file.name}:${file.size}:${file.lastModified}`),
      )
      return extra.length ? [...current, ...extra] : current
    })
  }

  function removeFile(index: number) {
    setFiles((current) => current.filter((_, i) => i !== index))
  }

  return (
    <main className="home">
      <img className="wordmark" src={logo} alt="сурьёзно." />

      <div className="prompt">
        <button
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
        </button>
        <div className="prompt-field">
          {!promptFocused && query ? (
            <span className="prompt-truncated" aria-hidden="true">
              {query}
            </span>
          ) : null}
          <input
            className={
              promptFocused || !query ? 'prompt-input' : 'prompt-input is-covered'
            }
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onFocus={() => setPromptFocused(true)}
            onBlur={() => setPromptFocused(false)}
            placeholder="Какой-нибудь промптик сюда напишите..."
            aria-label="Поиск"
            title={query}
          />
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          hidden
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />
      </div>

      {files.length > 0 ? (
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
      ) : null}
    </main>
  )
}

export default App
