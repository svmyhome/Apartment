import { useCallback, useEffect, useState } from "react"

import { checkApiHealth, type ApiAvailability } from "./api/health"
import "./App.css"

type HealthState = "loading" | ApiAvailability

function App() {
  const [healthState, setHealthState] = useState<HealthState>("loading")

  const refreshHealth = useCallback(async () => {
    setHealthState("loading")

    try {
      setHealthState(await checkApiHealth())
    } catch {
      setHealthState("unavailable")
    }
  }, [])

  useEffect(() => {
    let isActive = true

    void checkApiHealth().then(
      (availability) => {
        if (isActive) {
          setHealthState(availability)
        }
      },
      () => {
        if (isActive) {
          setHealthState("unavailable")
        }
      },
    )

    return () => {
      isActive = false
    }
  }, [])

  const statusText =
    healthState === "loading"
      ? "Проверяем API…"
      : healthState === "available"
        ? "API доступен"
        : "API недоступен"

  return (
    <main className="page">
      <section className="health-card" aria-live="polite">
        <p className="eyebrow">Web MVP</p>
        <h1>Renovation Planner</h1>
        <p className={`status status--${healthState}`}>{statusText}</p>
        <button
          type="button"
          onClick={() => void refreshHealth()}
          disabled={healthState === "loading"}
        >
          Повторить проверку
        </button>
      </section>
    </main>
  )
}

export default App
