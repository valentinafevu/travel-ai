export interface User {
  id: string
  name: string
  profile: string
  description: string
  history: string[]
  origin: string
  party_size: number
  max_price_per_person_usd: string
  vector: Record<string, number>
}

export interface Flight {
  id: string
  origin: string
  destination: string
  airline: string
  flight_number: string
  cabin: string
  departure_at: string
  arrival_at: string
  price_per_person_usd: string
  available_seats: number
  vector: Record<string, number>
}

export interface TravelPackage {
  id: string
  name: string
  destination: string
  nights: number
  description: string
  score: number
  vector: Record<string, number>
  price_per_person_usd: string
  total_price_usd: string
  max_people: number
  accommodation: {
    id: string
    hotel: string
    airport: string
    check_in: string
    check_out: string
    vector: Record<string, number>
    price_per_person_usd: string
  }
  outbound_flight: Flight
  return_flight: Flight
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/${path}`, { signal, headers: { Accept: 'application/json' } })
  if (!response.ok) throw new Error(`La API respondió con estado ${response.status}.`)
  return response.json() as Promise<T>
}

export const fetchUsers = () => get<{ users: User[] }>('users/')
export const fetchRecommendations = (id: string, signal: AbortSignal) =>
  get<{ recommendations: TravelPackage[] }>(`users/${encodeURIComponent(id)}/recommendations/`, signal)
