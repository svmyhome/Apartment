export type ApiAvailability = "available" | "unavailable"

type HealthResponse = {
  status: string
}

function getHealthUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL

  if (!apiUrl) {
    throw new Error("VITE_API_URL is not configured")
  }

  return `${apiUrl.replace(/\/$/, "")}/api/v1/health`
}

export async function checkApiHealth(): Promise<ApiAvailability> {
  const response = await fetch(getHealthUrl())

  if (response.status === 503) {
    return "unavailable"
  }

  if (!response.ok) {
    throw new Error("Unexpected API response")
  }

  const payload: HealthResponse = await response.json()

  if (payload.status !== "ok") {
    throw new Error("Unexpected health-check response")
  }

  return "available"
}
